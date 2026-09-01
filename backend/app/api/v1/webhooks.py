import json
import logging
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.recovery import RecoveryIncident, AuditLog
from backend.app.services.razorpay_service import razorpay_service
from backend.app.services.telegram_service import telegram_service

logger = logging.getLogger("razorloop.webhooks")

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle Razorpay Gateway Webhooks (payment.captured, payment_link.paid)."""
    body_bytes = await request.body()
    
    if x_razorpay_signature:
        is_valid = razorpay_service.verify_webhook_signature(body_bytes, x_razorpay_signature)
        if not is_valid:
            logger.warning("Invalid Razorpay webhook signature received.")
            raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        event = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")

    event_type = event.get("event")
    logger.info(f"Received Razorpay webhook event: {event_type}")

    payload_data = event.get("payload", {})
    payment = payload_data.get("payment", {}).get("entity", {})
    plink = payload_data.get("payment_link", {}).get("entity", {})

    # Extract incident identifier
    incident_id = None
    notes = payment.get("notes") or plink.get("notes") or {}
    if "incident_id" in notes:
        incident_id = notes["incident_id"]

    # Match by payment link id or reference id
    target_incident = None
    if incident_id:
        res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.id == incident_id))
        target_incident = res.scalars().first()

    if not target_incident and plink.get("id"):
        res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.payment_link_id == plink["id"]))
        target_incident = res.scalars().first()

    if event_type in ["payment.captured", "payment_link.paid", "order.paid"]:
        amount_paid = (payment.get("amount") or plink.get("amount", 0)) / 100.0
        pay_id = payment.get("id") or plink.get("id", "captured_pay_id")

        if target_incident:
            target_incident.status = "recovered"
            target_incident.recovered_amount = amount_paid or target_incident.original_amount
            target_incident.razorpay_payment_id = pay_id
            target_incident.stopping_rule_triggered = (
                f"SUCCESS_STOP: Payment {pay_id} captured. Immediate cessation of all dunning."
            )

            # Update Telegram card to show success
            if target_incident.telegram_message_id and target_incident.telegram_chat_id:
                success_msg = (
                    f"🎉 <b>Payment Successfully Captured!</b>\n\n"
                    f"Order Reference: <b>{target_incident.id}</b>\n"
                    f"Payment ID: <code>{pay_id}</code>\n"
                    f"Amount Paid: <b>₹{target_incident.recovered_amount:,.2f}</b>\n\n"
                    f"🛡️ <b>Stopping Rule Triggered:</b> All further dunning and retry notifications have been terminated."
                )
                await telegram_service.edit_message(
                    chat_id=target_incident.telegram_chat_id,
                    message_id=target_incident.telegram_message_id,
                    text=success_msg,
                    reply_markup=None
                )

            # Record audit log
            stmt = select(AuditLog).where(AuditLog.incident_id == target_incident.id).order_by(AuditLog.id.desc()).limit(1)
            last_log = (await db.execute(stmt)).scalars().first()
            prev_hash = last_log.event_hash if last_log else "GENESIS"
            
            audit = AuditLog(
                incident_id=target_incident.id,
                agent_name="Webhook_Controller",
                event_type="RECOVERY_VERIFIED",
                details=f"Payment {pay_id} captured for ₹{target_incident.recovered_amount}. Stopping rule executed.",
                compliance_rule="Instant Cessation of Dunning upon Debt Satisfaction",
                event_hash=AuditLog.generate_hash(prev_hash, target_incident.id, "RECOVERY_VERIFIED", pay_id)
            )
            db.add(audit)
            await db.commit()

            return {"status": "recovered", "incident_id": target_incident.id, "amount": target_incident.recovered_amount}

    return {"status": "received", "event": event_type}
