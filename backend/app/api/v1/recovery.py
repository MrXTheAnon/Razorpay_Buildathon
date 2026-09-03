from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from backend.app.core.database import get_db
from backend.app.models.recovery import RecoveryIncident, AuditLog
from backend.app.services.simulation_service import simulation_service
from backend.app.services.bank_health_service import bank_health_service
from backend.app.services.telegram_service import telegram_service
from backend.app.services.razorpay_service import razorpay_service
from backend.app.services.omniroute_ai_service import omniroute_ai_service

router = APIRouter(prefix="/recovery", tags=["Recovery & Simulation"])

class SimulateRequest(BaseModel):
    track: str = Field("in_flight_upi", description="in_flight_upi, ptp_split, b2b_dispute, mandate_failure")
    customer_name: Optional[str] = None
    amount: Optional[float] = None
    telegram_chat_id: Optional[str] = None
    customer_phone: Optional[str] = "+919876543210"

class BatchSimulateRequest(BaseModel):
    count: int = Field(20, ge=5, le=100)

class SimulatePaymentRequest(BaseModel):
    incident_id: str
    amount: Optional[float] = None

@router.post("/simulate")
async def simulate_single_incident(
    req: SimulateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Trigger a live at-risk incident with real Razorpay link and Telegram dispatch."""
    try:
        incident = await simulation_service.create_and_trigger_incident(
            db=db,
            track=req.track,
            customer_name=req.customer_name,
            amount=req.amount,
            telegram_chat_id=req.telegram_chat_id,
            customer_phone=req.customer_phone
        )
        return {"status": "success", "incident": incident.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-simulate")
async def batch_simulate(
    req: BatchSimulateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Run a batch simulation of multiple at-risk incidents and calculate recovered money."""
    result = await simulation_service.run_batch_simulation(db=db, count=req.count)
    return {"status": "success", "summary": result}

async def sync_paid_payment_links(db: AsyncSession):
    """Auto-detect if any customer completed payment on Razorpay testnet."""
    if not razorpay_service.client:
        return
    try:
        stmt = select(RecoveryIncident).where(
            RecoveryIncident.status == "intervened",
            RecoveryIncident.payment_link_id.isnot(None)
        ).limit(5)
        res = await db.execute(stmt)
        intervened = res.scalars().all()
        for inc in intervened:
            try:
                plink_data = razorpay_service.client.payment_link.fetch(inc.payment_link_id)
                if plink_data.get("status") == "paid":
                    paid_amt = float(plink_data.get("amount_paid", 0)) / 100 or inc.original_amount
                    inc.status = "recovered"
                    inc.recovered_amount = paid_amt
                    inc.razorpay_payment_id = (
                        plink_data.get("payments", [{}])[0].get("payment_id")
                        if plink_data.get("payments")
                        else f"pay_rzp_{inc.id[-6:]}"
                    )
                    inc.stopping_rule_triggered = f"SUCCESS_STOP: Payment of ₹{paid_amt:,.2f} verified on Razorpay."

                    # Update Telegram card to show "✅ Paid"
                    if inc.telegram_chat_id and inc.telegram_message_id:
                        text = (
                            f"🎉 <b>Payment Captured via NetBanking!</b>\n\n"
                            f"Order: <b>{inc.id}</b>\n"
                            f"Customer: <b>{inc.customer_name}</b>\n"
                            f"Amount Paid: <b>₹{paid_amt:,.2f}</b>\n\n"
                            f"🛡️ <b>Stopping Rule Triggered:</b> Debt satisfied. All dunning and reminders terminated."
                        )
                        keyboard = {
                            "inline_keyboard": [
                                [{"text": f"✅ Paid ₹{paid_amt:,.2f} (Confirmed)", "callback_data": f"paid:{inc.id}"}]
                            ]
                        }
                        await telegram_service.edit_message(
                            chat_id=inc.telegram_chat_id,
                            message_id=inc.telegram_message_id,
                            text=text,
                            reply_markup=keyboard
                        )

                    audit = AuditLog(
                        incident_id=inc.id,
                        agent_name="Razorpay_Payment_Sync",
                        event_type="RECOVERY_VERIFIED",
                        details=f"Payment link {inc.payment_link_id} verified as PAID on Razorpay (₹{paid_amt:,.2f}). Dunning terminated.",
                        compliance_rule="Instant Cessation of Dunning upon Debt Satisfaction",
                        event_hash=AuditLog.generate_hash("PAY_SYNC_HASH", inc.id, "RECOVERY_VERIFIED", str(paid_amt))
                    )
                    db.add(audit)
                    await db.commit()
            except Exception:
                pass
    except Exception:
        pass

@router.get("/incidents")
async def list_incidents(
    track: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List recovery incidents with optional filtering."""
    await sync_paid_payment_links(db)
    query = select(RecoveryIncident).order_by(desc(RecoveryIncident.created_at)).offset(offset).limit(limit)
    if track:
        query = query.where(RecoveryIncident.track == track)
    if status:
        query = query.where(RecoveryIncident.status == status)

    res = await db.execute(query)
    incidents = res.scalars().all()
    return [inc.to_dict() for inc in incidents]

@router.get("/metrics")
async def get_recovery_metrics(db: AsyncSession = Depends(get_db)):
    """Aggregate financial metrics: At-Risk vs Recovered, ROI, and Track breakdowns."""
    await sync_paid_payment_links(db)
    # Totals
    stmt = select(
        func.count(RecoveryIncident.id),
        func.sum(RecoveryIncident.original_amount),
        func.sum(RecoveryIncident.recovered_amount)
    )
    res = await db.execute(stmt)
    total_count, total_at_risk, total_recovered = res.first()

    total_at_risk = float(total_at_risk or 0.0)
    total_recovered = float(total_recovered or 0.0)
    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0.0

    # Count by status
    status_counts = {}
    for st in ["pending", "intervened", "recovered", "halted", "escalated"]:
        cnt_res = await db.execute(select(func.count(RecoveryIncident.id)).where(RecoveryIncident.status == st))
        status_counts[st] = cnt_res.scalar() or 0

    # Breakdown by track
    track_stmt = select(
        RecoveryIncident.track,
        func.count(RecoveryIncident.id),
        func.sum(RecoveryIncident.original_amount),
        func.sum(RecoveryIncident.recovered_amount)
    ).group_by(RecoveryIncident.track)
    track_res = (await db.execute(track_stmt)).all()

    by_track = []
    for tr, c, at_risk, rec in track_res:
        ar = float(at_risk or 0.0)
        rc = float(rec or 0.0)
        by_track.append({
            "track": tr,
            "count": c,
            "at_risk_inr": ar,
            "recovered_inr": rc,
            "recovery_rate": round((rc / ar * 100) if ar > 0 else 0, 1)
        })

    messaging_cost = (total_count or 0) * 2.5
    roi = ((total_recovered - messaging_cost) / messaging_cost) if messaging_cost > 0 else 0.0

    return {
        "total_incidents": total_count or 0,
        "total_at_risk_inr": round(total_at_risk, 2),
        "total_recovered_inr": round(total_recovered, 2),
        "recovery_rate_percent": round(recovery_rate, 2),
        "status_breakdown": status_counts,
        "track_breakdown": by_track,
        "estimated_messaging_cost_inr": messaging_cost,
        "roi_multiplier": round(roi, 1)
    }

@router.get("/audit-logs")
async def get_audit_logs(
    incident_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve immutable audit logs with hash integrity verification."""
    query = select(AuditLog).order_by(desc(AuditLog.id)).limit(limit)
    if incident_id:
        query = query.where(AuditLog.incident_id == incident_id)
    res = await db.execute(query)
    logs = res.scalars().all()
    return [log.to_dict() for log in logs]

@router.get("/bank-telemetry")
async def get_bank_telemetry():
    """Retrieve simulated Indian banking telemetry for retry window decisions."""
    return bank_health_service.get_all_banks()

@router.post("/simulate-payment")
async def simulate_payment(
    req: SimulatePaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Manually simulate payment capture to trigger the agent's stopping rule for demo."""
    res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.id == req.incident_id))
    inc = res.scalars().first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    pay_amount = req.amount or inc.original_amount
    inc.status = "recovered"
    inc.recovered_amount = pay_amount
    inc.razorpay_payment_id = f"pay_sim_{inc.id[-6:]}"
    inc.stopping_rule_triggered = f"SUCCESS_STOP: Demo payment captured for ₹{pay_amount:,.2f}."

    if inc.telegram_message_id and inc.telegram_chat_id:
        msg = (
            f"🎉 <b>Payment Captured! (Demo Simulation)</b>\n\n"
            f"Order: <b>{inc.id}</b>\n"
            f"Amount Paid: <b>₹{pay_amount:,.2f}</b>\n\n"
            f"🛡️ <b>Stopping Rule Triggered:</b> All further dunning terminated."
        )
        await telegram_service.edit_message(
            chat_id=inc.telegram_chat_id,
            message_id=inc.telegram_message_id,
            text=msg,
            reply_markup=None
        )

    # Log audit
    audit = AuditLog(
        incident_id=inc.id,
        agent_name="Demo_Simulator",
        event_type="RECOVERY_VERIFIED",
        details=f"Payment verified for ₹{pay_amount}. Stopping rule executed.",
        compliance_rule="Instant Cessation of Dunning upon Debt Satisfaction",
        event_hash=AuditLog.generate_hash("DEMO_HASH", inc.id, "RECOVERY_VERIFIED", str(pay_amount))
    )
    db.add(audit)
    await db.commit()
    return {"status": "success", "incident": inc.to_dict()}

@router.post("/reset")
async def reset_ledger(db: AsyncSession = Depends(get_db)):
    """Wipe all recovery incidents and audit logs to start with a completely fresh slate."""
    from sqlalchemy import delete
    await db.execute(delete(RecoveryIncident))
    await db.execute(delete(AuditLog))
    await db.commit()
    return {"status": "success", "message": "Ledger wiped. Fresh start ready."}

@router.post("/ai-executive-debrief")
async def get_ai_executive_debrief(db: AsyncSession = Depends(get_db)):
    """Generate live executive portfolio debrief via OmniRoute AI Gateway."""
    stmt = select(
        func.count(RecoveryIncident.id),
        func.sum(RecoveryIncident.original_amount),
        func.sum(RecoveryIncident.recovered_amount)
    )
    res = await db.execute(stmt)
    total_count, total_at_risk, total_recovered = res.first()

    total_at_risk = float(total_at_risk or 0.0)
    total_recovered = float(total_recovered or 0.0)
    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0.0

    msg_cost = (total_count or 0) * 2.50
    roi = (total_recovered / msg_cost) if msg_cost > 0 else 0.0

    track_stmt = select(
        RecoveryIncident.track,
        func.count(RecoveryIncident.id),
        func.sum(RecoveryIncident.original_amount),
        func.sum(RecoveryIncident.recovered_amount)
    ).group_by(RecoveryIncident.track)
    track_res = (await db.execute(track_stmt)).all()

    by_track = [
        {"track": tr, "count": c, "at_risk": float(ar or 0), "recovered": float(rec or 0)}
        for tr, c, ar, rec in track_res
    ]

    bank_data = bank_health_service.get_all_banks()

    debrief = await omniroute_ai_service.generate_executive_debrief(
        total_at_risk=total_at_risk,
        total_recovered=total_recovered,
        recovery_rate=recovery_rate,
        roi_multiplier=roi,
        incident_count=total_count or 0,
        track_breakdown=by_track,
        bank_telemetry=bank_data
    )

    return {
        "status": "success",
        "provider": "OmniRoute Multi-Model Gateway",
        "model": omniroute_ai_service.model,
        "debrief": debrief
    }
