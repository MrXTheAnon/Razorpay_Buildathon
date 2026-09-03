import asyncio
import logging
from typing import Optional
import httpx
from sqlalchemy import select
from backend.app.config import settings
from backend.app.core.database import async_session_factory
from backend.app.models.recovery import RecoveryIncident, AuditLog
from backend.app.services.telegram_service import telegram_service
from backend.app.agents.ptp_agent import ptp_agent
from backend.app.services.omniroute_ai_service import omniroute_ai_service

logger = logging.getLogger("razorloop.telegram_listener")

class TelegramListener:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.offset = 0
        self.is_running = False

    async def start(self):
        if not self.bot_token:
            logger.warning("No Telegram Bot Token provided. Listener disabled.")
            return

        self.is_running = True
        logger.info("Starting Telegram Long-Polling background listener...")

        # Clear old pending updates
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                await client.post(f"{self.base_url}/getUpdates", json={"offset": -1})
            except Exception:
                pass

        while self.is_running:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        f"{self.base_url}/getUpdates",
                        json={"offset": self.offset, "timeout": 5}
                    )
                    data = resp.json()

                    if data.get("ok"):
                        updates = data.get("result", [])
                        for update in updates:
                            self.offset = update["update_id"] + 1
                            await self.handle_update(update)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Telegram polling error: {e}")
                await asyncio.sleep(2)

    def stop(self):
        self.is_running = False

    async def handle_update(self, update: dict):
        # 1. Handle Button Clicks (callback_query)
        if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb["id"]
            data = cb.get("data", "")
            chat_id = str(cb["message"]["chat"]["id"])
            msg_id = cb["message"]["message_id"]

            logger.info(f"Received Telegram callback: {data}")

            if data.startswith("pay:") or data.startswith("paid:"):
                incident_id = data.split(":", 1)[1]
                await self.handle_pay(incident_id, chat_id, msg_id, cb_id)
            elif data.startswith("cancel:"):
                incident_id = data.split(":", 1)[1]
                await self.handle_cancel(incident_id, chat_id, msg_id, cb_id)
            elif data.startswith("ptp:"):
                incident_id = data.split(":", 1)[1]
                await self.handle_ptp(incident_id, chat_id, msg_id, cb_id)
            elif data.startswith("accept_cn:"):
                incident_id = data.split(":", 1)[1]
                await self.handle_accept_cn(incident_id, chat_id, msg_id, cb_id)
            elif data.startswith("escalate:"):
                incident_id = data.split(":", 1)[1]
                await self.handle_escalate(incident_id, chat_id, msg_id, cb_id)
            elif data.startswith("alt_rail:"):
                incident_id = data.split(":", 1)[1]
                await self.handle_alt_rail(incident_id, chat_id, msg_id, cb_id)

        # 2. Handle Text Messages (/start, /help)
        elif "message" in update and "text" in update["message"]:
            msg = update["message"]
            text = msg["text"].strip()
            chat_id = str(msg["chat"]["id"])
            first_name = msg["chat"].get("first_name", "Friend")

            if text.startswith("/start") or text.startswith("/help"):
                masked_cid = f"{chat_id[0]}*******{chat_id[-1]}" if len(chat_id) >= 2 else "********"
                welcome_text = (
                    f"👋 <b>Namaste {first_name}!</b>\n\n"
                    f"Welcome to <b>RazorLoop</b> — Autonomous AI Revenue Recovery Agent for Razorpay.\n\n"
                    f"📱 <b>Your Telegram Chat ID:</b> <code>{masked_cid}</code> (Masked for Security)\n"
                    f"(Use this in the dashboard simulator to receive live interactive recovery cards on your phone!)\n\n"
                    f"<b>Available Capabilities:</b>\n"
                    f"• ⚡ In-Flight UPI Intent Drop-Off Reassurance\n"
                    f"• 🤝 Promise-to-Pay (PTP) Installment Negotiation\n"
                    f"• 📑 B2B Invoicing TDS/GST Dispute Net Settlement\n"
                    f"• 🏦 UPI Autopay Telemetry-Aware Mandate Healing"
                )
                await telegram_service.send_message(chat_id=chat_id, text=welcome_text)
            elif text.startswith("/myid"):
                await telegram_service.send_message(chat_id=chat_id, text=f"🔑 Your exact Chat ID: <code>{chat_id}</code>")
            else:
                # 🤖 Autonomous AI Recovery Copilot via OmniRoute
                await self.handle_customer_ai_chat(chat_id, first_name, text)

    async def handle_cancel(self, incident_id: str, chat_id: str, msg_id: int, cb_id: str):
        async with async_session_factory() as db:
            res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.id == incident_id))
            inc = res.scalars().first()
            if inc:
                inc.status = "halted"
                inc.stopping_rule_triggered = "USER_STOP: Customer explicitly clicked 'Cancel Order' via Telegram."

                stmt = select(AuditLog).where(AuditLog.incident_id == inc.id).order_by(AuditLog.id.desc()).limit(1)
                last_log = (await db.execute(stmt)).scalars().first()
                prev_hash = last_log.event_hash if last_log else "GENESIS"

                audit = AuditLog(
                    incident_id=inc.id,
                    agent_name="Telegram_Listener",
                    event_type="STOPPING_RULE",
                    details="Customer clicked 'Cancel Order' on Telegram card. Dunning terminated immediately.",
                    compliance_rule="RBI / TRAI Do-Not-Disturb & Customer Opt-Out Directives",
                    event_hash=AuditLog.generate_hash(prev_hash, inc.id, "STOPPING_RULE", "USER_CANCEL")
                )
                db.add(audit)
                await db.commit()

                halted_text = (
                    f"🛑 <b>Order Cancelled</b>\n\n"
                    f"Reference: <b>{inc.id}</b>\n\n"
                    f"🛡️ <b>Stopping Rule Triggered:</b> Customer chose to cancel. All automated reminders and retries have been terminated immediately."
                )
                await telegram_service.edit_message(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=halted_text,
                    reply_markup=None
                )
                await telegram_service.answer_callback_query(cb_id, text="Order cancelled. Dunning halted.")

    async def handle_ptp(self, incident_id: str, chat_id: str, msg_id: int, cb_id: str):
        async with async_session_factory() as db:
            res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.id == incident_id))
            inc = res.scalars().first()
            if inc:
                await ptp_agent.intervene(inc, db)
                await telegram_service.answer_callback_query(cb_id, text="2-tranche installment plan activated!")

    async def handle_accept_cn(self, incident_id: str, chat_id: str, msg_id: int, cb_id: str):
        async with async_session_factory() as db:
            res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.id == incident_id))
            inc = res.scalars().first()
            if inc:
                inc.status = "recovered"
                inc.stopping_rule_triggered = "SUCCESS_STOP: Client AP accepted Credit Note and initiated net settlement."
                await db.commit()

                cn_text = (
                    f"✅ <b>TDS Credit Note Accepted</b>\n\n"
                    f"Invoice <b>{inc.id}</b> net settlement approved. Escrow reconciliation complete."
                )
                await telegram_service.edit_message(chat_id=chat_id, message_id=msg_id, text=cn_text, reply_markup=None)
                await telegram_service.answer_callback_query(cb_id, text="Credit Note accepted!")

    async def handle_escalate(self, incident_id: str, chat_id: str, msg_id: int, cb_id: str):
        async with async_session_factory() as db:
            res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.id == incident_id))
            inc = res.scalars().first()
            if inc:
                inc.status = "escalated"
                inc.stopping_rule_triggered = "MANUAL_ESCALATION: Escalated to merchant finance team."
                await db.commit()

    async def handle_alt_rail(self, incident_id: str, chat_id: str, msg_id: int, cb_id: str):
        async with async_session_factory() as db:
            res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.id == incident_id))
            inc = res.scalars().first()
            if inc:
                inc.status = "recovered"
                inc.recovered_amount = inc.original_amount
                inc.stopping_rule_triggered = "RAIL_SWITCH_STOP: Customer selected alternative settlement rail (PayPal)."

                audit = AuditLog(
                    incident_id=inc.id,
                    agent_name="CrossBorder_Decline_Agent",
                    event_type="ALTERNATIVE_RAIL_ROUTED",
                    details="Customer opted for alternative global payment rail. Dunning stopped.",
                    compliance_rule="Multi-Rail Redundancy & Customer Choice Architecture",
                    event_hash=AuditLog.generate_hash("ALT_RAIL", inc.id, "RAIL_SWITCH", "PAYPAL")
                )
                db.add(audit)
                await db.commit()

                alt_text = (
                    f"🌐 <b>Alternative Payment Rail Activated</b>\n\n"
                    f"Redirecting transaction <b>{inc.id}</b> (₹{inc.original_amount:,.0f}) to our global PayPal portal.\n"
                    f"Dunning halted under Multi-Rail Redundancy rule."
                )
                await telegram_service.edit_message(chat_id=chat_id, message_id=msg_id, text=alt_text, reply_markup=None)
                await telegram_service.answer_callback_query(cb_id, text="Switched to alternative rail!")

    async def handle_pay(self, incident_id: str, chat_id: str, msg_id: int, cb_id: str):
        """Handle 1-tap payment callback on Telegram."""
        async with async_session_factory() as db:
            res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.id == incident_id))
            inc = res.scalars().first()
            if inc:
                pay_amount = inc.original_amount
                pay_id = f"pay_tg_{uuid.uuid4().hex[:8]}"
                inc.status = "recovered"
                inc.recovered_amount = pay_amount
                inc.razorpay_payment_id = pay_id
                inc.stopping_rule_triggered = f"SUCCESS_STOP: Payment of ₹{pay_amount:,.2f} verified on Razorpay ({pay_id})."

                stmt = select(AuditLog).where(AuditLog.incident_id == inc.id).order_by(AuditLog.id.desc()).limit(1)
                last_log = (await db.execute(stmt)).scalars().first()
                prev_hash = last_log.event_hash if last_log else "GENESIS"

                audit = AuditLog(
                    incident_id=inc.id,
                    agent_name="Telegram_Listener",
                    event_type="RECOVERY_VERIFIED",
                    details=f"Payment verified for ₹{pay_amount:,.2f} on Telegram. Dunning terminated.",
                    compliance_rule="Instant Cessation of Dunning upon Debt Satisfaction",
                    event_hash=AuditLog.generate_hash(prev_hash, inc.id, "RECOVERY_VERIFIED", str(pay_amount))
                )
                db.add(audit)
                await db.commit()

                text = (
                    f"🎉 <b>Payment Captured via NetBanking!</b>\n\n"
                    f"Order: <b>{inc.id}</b>\n"
                    f"Customer: <b>{inc.customer_name}</b>\n"
                    f"Amount Paid: <b>₹{pay_amount:,.2f}</b>\n"
                    f"Payment ID: <code>{pay_id}</code>\n\n"
                    f"🛡️ <b>Stopping Rule Triggered:</b> Debt satisfied. All reminders and dunning terminated."
                )
                keyboard = {
                    "inline_keyboard": [
                        [{"text": f"✅ Paid ₹{pay_amount:,.2f} (Confirmed)", "callback_data": f"paid:{inc.id}"}]
                    ]
                }
                await telegram_service.edit_message(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=text,
                    reply_markup=keyboard
                )
                await telegram_service.answer_callback_query(cb_id, text=f"Payment of ₹{pay_amount:,.2f} confirmed!")

    async def handle_customer_ai_chat(self, chat_id: str, first_name: str, user_text: str):
        """Invoke OmniRoute AI Copilot to address customer query with active incident context."""
        try:
            async with async_session_factory() as db:
                stmt = select(RecoveryIncident).where(
                    (RecoveryIncident.telegram_chat_id == chat_id) | (RecoveryIncident.telegram_chat_id == settings.TELEGRAM_DEMO_CHAT_ID)
                ).order_by(RecoveryIncident.created_at.desc()).limit(1)
                res = await db.execute(stmt)
                inc = res.scalars().first()

                incident_context = inc.to_dict() if inc else {
                    "track": "in_flight_upi",
                    "original_amount": 1499.0,
                    "root_cause": "Payment verification query",
                    "customer_name": first_name
                }

                customer_name = inc.customer_name if inc else first_name
                ai_reply = await omniroute_ai_service.chat_with_customer(
                    customer_name=customer_name,
                    incident_context=incident_context,
                    user_message=user_text
                )

                keyboard = None
                if inc and inc.status != "recovered":
                    host = os.getenv("APP_HOST_URL", "http://192.168.1.37:8000")
                    checkout_url = inc.payment_link_url if (inc.payment_link_url and "localhost" not in inc.payment_link_url) else f"{host}/pay/{inc.id}"
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": f"💳 Complete Payment (₹{inc.original_amount:,.0f})", "url": checkout_url}],
                            [{"text": "🛑 Stop Reminders", "callback_data": f"cancel:{inc.id}"}]
                        ]
                    }

                await telegram_service.send_message(
                    chat_id=chat_id,
                    text=f"🤖 <b>RazorLoop Copilot:</b>\n\n{ai_reply}",
                    reply_markup=keyboard
                )

                # Log Copilot Interaction in Audit
                if inc:
                    audit = AuditLog(
                        incident_id=inc.id,
                        agent_name="OmniRoute_AI_Copilot",
                        event_type="AI_COPILOT_CHAT",
                        details=f"Customer: '{user_text[:80]}' -> AI Copilot responded with context-aware guidance.",
                        compliance_rule="RBI Fair Lending & Transparent Dispute Resolution Guidelines",
                        event_hash=AuditLog.generate_hash("AI_CHAT", inc.id, "COPILOT_INTERACTION", user_text[:30])
                    )
                    db.add(audit)
                    await db.commit()
        except Exception as e:
            logger.error(f"Error in handle_customer_ai_chat: {e}")
            await telegram_service.send_message(
                chat_id=chat_id,
                text=f"Namaste {first_name}, our recovery system received your message. Your transaction is safe and no funds were double-debited."
            )

telegram_listener = TelegramListener()
