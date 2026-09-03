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
UPI_CAUSES = [
    "GPay app-switch freeze on 5G handshake; zero debit verified on issuer core.",
    "PhonePe biometric timeout during checkout; buyer halted fearing duplicate debit.",
    "Paytm session killed during app transition; core switch confirms zero debit.",
    "UPI Intent handler killed by iOS memory manager; bank account untouched.",
    "BHIM server-side handshake latency exceeded 45s; zero debit confirmed.",
    "Cred UPI app-switch drop-off; buyer hesitated on second attempt after latency lag.",
    "Amazon Pay UPI intent crashed on OTP autofill; zero funds debited from bank.",
    "WhatsApp Pay intent return hook timed out; customer abandoned checkout cart."
]

PTP_CAUSES = [
    "Q3 cash flow squeeze on annual renewal; customer requested 2-tranche split.",
    "Corporate credit card limit reached; buyer negotiated 50% upfront milestone.",
    "End-of-month liquidity constraint; customer agreed to 50/50 payment plan.",
    "Quarterly enterprise budget cycle transition; deferred 50% balance to net-15.",
    "Payroll timing mismatch on executive plan; requested 14-day grace period on 2nd tranche.",
    "Subscription upgrade sticker shock; customer opted for 2x milestone settlement."
]

B2B_CAUSES_NORMAL = [
    "AP department deducted ₹{deducted} under Section 194C (2.0% contractor TDS variance).",
    "Client accounts payable withheld ₹{deducted} under Section 194C; certificate pending in TRACES.",
    "Enterprise finance deducted ₹{deducted} (2.0% statutory TDS) awaiting Form 16A reconciliation.",
    "Corporate procurement withheld ₹{deducted} (Section 194Q 0.1% purchase TDS variance)."
]

B2B_CAUSES_ESCALATED = [
    "Enterprise finance deducted ₹{deducted} under Section 194J (10.0% professional tax variance).",
    "Client AP disputed milestone delivery and withheld ₹{deducted} (12.5% invoice holdback).",
    "Vendor management withheld ₹{deducted} under Section 194J; exceeds 5% auto-clearance threshold."
]

MANDATE_CAUSES = [
    "SBI core banking nightly maintenance (8-11 PM) locked NPCI auto-debit batch.",
    "HDFC e-NACH mandate presentation timed out due to issuer CBS switch overload.",
    "ICICI recurring UPI autopay throttled during 9 PM settlement cycle.",
    "Axis Bank recurring auto-debit returned R08 (Issuer Switch Inoperative).",
    "Kotak e-mandate presentation failed; core banking scheduled maintenance active.",
    "Bank of Baroda NPCI auto-debit timed out in 10 PM batch window."
]

CROSS_BORDER_CAUSES = [
    "HDFC Visa Signature declined (ISO-8583 57: International e-commerce toggle disabled).",
    "ICICI Mastercard blocked under RBI LRS mandate; requires 1-tap iMobile unlock.",
    "SBI Global Debit card rejected: foreign currency cross-border limit set to ₹0.",
    "Axis Bank World card declined: 3DS2 frictionless flow failed issuer risk filter.",
    "Standard Chartered card blocked for overseas SaaS billing under RBI card tokenization rules.",
    "Amex India card auto-declined due to missing dynamic OTP in foreign merchant flow."
]

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

    async def run_batch_simulation(self, db: AsyncSession, count: int = 20) -> Dict[str, Any]:
        """Simulate a batch of at-risk transactions across all 5 tracks with guaranteed unique names and randomized causes."""
        tracks = ["in_flight_upi", "ptp_split", "b2b_dispute", "mandate_failure", "cross_border"]
        weights = [0.25, 0.20, 0.25, 0.15, 0.15]

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
                amt = float(random.choice([799, 999, 1249, 1499, 1899, 2499, 3299, 4999]))
                total_at_risk += amt
                is_recovered = random.random() < 0.75
                rec_amt = amt if is_recovered else 0.0
                if is_recovered:
                    total_recovered += rec_amt
                    recovered_count += 1

                cause = random.choice(UPI_CAUSES)
                inc = RecoveryIncident(
                    id=inc_id,
                    customer_name=name,
                    track="in_flight_upi",
                    original_amount=amt,
                    recovered_amount=rec_amt,
                    status="recovered" if is_recovered else "intervened",
                    root_cause=cause,
                    intervention_action="Dispatched instant 1-click fallback link with zero-debit reassurance.",
                    stopping_rule_triggered="SUCCESS_STOP: Payment captured via Razorpay" if is_recovered else None
                )
                db.add(inc)
                created_incidents.append(inc)

            elif selected_track == "ptp_split":
                name = generate_unique_person_name(used_names)
                amt = float(random.choice([3999, 5499, 7999, 9499, 12999, 15999]))
                total_at_risk += amt
                is_recovered = random.random() < 0.65
                rec_amt = (amt / 2) if is_recovered else 0.0
                if is_recovered:
                    total_recovered += rec_amt
                    recovered_count += 1

                cause = random.choice(PTP_CAUSES)
                inc = RecoveryIncident(
                    id=inc_id,
                    customer_name=name,
                    track="ptp_split",
                    original_amount=amt,
                    recovered_amount=rec_amt,
                    status="recovered" if is_recovered else "intervened",
                    root_cause=cause,
                    intervention_action="Negotiated 2-tranche milestone settlement; paused all interim dunning.",
                    stopping_rule_triggered="PTP_TRANCHE_PAID: Tranche 1 paid; reminder paused" if is_recovered else None
                )
                db.add(inc)
                created_incidents.append(inc)

            elif selected_track == "b2b_dispute":
                company_name = generate_unique_company_name(used_names)
                amt = float(random.choice([24000, 38500, 48000, 62000, 85000, 115000, 142000]))
                total_at_risk += amt
                is_escalated = random.random() < 0.30

                if not is_escalated:
                    variance_pct = 2.0
                    deducted_amt = round(amt * 0.02, 2)
                    net_amt = amt - deducted_amt
                    total_recovered += net_amt
                    recovered_count += 1
                    status = "recovered"
                    stopping = "SUCCESS_STOP: Net Virtual Account settled"
                    action = "Generated Smart Collect Virtual Account and Credit Note"
                    cause = random.choice(B2B_CAUSES_NORMAL).format(deducted=int(deducted_amt))
                else:
                    variance_pct = 10.0
                    deducted_amt = round(amt * 0.10, 2)
                    net_amt = 0.0
                    escalated_count += 1
                    status = "escalated"
                    stopping = "ESCALATION_STOP: Variance >5% escalated to CFO"
                    action = "Escalated to CFO with automated tax memo"
                    cause = random.choice(B2B_CAUSES_ESCALATED).format(deducted=int(deducted_amt))

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
                amt = float(random.choice([799, 1199, 1499, 1999, 2999, 4499]))
                total_at_risk += amt
                is_recovered = random.random() < 0.80
                rec_amt = amt if is_recovered else 0.0
                if is_recovered:
                    total_recovered += rec_amt
                    recovered_count += 1

                cause = random.choice(MANDATE_CAUSES)
                inc = RecoveryIncident(
                    id=inc_id,
                    customer_name=name,
                    track="mandate_failure",
                    original_amount=amt,
                    recovered_amount=rec_amt,
                    status="recovered" if is_recovered else "intervened",
                    root_cause=cause,
                    intervention_action="Rescheduled 24-hr pre-debit notice to morning 06:30 AM window.",
                    stopping_rule_triggered="MANDATE_RESCHEDULED: Pre-debit notice re-aligned to 06:30 AM" if is_recovered else None
                )
                db.add(inc)
                created_incidents.append(inc)

            elif selected_track == "cross_border":
                name = generate_unique_person_name(used_names)
                amt = float(random.choice([4999, 6999, 9999, 14500, 22000, 35000]))
                total_at_risk += amt
                is_recovered = random.random() < 0.72
                rec_amt = amt if is_recovered else 0.0
                if is_recovered:
                    total_recovered += rec_amt
                    recovered_count += 1

                cause = random.choice(CROSS_BORDER_CAUSES)
                inc = RecoveryIncident(
                    id=inc_id,
                    customer_name=name,
                    track="cross_border",
                    original_amount=amt,
                    recovered_amount=rec_amt,
                    status="recovered" if is_recovered else "intervened",
                    root_cause=cause,
                    intervention_action="Dispatched 1-tap mobile bank unlock guidance and alternative rail link.",
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
