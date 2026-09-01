import uuid
import random
import json
import logging
from typing import Dict, Any, List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.config import settings
from backend.app.models.recovery import RecoveryIncident
from backend.app.agents.upi_dropoff_agent import upi_dropoff_agent
from backend.app.agents.ptp_agent import ptp_agent
from backend.app.agents.b2b_dispute_agent import b2b_dispute_agent
from backend.app.agents.mandate_healer_agent import mandate_healer_agent
from backend.app.agents.cross_border_agent import cross_border_agent

logger = logging.getLogger("razorloop.simulator")

FIRST_NAMES = [
    "Aarav", "Priya", "Vikram", "Ananya", "Rohan", "Sneha", "Karan", "Pooja",
    "Aditya", "Divya", "Siddharth", "Meera", "Arjun", "Neha", "Rahul", "Kavita",
    "Nikhil", "Tanvi", "Gaurav", "Isha", "Manish", "Rhea", "Harsh", "Shreya",
    "Kabir", "Anushka", "Dev", "Simran", "Aakash", "Pallavi", "Rishi", "Tara",
    "Varun", "Sunita", "Deepak", "Aarti", "Sameer", "Swati", "Pranav", "Nisha",
    "Kunal", "Bhavna", "Alok", "Rashmi", "Tarun", "Payal", "Abhishek", "Jyoti",
    "Rajesh", "Smriti", "Mohit", "Anjali", "Suresh", "Preeti", "Kartik", "Sandhya"
]

LAST_NAMES = [
    "Sharma", "Patel", "Malhotra", "Reddy", "Iyer", "Kulkarni", "Singhania", "Verma",
    "Joshi", "Nair", "Das", "Mukherjee", "Kapoor", "Chopra", "Bansal", "Mehta",
    "Bhatia", "Deshmukh", "Chawla", "Menon", "Agarwal", "Gupta", "Saxena", "Choudhury",
    "Pillai", "Rao", "Hegde", "Mishra", "Pandey", "Chatterjee", "Trivedi", "Shetty",
    "Nambiar", "Bose", "Sengupta", "Dutta", "Sethi", "Khanna", "Bajaj", "Mahajan",
    "Goel", "Rathore", "Pawar", "Solanki", "Bhardwaj", "Bhattacharya", "Nadkarni"
]

COMPANY_PREFIXES = [
    "Vortex", "Zenith", "Acme", "BlueDart", "Hyperion", "Nexus", "Apex", "Quantix",
    "Starlight", "Infini", "Solaria", "Optima", "Aura", "Trident", "Crest", "Novus",
    "Synergy", "Vector", "Titan", "Omni", "Prism", "Krypton", "Pulse", "Stratum",
    "Velocity", "Zephyr", "Aegis", "Catalyst", "Beacon", "Vertex", "Cobalt", "Zenithal"
]

COMPANY_SUFFIXES = [
    "SaaS Pvt Ltd", "Technologies", "Media Works", "Logistics", "Cloud Systems",
    "Infotech Ltd", "Solutions LLP", "Digital Labs", "Retail Networks", "Enterprises",
    "Supply Chain Pvt Ltd", "Fintech India", "Creative Agency", "Analytics LLP",
    "Consulting Group", "AI Studio", "Engineering Works", "Communications Pvt Ltd"
]

def generate_unique_person_name(used_names: Set[str]) -> str:
    """Generate a unique Indian person name that is not in used_names."""
    for _ in range(500):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        if name not in used_names:
            used_names.add(name)
            return name
    fallback = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)} {random.randint(10, 99)}"
    used_names.add(fallback)
    return fallback

def generate_unique_company_name(used_names: Set[str]) -> str:
    """Generate a unique B2B enterprise/company name that is not in used_names."""
    for _ in range(500):
        name = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)}"
        if name not in used_names:
            used_names.add(name)
            return name
    fallback = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)} ({random.randint(10, 99)})"
    used_names.add(fallback)
    return fallback

class SimulationService:
    async def create_and_trigger_incident(
        self,
        db: AsyncSession,
        track: str,
        customer_name: str = None,
        amount: float = None,
        telegram_chat_id: str = None,
        customer_phone: str = "+919876543210"
    ) -> RecoveryIncident:
        chat_id = telegram_chat_id or settings.TELEGRAM_DEMO_CHAT_ID
        
        # Collect existing names from DB to prevent collisions
        existing_names = set((await db.execute(select(RecoveryIncident.customer_name))).scalars().all())
        
        if customer_name:
            name = customer_name
        elif track == "b2b_dispute":
            name = generate_unique_company_name(existing_names)
        else:
            name = generate_unique_person_name(existing_names)

        incident_id = f"inc_{uuid.uuid4().hex[:8]}"

        if track == "in_flight_upi":
            amt = amount or random.choice([799.0, 1499.0, 2499.0, 3999.0])
            incident = RecoveryIncident(
                id=incident_id,
                customer_name=name,
                customer_phone=customer_phone,
                telegram_chat_id=chat_id,
                track="in_flight_upi",
                original_amount=amt,
                status="pending",
                root_cause="UPI Intent drop-off during app-switch; zero debit verified."
            )
            db.add(incident)
            await db.commit()
            await upi_dropoff_agent.intervene(incident, db)

        elif track == "ptp_split":
            amt = amount or random.choice([4999.0, 8999.0, 12499.0])
            incident = RecoveryIncident(
                id=incident_id,
                customer_name=name,
                customer_phone=customer_phone,
                telegram_chat_id=chat_id,
                track="ptp_split",
                original_amount=amt,
                status="pending",
                root_cause="Annual renewal cash constraint. Customer requested split payment."
            )
            db.add(incident)
            await db.commit()
            await ptp_agent.intervene(incident, db)

        elif track == "b2b_dispute":
            amt = amount or random.choice([32000.0, 45000.0, 68000.0, 85000.0, 120000.0])
            is_high_variance = random.random() < 0.35
            if is_high_variance:
                variance_pct = 10.0
                dispute_type = "TDS_194J"
                withheld_amt = amt * 0.10
            else:
                variance_pct = 2.0
                dispute_type = "TDS_194C"
                withheld_amt = amt * 0.02

            extra = {
                "dispute_type": dispute_type,
                "withheld_amount": withheld_amt,
                "variance_percent": variance_pct
            }
            incident = RecoveryIncident(
                id=incident_id,
                customer_name=name,
                customer_phone=customer_phone,
                telegram_chat_id=chat_id,
                track="b2b_dispute",
                original_amount=amt,
                status="pending",
                root_cause=f"AP team withholds {variance_pct}% under Section {dispute_type}.",
                extra_data=json.dumps(extra)
            )
            db.add(incident)
            await db.commit()
            await b2b_dispute_agent.intervene(incident, db)

        elif track == "mandate_failure":
            amt = amount or random.choice([999.0, 1499.0, 2499.0])
            incident = RecoveryIncident(
                id=incident_id,
                customer_name=name,
                customer_phone=customer_phone,
                telegram_chat_id=chat_id,
                track="mandate_failure",
                original_amount=amt,
                status="pending",
                root_cause="Recurring mandate debit timed out in issuer window."
            )
            db.add(incident)
            await db.commit()
            await mandate_healer_agent.intervene(incident, db)

        elif track == "cross_border":
            amt = amount or random.choice([5499.0, 9999.0, 18500.0, 32000.0])
            issuer = random.choice(["HDFC", "ICICI", "SBI", "AXIS"])
            card_net = random.choice(["Visa", "Mastercard"])
            extra = {
                "issuer_bank": issuer,
                "card_network": card_net,
                "error_code": "ISO_8583_57"
            }
            incident = RecoveryIncident(
                id=incident_id,
                customer_name=name,
                customer_phone=customer_phone,
                telegram_chat_id=chat_id,
                track="cross_border",
                original_amount=amt,
                status="pending",
                root_cause=f"Cross-border decline on {issuer} {card_net} (RBI international e-commerce lock).",
                extra_data=json.dumps(extra)
            )
            db.add(incident)
            await db.commit()
            await cross_border_agent.intervene(incident, db)

        else:
            raise ValueError(f"Unknown track: {track}")

        await db.refresh(incident)
        return incident

    async def run_batch_simulation(self, db: AsyncSession, count: int = 25) -> Dict[str, Any]:
        """Simulate a batch of at-risk transactions across all 5 tracks with guaranteed unique names."""
        tracks = ["in_flight_upi", "ptp_split", "b2b_dispute", "mandate_failure", "cross_border"]
        weights = [0.28, 0.20, 0.20, 0.16, 0.16]

        existing_names = set((await db.execute(select(RecoveryIncident.customer_name))).scalars().all())
        used_names: Set[str] = set(existing_names)

        total_at_risk = 0.0
        total_recovered = 0.0
        recovered_count = 0
        escalated_count = 0

        created_incidents = []
        for _ in range(count):
            selected_track = random.choices(tracks, weights=weights)[0]
            inc_id = f"batch_{uuid.uuid4().hex[:8]}"

            if selected_track == "in_flight_upi":
                name = generate_unique_person_name(used_names)
                amt = random.choice([899.0, 1499.0, 2199.0, 3499.0])
                total_at_risk += amt
                is_recovered = random.random() < 0.75
                rec_amt = amt if is_recovered else 0.0
                if is_recovered:
                    total_recovered += rec_amt
                    recovered_count += 1

                inc = RecoveryIncident(
                    id=inc_id,
                    customer_name=name,
                    track="in_flight_upi",
                    original_amount=amt,
                    recovered_amount=rec_amt,
                    status="recovered" if is_recovered else "intervened",
                    root_cause="In-flight UPI app-switch drop-off; zero debit verified.",
                    intervention_action="Dispatched instant 1-click fallback link with double-debit reassurance.",
                    stopping_rule_triggered="SUCCESS_STOP: Payment captured via Razorpay" if is_recovered else None
                )
                db.add(inc)
                created_incidents.append(inc)

            elif selected_track == "ptp_split":
                name = generate_unique_person_name(used_names)
                amt = random.choice([4999.0, 7999.0, 11999.0])
                total_at_risk += amt
                is_recovered = random.random() < 0.65
                rec_amt = (amt / 2) if is_recovered else 0.0
                if is_recovered:
                    total_recovered += rec_amt
                    recovered_count += 1

                inc = RecoveryIncident(
                    id=inc_id,
                    customer_name=name,
                    track="ptp_split",
                    original_amount=amt,
                    recovered_amount=rec_amt,
                    status="recovered" if is_recovered else "intervened",
                    root_cause="Customer liquidity constraint on renewal.",
                    intervention_action="Negotiated 2-tranche PTP settlement; paused all interim dunning.",
                    stopping_rule_triggered="PTP_TRANCHE_PAID: Tranche 1 paid; reminder paused" if is_recovered else None
                )
                db.add(inc)
                created_incidents.append(inc)

            elif selected_track == "b2b_dispute":
                company_name = generate_unique_company_name(used_names)
                amt = random.choice([28000.0, 32000.0, 45000.0, 64000.0, 85000.0, 110000.0])
                total_at_risk += amt
                is_escalated = random.random() < 0.30

                if not is_escalated:
                    variance_pct = 2.0
                    deducted_amt = amt * 0.02
                    net_amt = amt - deducted_amt
                    total_recovered += net_amt
                    recovered_count += 1
                    status = "recovered"
                    stopping = "SUCCESS_STOP: Net Virtual Account settled"
                    action = "Generated Smart Collect Virtual Account and Credit Note"
                    cause = f"AP deducted ₹{int(deducted_amt)} under Section 194C (2.0% variance)."
                else:
                    variance_pct = 10.0
                    deducted_amt = amt * 0.10
                    net_amt = 0.0
                    escalated_count += 1
                    status = "escalated"
                    stopping = "ESCALATION_STOP: Variance >5% escalated to CFO"
                    action = "Escalated to CFO"
                    cause = f"AP deducted ₹{int(deducted_amt)} under Section 194J (10.0% variance)."

                inc = RecoveryIncident(
                    id=inc_id,
                    customer_name=company_name,
                    track="b2b_dispute",
                    original_amount=amt,
                    recovered_amount=net_amt,
                    status=status,
                    root_cause=cause,
                    intervention_action=action,
                    stopping_rule_triggered=stopping
                )
                db.add(inc)
                created_incidents.append(inc)

            elif selected_track == "mandate_failure":
                name = generate_unique_person_name(used_names)
                amt = random.choice([999.0, 1499.0, 2499.0])
                total_at_risk += amt
                is_recovered = random.random() < 0.80
                rec_amt = amt if is_recovered else 0.0
                if is_recovered:
                    total_recovered += rec_amt
                    recovered_count += 1

                inc = RecoveryIncident(
                    id=inc_id,
                    customer_name=name,
                    track="mandate_failure",
                    original_amount=amt,
                    recovered_amount=rec_amt,
                    status="recovered" if is_recovered else "intervened",
                    root_cause="Issuer core banking downtime during NPCI 9 PM batch.",
                    intervention_action="Rescheduled 24-hr pre-debit notice to morning 06:30 AM window.",
                    stopping_rule_triggered="MANDATE_RESCHEDULED: Pre-debit notice re-aligned to 06:30 AM" if is_recovered else None
                )
                db.add(inc)
                created_incidents.append(inc)

            elif selected_track == "cross_border":
                name = generate_unique_person_name(used_names)
                amt = random.choice([5499.0, 8999.0, 16500.0, 32000.0])
                issuer = random.choice(["HDFC", "ICICI", "SBI", "AXIS"])
                total_at_risk += amt
                # 72% recovered via 1-tap card toggle or PayPal alternative rail
                is_recovered = random.random() < 0.72
                rec_amt = amt if is_recovered else 0.0
                if is_recovered:
                    total_recovered += rec_amt
                    recovered_count += 1

                inc = RecoveryIncident(
                    id=inc_id,
                    customer_name=name,
                    track="cross_border",
                    original_amount=amt,
                    recovered_amount=rec_amt,
                    status="recovered" if is_recovered else "intervened",
                    root_cause=f"Cross-border decline on {issuer} (ISO-8583 57: RBI international e-commerce lock).",
                    intervention_action=f"Dispatched {issuer} MyCards 1-tap unlock guidance + multi-rail fallback link.",
                    stopping_rule_triggered="SUCCESS_STOP: 3DS2 re-authenticated via card toggle" if is_recovered else None
                )
                db.add(inc)
                created_incidents.append(inc)

        await db.commit()

        rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0.0
        msg_cost = count * 2.50
        roi = (total_recovered / msg_cost) if msg_cost > 0 else 0.0

        return {
            "batch_id": f"batch_{uuid.uuid4().hex[:8]}",
            "total_incidents_processed": count,
            "summary": {
                "total_at_risk_inr": round(total_at_risk, 2),
                "total_recovered_inr": round(total_recovered, 2),
                "recovery_rate_percent": round(rate, 2),
                "roi_multiplier": round(roi, 1),
                "recovered_count": recovered_count,
                "escalated_count": escalated_count
            }
        }

simulation_service = SimulationService()
