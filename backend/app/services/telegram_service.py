import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
import httpx
from backend.app.config import settings

logger = logging.getLogger("razorloop.telegram")

class TelegramService:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = settings.TELEGRAM_DEMO_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self._is_polling = False
        self._offset = 0

    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "HTML"
    ) -> Optional[int]:
        """Send a message to a Telegram chat, returns message_id if successful."""
        target_chat = chat_id or self.default_chat_id
        if not self.bot_token or not target_chat:
            logger.warning("Telegram Bot Token or Chat ID not configured.")
            return None

        payload: Dict[str, Any] = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/sendMessage", json=payload)
                data = resp.json()
                if data.get("ok"):
                    msg_id = data["result"]["message_id"]
                    logger.info(f"Telegram message sent successfully! message_id={msg_id}")
                    return msg_id
                else:
                    logger.error(f"Telegram API error: {data}")
                    return None
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
                return None

    async def edit_message(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """Edit an existing Telegram message."""
        target_chat = chat_id or self.default_chat_id
        if not self.bot_token or not target_chat or not message_id:
            return False

        payload: Dict[str, Any] = {
            "chat_id": target_chat,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/editMessageText", json=payload)
                data = resp.json()
                return bool(data.get("ok"))
            except Exception as e:
                logger.error(f"Failed to edit Telegram message: {e}")
                return False

    async def edit_reply_markup(
        self,
        chat_id: str,
        message_id: int,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Edit the inline keyboard of an existing Telegram message without altering text."""
        target_chat = chat_id or self.default_chat_id
        if not self.bot_token or not target_chat or not message_id:
            return False

        payload: Dict[str, Any] = {
            "chat_id": target_chat,
            "message_id": message_id
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/editMessageReplyMarkup", json=payload)
                data = resp.json()
                return bool(data.get("ok"))
            except Exception as e:
                logger.error(f"Failed to edit Telegram reply markup: {e}")
                return False

    async def answer_callback_query(self, callback_query_id: str, text: str = ""):
        """Acknowledge a Telegram button click."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                await client.post(
                    f"{self.base_url}/answerCallbackQuery",
                    json={"callback_query_id": callback_query_id, "text": text}
                )
            except Exception as e:
                logger.error(f"Error answering callback query: {e}")

    def build_in_flight_keyboard(self, incident_id: str, payment_url: str, amount: float) -> Dict[str, Any]:
        """Build inline keyboard for in-flight UPI drop-off."""
        host = os.getenv("APP_HOST_URL", "http://192.168.1.37:8000")
        checkout_url = payment_url if (payment_url and "localhost" not in payment_url) else f"{host}/pay/{incident_id}"
        buttons = [
            [
                {"text": f"💳 Complete via Razorpay (₹{amount:,.0f})", "url": checkout_url}
            ],
            [
                {"text": "🔄 Split into 2 Installments (PTP)", "callback_data": f"ptp:{incident_id}"},
                {"text": "❌ Cancel Order", "callback_data": f"cancel:{incident_id}"}
            ]
        ]
        return {"inline_keyboard": buttons}

    def build_b2b_dispute_keyboard(self, incident_id: str, va_upi: str, net_amount: float) -> Dict[str, Any]:
        """Build inline keyboard for B2B dispute resolution."""
        buttons = [
            [
                {"text": f"🏦 Pay Net ₹{net_amount:,.2f} (Smart Collect)", "callback_data": f"pay:{incident_id}"}
            ],
            [
                {"text": "📑 Accept Adjusted TDS Credit Note", "callback_data": f"accept_cn:{incident_id}"},
                {"text": "🚨 Escalate to Merchant CFO", "callback_data": f"escalate:{incident_id}"}
            ]
        ]
        return {"inline_keyboard": buttons}

telegram_service = TelegramService()
