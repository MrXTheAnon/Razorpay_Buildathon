import pytest
import asyncio
from backend.app.core.database import init_db, async_session_factory
from backend.app.services.simulation_service import simulation_service
from backend.app.services.bank_health_service import bank_health_service
from backend.app.services.razorpay_service import razorpay_service

def test_bank_telemetry():
    banks = bank_health_service.get_all_banks()
    assert "HDFC" in banks
    assert "SBI" in banks
    assert banks["HDFC"]["success_rate"] > 90

def test_razorpay_service_init():
    assert razorpay_service.client is not None or razorpay_service.key_id != ""

@pytest.mark.asyncio
async def test_batch_simulation():
    await init_db()
    async with async_session_factory() as db:
        res = await simulation_service.run_batch_simulation(db=db, count=5)
        assert res["batch_size"] == 5
        assert res["total_at_risk_inr"] > 0
        assert res["recovery_rate_percent"] >= 0
