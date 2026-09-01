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
        """Create a real Razorpay Payment Link in test mode with graceful fallback."""
        amount_paise = int(amount_inr * 100)
        phone = customer_phone if customer_phone and len(customer_phone) >= 10 else "+919876543210"
        
        # Clean phone format
        if not phone.startswith("+91"):
            phone = f"+91{phone[-10:]}"

        if self.client:
            try:
                reference_id = f"rec_{incident_id}_{uuid.uuid4().hex[:6]}" if incident_id else f"rec_{uuid.uuid4().hex[:8]}"
                res = self.client.payment_link.create({
                    "amount": amount_paise,
                    "currency": "INR",
                    "accept_partial": False,
                    "description": description[:250],
                    "reference_id": reference_id,
                    "customer": {
                        "name": customer_name,
                        "contact": phone
                    },
                    "notify": {
                        "sms": False,
                        "email": False
                    },
                    "reminder_enable": False,
                    "notes": {
                        "incident_id": incident_id or "",
                        "agent": "RazorLoop"
                    }
                })
                logger.info(f"Created Razorpay Payment Link: {res.get('short_url')} (ID: {res.get('id')})")
                return {
                    "id": res.get("id"),
                    "short_url": res.get("short_url"),
                    "amount": amount_inr,
                    "status": res.get("status")
                }
            except Exception as e:
                logger.error(f"Failed to create Razorpay payment link via API: {e}. Generating simulated link.")

        # Fallback simulation
        mock_id = f"plink_mock_{uuid.uuid4().hex[:10]}"
        return {
            "id": mock_id,
            "short_url": f"https://rzp.io/i/{mock_id}",
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
