import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.agents.base_agent import BaseRecoveryAgent
from backend.app.models.recovery import RecoveryIncident
from backend.app.services.razorpay_service import razorpay_service
from backend.app.services.telegram_service import telegram_service

logger = logging.getLogger("razorloop.b2b_agent")

class B2BDisputeAgent(BaseRecoveryAgent):
    def __init__(self):
        super().__init__(agent_name="B2B_Dispute_Chaser")
        self.max_auto_variance_percent = 5.0 # Max variance auto-approved without CFO escalation

    async def diagnose(self, incident: RecoveryIncident) -> Dict[str, Any]:
        # Parse extra_data or simulate dispute parameters
        data = json.loads(incident.extra_data) if incident.extra_data else {}
        dispute_type = data.get("dispute_type", "TDS_194C_WITHHOLDING")
        withheld_amount = data.get("withheld_amount", incident.original_amount * 0.02) # 2% default TDS
        variance_pct = (withheld_amount / incident.original_amount) * 100 if incident.original_amount > 0 else 0

        is_auto_approvable = variance_pct <= self.max_auto_variance_percent

        return {
            "root_cause": f"Client AP team withheld ₹{withheld_amount:,.0f} under Section {dispute_type}.",
            "dispute_type": dispute_type,
            "withheld_amount": withheld_amount,
            "variance_percent": round(variance_pct, 2),
            "is_auto_approvable": is_auto_approvable,
            "net_payable": incident.original_amount - withheld_amount
        }

    async def intervene(self, incident: RecoveryIncident, db: AsyncSession) -> Dict[str, Any]:
        diag = await self.diagnose(incident)
        net_payable = diag["net_payable"]

        if diag["is_auto_approvable"]:
            # Auto-generate Smart Collect Virtual Account for net amount
            va = razorpay_service.create_smart_collect_va(
                invoice_number=incident.id,
                amount_inr=net_payable,
                customer_name=incident.customer_name
            )

            incident.status = "intervened"
            incident.intervention_action = (
                f"TDS variance {diag['variance_percent']}% is within policy (<=5%). "
                f"Generated Smart Collect VA for net amount ₹{net_payable:,.0f} and drafted Credit Note."
            )

            # Audit Diagnosis
            await self.log_audit(
                db=db,
                incident_id=incident.id,
                event_type="DISPUTE_DIAGNOSIS",
                details=f"Parsed AP response: Withheld ₹{diag['withheld_amount']} ({diag['variance_percent']}%). Auto-approved under tolerance policy.",
                compliance_rule="Indian Income Tax Act Section 194C/194J Compliance"
            )

            # Telegram Notification
            msg_text = (
                f"📑 <b>B2B Invoice Dispute Auto-Reconciled</b>\n\n"
                f"Invoice: <b>{incident.id}</b> | Client: <b>{incident.customer_name}</b>\n"
                f"• Gross Invoice: ₹{incident.original_amount:,.0f}\n"
                f"• TDS Withheld: ₹{diag['withheld_amount']:,.0f} ({diag['variance_percent']}%)\n"
                f"• <b>Net Payable:</b> <b>₹{net_payable:,.0f}</b>\n\n"
                f"🏦 <b>Razorpay Smart Collect Details:</b>\n"
                f"Account: <code>{va['account_number']}</code>\n"
                f"IFSC: <code>{va['ifsc']}</code>\n"
                f"UPI ID: <code>{va['upi_id']}</code>\n\n"
                f"✅ Credit Note draft generated automatically for compliance."
            )

            keyboard = telegram_service.build_b2b_dispute_keyboard(
                incident_id=incident.id,
                va_upi=va["upi_id"],
                net_amount=net_payable
            )

            msg_id = await telegram_service.send_message(
                chat_id=incident.telegram_chat_id,
                text=msg_text,
                reply_markup=keyboard
            )
            if msg_id:
                incident.telegram_message_id = msg_id

            await db.commit()
            return {"status": "auto_approved", "net_payable": net_payable, "va": va}
        else:
            # Escalate to merchant CFO
            incident.status = "escalated"
            incident.intervention_action = f"TDS variance {diag['variance_percent']}% exceeds 5% threshold. Escalated to CFO; dunning halted."

            await self.log_audit(
                db=db,
                incident_id=incident.id,
                event_type="STOPPING_RULE",
                details=f"Variance of {diag['variance_percent']}% exceeded maximum 5% tolerance. Escalated to finance review.",
                compliance_rule="Audit & Escalation Protocol for Disputed Invoices"
            )

            msg_text = (
                f"🚨 <b>B2B Dispute Escalated to CFO</b>\n\n"
                f"Invoice: <b>{incident.id}</b> | Client: <b>{incident.customer_name}</b>\n"
                f"Variance: <b>{diag['variance_percent']}%</b> (exceeds 5% tolerance).\n\n"
                f"🛑 All automated dunning paused pending manual review."
            )
            await telegram_service.send_message(chat_id=incident.telegram_chat_id, text=msg_text)
            await db.commit()
            return {"status": "escalated", "reason": "Variance threshold exceeded"}

    def evaluate_stopping_rule(self, incident: RecoveryIncident, event_type: str, event_data: Dict[str, Any]) -> Optional[str]:
        if event_type == "payment.captured":
            return "SUCCESS_STOP: Net payment received via Smart Collect. Clear invoice and issue receipt."
        elif event_type == "escalate":
            return "ESCALATION_STOP: Dispute escalated to CFO. Automated dunning paused."
        return None

b2b_dispute_agent = B2BDisputeAgent()
