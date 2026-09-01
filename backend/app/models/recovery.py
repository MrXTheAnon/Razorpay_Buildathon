import datetime
import hashlib
import json
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text
from backend.app.core.database import Base

def mask_chat_id(chat_id: str) -> str:
    """Mask Telegram chat ID to format: 6*******4."""
    if not chat_id:
        return ""
    cid = str(chat_id).strip()
    if len(cid) >= 2:
        return f"{cid[0]}*******{cid[-1]}"
    return "********"

def mask_phone(phone: str) -> str:
    """Mask customer phone number: +919876543210 -> +91 98****3210."""
    if not phone:
        return ""
    p = str(phone).strip()
    if len(p) > 6:
        return f"{p[:5]}****{p[-4:]}"
    return "******"

class RecoveryIncident(Base):
    __tablename__ = "recovery_incidents"

    id = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    customer_name = Column(String(128), default="Customer")
    customer_phone = Column(String(32), default="")
    telegram_chat_id = Column(String(64), default="")
    track = Column(String(64), index=True) # in_flight_upi, ptp_split, b2b_dispute, mandate_failure
    original_amount = Column(Float, default=0.0)
    currency = Column(String(10), default="INR")
    status = Column(String(32), default="pending", index=True) # pending, diagnosed, intervened, recovered, halted, escalated
    root_cause = Column(Text, default="")
    intervention_action = Column(Text, default="")
    stopping_rule_triggered = Column(Text, nullable=True)
    razorpay_payment_id = Column(String(64), nullable=True)
    razorpay_order_id = Column(String(64), nullable=True)
    payment_link_id = Column(String(64), nullable=True)
    payment_link_url = Column(String(512), nullable=True)
    telegram_message_id = Column(Integer, nullable=True)
    recovered_amount = Column(Float, default=0.0)
    extra_data = Column(Text, default="{}")

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "customer_name": self.customer_name,
            "customer_phone": mask_phone(self.customer_phone),
            "telegram_chat_id": mask_chat_id(self.telegram_chat_id),
            "track": self.track,
            "original_amount": self.original_amount,
            "currency": self.currency,
            "status": self.status,
            "root_cause": self.root_cause,
            "intervention_action": self.intervention_action,
            "stopping_rule_triggered": self.stopping_rule_triggered,
            "razorpay_payment_id": self.razorpay_payment_id,
            "razorpay_order_id": self.razorpay_order_id,
            "payment_link_id": self.payment_link_id,
            "payment_link_url": self.payment_link_url,
            "telegram_message_id": self.telegram_message_id,
            "recovered_amount": self.recovered_amount,
            "extra_data": json.loads(self.extra_data) if self.extra_data else {}
        }

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(64), index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    agent_name = Column(String(64))
    event_type = Column(String(64)) # DIAGNOSIS, INTERVENTION, STOPPING_RULE, RECOVERY_VERIFIED
    details = Column(Text)
    compliance_rule = Column(String(256))
    event_hash = Column(String(64))

    @staticmethod
    def generate_hash(prev_hash: str, incident_id: str, event_type: str, details: str) -> str:
        payload = f"{prev_hash}:{incident_id}:{event_type}:{details}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "agent_name": self.agent_name,
            "event_type": self.event_type,
            "details": self.details,
            "compliance_rule": self.compliance_rule,
            "event_hash": self.event_hash
        }

class BankHealthMetric(Base):
    __tablename__ = "bank_health_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bank_name = Column(String(64), unique=True)
    success_rate = Column(Float, default=95.0)
    status = Column(String(32), default="HEALTHY")
    npci_window_active = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "bank_name": self.bank_name,
            "success_rate": self.success_rate,
            "status": self.status,
            "npci_window_active": self.npci_window_active,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None
        }
