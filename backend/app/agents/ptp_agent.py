import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.agents.base_agent import BaseRecoveryAgent
from backend.app.models.recovery import RecoveryIncident
from backend.app.services.razorpay_service import razorpay_service
from backend.app.services.telegram_service import telegram_service

logger = logging.getLogger("razorloop.ptp_agent")

class PTPAgent(BaseRecoveryAgent):
    def __init__(self):
        super().__init__(agent_name="PTP_Installment_Negotiator")

    async def diagnose(self, incident: RecoveryIncident) -> Dict[str, Any]:
        return {
            "root_cause": "Temporary cash-flow / liquidity constraint.",
            "negotiation_posture": "Split into 2x 50% tranches with 15-day grace period.",
            "recommended_action": "Issue partial payment link for Tranche 1; pause reminders."
        }

    async def intervene(self, incident: RecoveryIncident, db: AsyncSession) -> Dict[str, Any]:
        half_amount = round(incident.original_amount / 2, 2)

        # 1. Create Razorpay Payment Link for Tranche 1
        plink = razorpay_service.create_payment_link(
            amount_inr=half_amount,
            description=f"Tranche 1 (50%) for {incident.customer_name}",
            customer_name=incident.customer_name,
            customer_phone=incident.customer_phone,
            incident_id=incident.id
        )

        plan = {
            "tranche_1_amount": half_amount,
            "tranche_2_amount": half_amount,
            "tranche_1_link": plink.get("short_url"),
            "status": "ptp_active",
            "grace_period_days": 15
        }
        incident.extra_data = json.dumps(plan)
        incident.status = "intervened"
        incident.payment_link_url = plink.get("short_url")
        incident.intervention_action = f"Structured 2-tranche PTP plan (₹{half_amount:,.0f} today). Paused all reminders."

        # 2. Audit Diagnosis & Intervention
        await self.log_audit(
            db=db,
            incident_id=incident.id,
            event_type="PTP_RESTRUCTURE",
            details=f"Customer selected PTP. Split ₹{incident.original_amount} into 2x ₹{half_amount}. Generated {plink.get('short_url')}",
            compliance_rule="RBI Fair Lending & Non-Coercive Debt Resolution Framework"
        )

        # 3. Update or Send Telegram confirmation
        msg_text = (
            f"🤝 <b>Promise-to-Pay (PTP) Restructuring Confirmed!</b>\n\n"
            f"Hey <b>{incident.customer_name}</b>, we've split your payment of ₹{incident.original_amount:,.0f} into 2 installments:\n\n"
            f"• <b>Tranche 1 (Due Today):</b> ₹{half_amount:,.0f}\n"
            f"• <b>Tranche 2 (Due in 15 days):</b> ₹{half_amount:,.0f}\n\n"
            f"⏳ <b>Status:</b> All automated dunning paused until the promised date."
        )

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": f"💳 Pay Tranche 1 (₹{half_amount:,.0f})", "url": plink.get("short_url")}
                ],
                [
                    {"text": "❌ Cancel Order", "callback_data": f"cancel:{incident.id}"}
                ]
            ]
        }

        # If previous message exists, edit it or send new one
        if incident.telegram_message_id:
            edited = await telegram_service.edit_message(
                chat_id=incident.telegram_chat_id,
                message_id=incident.telegram_message_id,
                text=msg_text,
                reply_markup=keyboard
            )
            if not edited:
                msg_id = await telegram_service.send_message(
                    chat_id=incident.telegram_chat_id,
                    text=msg_text,
                    reply_markup=keyboard
                )
                incident.telegram_message_id = msg_id
        else:
            msg_id = await telegram_service.send_message(
                chat_id=incident.telegram_chat_id,
                text=msg_text,
                reply_markup=keyboard
            )
            incident.telegram_message_id = msg_id

        await db.commit()
        return {
            "status": "success",
            "tranche_1_amount": half_amount,
            "payment_url": plink.get("short_url")
        }

    def evaluate_stopping_rule(self, incident: RecoveryIncident, event_type: str, event_data: Dict[str, Any]) -> Optional[str]:
        if event_type == "payment.captured":
            return "PTP_TRANCHE_PAID: Tranche 1 captured. Pause dunning until Tranche 2 milestone date."
        elif event_type == "customer.cancel":
            return "USER_STOP: Customer opted out of PTP plan."
        return None

ptp_agent = PTPAgent()
