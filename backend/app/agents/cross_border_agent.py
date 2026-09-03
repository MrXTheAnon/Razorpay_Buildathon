import os
import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.agents.base_agent import BaseRecoveryAgent
from backend.app.models.recovery import RecoveryIncident
from backend.app.services.razorpay_service import razorpay_service
from backend.app.services.telegram_service import telegram_service

logger = logging.getLogger("razorloop.agents.cross_border")

ISSUER_GUIDES = {
    "HDFC": {
        "app": "MyCards App / NetBanking",
        "steps": "Cards > Manage Card > Enable International E-Commerce",
        "portal_url": "https://mycards.hdfcbank.com"
    },
    "ICICI": {
        "app": "iMobile Pay",
        "steps": "Cards & Forex > Manage Limits > Domestic & International Usage",
        "portal_url": "https://www.icicibank.com"
    },
    "SBI": {
        "app": "SBI YONO / Card App",
        "steps": "Services > Manage Card Usage > International Transactions ON",
        "portal_url": "https://www.sbicard.com"
    },
    "AXIS": {
        "app": "Axis Mobile App",
        "steps": "Credit Cards > Control Center > International Usage Toggle",
        "portal_url": "https://www.axisbank.com"
    }
}

class CrossBorderDeclineAgent(BaseRecoveryAgent):
    def __init__(self):
        super().__init__("CrossBorder_Decline_Agent")

    async def diagnose(self, incident: RecoveryIncident) -> Dict[str, Any]:
        """Diagnose opaque ISO-8583 error code and determine issuer unlock steps."""
        extra = json.loads(incident.extra_data) if incident.extra_data else {}
        issuer = extra.get("issuer_bank", "HDFC")
        card_network = extra.get("card_network", "Visa")
        error_code = extra.get("error_code", "ISO_8583_57")

        guide = ISSUER_GUIDES.get(issuer, ISSUER_GUIDES["HDFC"])
        root_cause = (
            f"Declined under RBI LRS mandate: {card_network} international e-commerce disabled by default on {issuer}."
        )

        return {
            "root_cause": root_cause,
            "error_code": error_code,
            "issuer_bank": issuer,
            "card_network": card_network,
            "app_guide": guide
        }

    async def intervene(self, incident: RecoveryIncident, db: AsyncSession) -> Dict[str, Any]:
        """Send targeted unlock guidance + multi-rail fallback link."""
        diag = await self.diagnose(incident)
        incident.root_cause = diag["root_cause"]
        guide = diag["app_guide"]
        issuer = diag["issuer_bank"]

        # Create Razorpay multi-currency / card retry link
        plink = razorpay_service.create_payment_link(
            amount_inr=incident.original_amount,
            customer_name=incident.customer_name,
            customer_phone=incident.customer_phone,
            description=f"International checkout for {incident.customer_name} ({issuer} Retry)",
            incident_id=incident.id
        )

        incident.payment_link_id = plink.get("id")
        incident.payment_link_url = plink.get("short_url")
        incident.intervention_action = f"Provided {issuer} 1-tap card toggle guide ({guide['app']}) + Multi-rail checkout link."
        incident.status = "intervened"

        # Log audit entry
        await self.log_audit(
            db=db,
            incident_id=incident.id,
            event_type="CROSS_BORDER_TRANSLATION",
            details=f"Opaque decline translated: {diag['error_code']} -> {issuer} international lock. 3DS2 guidance sent.",
            compliance_rule="RBI Mandatory International Usage Regulation (Security Directive 2020/21)"
        )

        # Dispatch Telegram card if chat ID configured
        if incident.telegram_chat_id:
            text = (
                f"🌐 <b>International Card Declined: Action Required</b>\n\n"
                f"Hello {incident.customer_name}, your transaction of <b>₹{incident.original_amount:,.0f}</b> on your {issuer} card was declined.\n\n"
                f"<b>Why this happened:</b> Under RBI security directives, international online transactions are <i>disabled by default</i> on new cards.\n\n"
                f"📲 <b>How to enable in 30 seconds:</b>\n"
                f"1. Open <b>{guide['app']}</b>\n"
                f"2. Go to: <code>{guide['steps']}</code>\n"
                f"3. Toggle <b>International Online Transactions ON</b>\n\n"
                f"Once toggled, complete your checkout below, or choose an alternative rail:"
            )

            host = os.getenv("APP_HOST_URL", "http://192.168.1.37:8000")
            checkout_url = incident.payment_link_url if (incident.payment_link_url and "localhost" not in incident.payment_link_url) else f"{host}/pay/{incident.id}"
            keyboard = {
                "inline_keyboard": [
                    [{"text": "💳 Complete Card Checkout", "url": checkout_url}],
                    [{"text": "🌐 Switch to Alternative Rail (PayPal)", "callback_data": f"alt_rail:{incident.id}"}],
                    [{"text": "❌ Cancel Transaction", "callback_data": f"cancel:{incident.id}"}]
                ]
            }

            msg_id = await telegram_service.send_message(
                chat_id=incident.telegram_chat_id,
                text=text,
                reply_markup=keyboard
            )
            if msg_id:
                incident.telegram_message_id = msg_id

        await db.commit()
        return {"status": "intervened", "incident_id": incident.id}

    def evaluate_stopping_rule(self, incident: RecoveryIncident, event_type: str, event_data: Dict[str, Any]) -> Optional[str]:
        """Stop dunning on 3DS2 success, alternative rail choice, or cancel."""
        if event_type == "payment.captured":
            return "SUCCESS_STOP: Card re-authenticated via 3DS2 or alternative rail."
        elif event_type == "customer.cancel":
            return "USER_STOP: Customer cancelled international transaction."
        elif event_type == "alternative_rail_selected":
            return "RAIL_SWITCH_STOP: Customer switched to alternative settlement rail."
        return None

cross_border_agent = CrossBorderDeclineAgent()
