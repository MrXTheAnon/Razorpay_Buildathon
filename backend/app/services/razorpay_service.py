import os
import socket
import logging
import hmac
import hashlib
import uuid
import razorpay
from backend.app.config import settings

logger = logging.getLogger("razorloop.razorpay")

class RazorpayService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        if self.key_id and self.key_secret:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        else:
            self.client = None

    def create_payment_link(
        self,
        amount_inr: float,
        description: str,
        customer_name: str,
        customer_phone: str = "+919876543210",
        incident_id: str = None
    ) -> dict:
        """Create a dedicated standard checkout link for exact customer and amount."""
        inc_id = incident_id or f"inc_{uuid.uuid4().hex[:8]}"
        host = os.getenv("APP_HOST_URL", "http://192.168.1.37:8000")
        checkout_url = f"{host}/pay/{inc_id}"
        order_id = None
        if self.client:
            try:
                order = self.client.order.create({
                    "amount": int(amount_inr * 100),
                    "currency": "INR",
                    "receipt": f"rcpt_{inc_id[-12:]}",
                    "notes": {
                        "incident_id": inc_id,
                        "customer_name": customer_name,
                        "agent": "RazorLoop"
                    }
                })
                order_id = order.get("id")
                logger.info(f"Created Razorpay Order {order_id} for {customer_name} (₹{amount_inr:,.2f})")
            except Exception as e:
                logger.warning(f"Could not create Razorpay order: {e}")

        return {
            "id": order_id or f"plink_{inc_id[-12:]}",
            "short_url": checkout_url,
            "amount": amount_inr,
            "status": "created"
        }

    def verify_webhook_signature(self, body_bytes: bytes, signature: str) -> bool:
        """Verify Razorpay webhook HMAC SHA256 signature."""
        if not self.webhook_secret or self.webhook_secret == "whsec_xxx":
            return True # Allow testing if secret not configured
        try:
            expected = hmac.new(
                self.webhook_secret.encode("utf-8"),
                body_bytes,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    def create_smart_collect_va(self, invoice_number: str, amount_inr: float, customer_name: str) -> dict:
        """Simulate or create Razorpay Smart Collect Virtual Account for B2B dispute net settlement."""
        account_number = f"RZP{uuid.uuid4().hex[:10].upper()}"
        ifsc = "RAZR0000001"
        upi_id = f"b2b.{invoice_number.lower()}@razorpay"
        return {
            "virtual_account_id": f"va_{uuid.uuid4().hex[:8]}",
            "account_number": account_number,
            "ifsc": ifsc,
            "upi_id": upi_id,
            "amount": amount_inr,
            "beneficiary_name": f"RazorLoop Escrow - {customer_name}"
        }

razorpay_service = RazorpayService()
