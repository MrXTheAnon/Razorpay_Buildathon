from abc import ABC, abstractmethod
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.recovery import AuditLog, RecoveryIncident

class BaseRecoveryAgent(ABC):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    @abstractmethod
    async def diagnose(self, incident: RecoveryIncident) -> Dict[str, Any]:
        """Diagnose root cause from telemetry and transaction state."""
        pass

    @abstractmethod
    async def intervene(self, incident: RecoveryIncident, db: AsyncSession) -> Dict[str, Any]:
        """Execute bounded intervention with dynamic Razorpay link or Telegram card."""
        pass

    @abstractmethod
    def evaluate_stopping_rule(self, incident: RecoveryIncident, event_type: str, event_data: Dict[str, Any]) -> Optional[str]:
        """Evaluate whether to immediately halt execution based on safety/compliance rules."""
        pass

    async def log_audit(
        self,
        db: AsyncSession,
        incident_id: str,
        event_type: str,
        details: str,
        compliance_rule: str
    ) -> AuditLog:
        """Create an immutable, cryptographically hashed audit log."""
        # Find latest audit log for hash chaining
        stmt = select(AuditLog).where(AuditLog.incident_id == incident_id).order_by(AuditLog.id.desc()).limit(1)
        res = await db.execute(stmt)
        last_log = res.scalars().first()
        prev_hash = last_log.event_hash if last_log else "GENESIS_BLOCK"

        event_hash = AuditLog.generate_hash(prev_hash, incident_id, event_type, details)

        audit_entry = AuditLog(
            incident_id=incident_id,
            timestamp=datetime.datetime.utcnow(),
            agent_name=self.agent_name,
            event_type=event_type,
            details=details,
            compliance_rule=compliance_rule,
            event_hash=event_hash
        )
        db.add(audit_entry)
        await db.commit()
        return audit_entry
