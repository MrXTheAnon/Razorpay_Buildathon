# RazorLoop

> **Autonomous, Bounded Revenue Recovery Engine Built on Razorpay Rails**  
> *Track 03: AI Revenue Recovery — Razorpay Buildathon 2026*

---

## 1. The Core Problem: Why Blind Retries Fail

In payment engineering, revenue loss is rarely an atomic, single-step failure. It is almost always a procedural degradation:
* An OS terminates a mobile browser session during a UPI app-switch, leaving the customer terrified that their bank account will be double-debited.
* An annual SaaS subscriber hits an end-of-month credit card limit and is cancelled by an inflexible all-or-nothing billing system.
* An enterprise Accounts Payable department unilaterally withholds 2% TDS under Section 194C on a ₹45,000 invoice, leaving standard ERPs to blindly spam the client CFO with ignored overdue notices.
* Recurring UPI Autopay / e-NACH debits fire blindly during NPCI core banking maintenance (8 PM–11 PM), triggering bank rejection fees and NPCI mandate auto-revocation.
* International cardholders purchasing in India have their transactions rejected under RBI LRS default-disabled card controls, receiving only an opaque `ISO-8583 57: Transaction Not Permitted` error.

Standard recovery tools rely on blind cron retries and spammy dunning emails. In India's regulated financial rails, blind retries are actively destructive: they violate bank throttling limits, incur merchant penalties, and permanently churn customers.

**RazorLoop** is an autonomous, event-driven recovery engine that closes the loop between gateway telemetry, issuing bank health, and context-aware interventions—strictly governed by deterministic **stopping rules**.

---

## 2. Architecture: The Tri-State Protocol

Every autonomous recovery workflow in RazorLoop enforces a three-stage bounded lifecycle:

```
┌─────────────────┐       ┌────────────────────────┐       ┌─────────────────────────┐
│   1. DIAGNOSE   │ ────> │ 2. BOUNDED INTERVENE   │ ────> │  3. HARD STOPPING RULE  │
└─────────────────┘       └────────────────────────┘       └─────────────────────────┘
  • Gateway state           • 1-Click Razorpay link          • payment.captured webhook
  • Bank telemetry          • Smart Collect Net VA           • Explicit user opt-out
  • Dispute variance        • Rescheduled PN notice          • Max retry / CFO ceiling
```

1. **Diagnosis**: At failure detection ($T+90\text{s}$), the agent inspects the Razorpay gateway state and issuer telemetry to verify zero-debit conditions, withholding percentages, or maintenance windows before taking action.
2. **Bounded Intervention**: The agent executes a bounded, non-coercive recovery action: generating dynamic Razorpay Payment Links, structuring multi-tranche PTP agreements, or creating Net Smart Collect Virtual Accounts.
3. **Hard Stopping Rule**: Dunning and retries cease immediately upon debt satisfaction (`payment.captured`), customer cancellation (`cancel:`), or policy breaches (e.g., dispute variance $> 5\%$).

---

## 3. The 5 Autonomous Recovery Agents

| # | Recovery Agent | Failure Mode Targeted | Autonomous Action | Deterministic Stopping Rule |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **In-Flight UPI Drop-off Reassurer** | Mobile app-switch crash during UPI checkout; buyer halts fearing double-debit. | Confirms ₹0 debited on issuer; issues instant 1-click fallback link with 15-min cart lock. | Halts instantly on `payment.captured` or user clicking *Cancel Order*. |
| **2** | **Promise-to-Pay (PTP) Negotiator** | Annual renewal failure due to temporary credit/cash-flow constraint. | Restructures debt into 2x 50% tranches; locks in a 15-day dunning pause. | Capturing Tranche 1 payment suppresses all automated dunning. |
| **3** | **B2B TDS / GST Dispute Chaser** | Enterprise AP withholds 2% TDS (194C vs 194J); invoices stall indefinitely. | Auto-validates variance ($\le 5\%$); generates Net Smart Collect VA + Credit Note draft. | Variance $> 5\%$ halts reminders and escalates packet directly to CFO. |
| **4** | **Mandate Degradation Healer** | UPI Autopay / e-NACH failures during bank maintenance (e.g., SBI 8–11 PM). | Inspects bank telemetry; auto-reschedules 24-hr pre-debit notice to `06:30 AM`. | Suppresses blind retries; enforces maximum 3 compliant attempts. |
| **5** | **Cross-Border Decline Translator** | International card decline under RBI default-off international e-commerce rules. | Identifies issuer (HDFC/ICICI/SBI); sends 1-tap app toggle guide + PayPal fallback. | Halts upon 3DS2 re-authentication or alternative rail selection. |

---

## 4. Razorpay Rails & Integrations

RazorLoop interfaces directly with core Razorpay primitives:

* **Razorpay Payment Links API (`/v1/payment_links`)**: Dynamically generates localized, multi-rail payment links embedded into interactive Telegram recovery cards.
* **Razorpay Smart Collect Virtual Accounts (`/v1/virtual_accounts`)**: Provisions dedicated virtual accounts (UPI ID + NEFT/IFSC) for B2B net settlements, automatically reconciling disputed invoices.
* **Webhook Verification Engine**: Verifies cryptographic signatures using `X-Razorpay-Signature` and HMAC-SHA256 against `RAZORPAY_WEBHOOK_SECRET` to execute immediate stopping rules.
* **Cryptographic Audit Ledger**: Every agent diagnosis, intervention, and stopping rule execution is hashed and chained into an immutable append-only ledger (`SHA-256(prev_hash + incident_id + event + details)`), satisfying RBI digital lending and recovery audit compliance.

---

## 5. Technology Stack

* **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (Async), SQLite WAL Mode (with PostgreSQL compatibility via `asyncpg`).
* **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons.
* **Messaging Channel**: Telegram Bot API (`python-telegram-bot` / long-polling HTTP client via `httpx`).
* **Payment Gateway**: Official `razorpay` Python SDK.

---

## 6. Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/                     # Bounded Recovery Agents
│   │   │   ├── base_agent.py           # Base abstract lifecycle & audit logging
│   │   │   ├── upi_dropoff_agent.py    # Track 2: In-flight UPI drop-off handler
│   │   │   ├── ptp_agent.py            # Track 6: Promise-to-Pay restructurer
│   │   │   ├── b2b_dispute_agent.py    # Track 3: B2B TDS/GST micro-disputes
│   │   │   ├── mandate_healer_agent.py # Track 1: UPI Autopay & e-NACH healer
│   │   │   └── cross_border_agent.py   # Track 4: Cross-border decline translator
│   │   ├── api/v1/
│   │   │   ├── recovery.py             # Metrics, incident feed, simulation, reset
│   │   │   └── webhooks.py             # Razorpay webhook ingress & HMAC verification
│   │   ├── core/
│   │   │   └── database.py             # Async SQLAlchemy engine with WAL mode
│   │   ├── models/
│   │   │   └── recovery.py             # Incident, AuditLog, and BankHealth schemas
│   │   ├── services/
│   │   │   ├── razorpay_service.py     # Real Razorpay API client wrapper
│   │   │   ├── telegram_service.py     # HTML recovery cards & inline button dispatcher
│   │   │   ├── telegram_listener.py    # Async long-polling receiver for button clicks
│   │   │   ├── bank_health_service.py  # NPCI issuer bank health telemetry
│   │   │   └── simulation_service.py   # Deterministic multi-track batch generator
│   │   ├── config.py                   # Pydantic BaseSettings environment loader
│   │   └── main.py                     # FastAPI application entrypoint
│   └── tests/
│       └── test_recovery.py            # Pytest test suite
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx              # System badges, Live Sync toggle, reset button
│   │   │   ├── FinancialTicker.tsx     # At-Risk, Won-Back, Yield %, ROI metrics
│   │   │   ├── BankTelemetryBar.tsx    # Live Indian bank health metrics
│   │   │   ├── AgentLanes.tsx          # The 5 Bounded Agent command cards
│   │   │   ├── LiveIncidentFeed.tsx    # Filterable incident ledger & drawer inspector
│   │   │   ├── AuditModal.tsx          # SHA-256 cryptographic compliance inspector
│   │   │   └── QRModal.tsx             # Mobile phone Telegram pairing modal
│   │   ├── App.tsx                     # Main dashboard layout coordinator
│   │   ├── types.ts                    # Strict TypeScript data models
│   │   └── index.css                   # Custom natural cream styling & black shadows
│   └── package.json
├── infra/
│   ├── .env.example                    # Sample configuration template
│   └── docker-compose.yml              # Optional containerized deployment
├── run_demo.sh                         # Single-command launcher for backend & frontend
└── LICENSE                             # MIT License
```

---

## 7. Getting Started

### Prerequisites

* Python 3.10+
* Node.js 18+ and `npm`
* Razorpay Test Account credentials ([dashboard.razorpay.com](https://dashboard.razorpay.com))
* Telegram Account (for live mobile phone testing)

### Quick Start (Single Command)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/razorloop.git
   cd razorloop
   ```

2. **Configure environment variables**:
   ```bash
   cp infra/.env.example infra/.env
   ```
   Edit `infra/.env` with your Razorpay Test API keys (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`) and your Telegram Bot Token (`TELEGRAM_BOT_TOKEN`).

3. **Install dependencies**:
   ```bash
   # Python backend
   python3 -m venv razorpay_env
   source razorpay_env/bin/activate
   pip install -r backend/requirements.txt  # or: pip install fastapi uvicorn httpx pydantic sqlalchemy aiosqlite razorpay

   # Frontend
   npm --prefix frontend install
   ```

4. **Run both services**:
   ```bash
   chmod +x run_demo.sh
   ./run_demo.sh
   ```

* Dashboard UI: [http://localhost:5173](http://localhost:5173)
* Backend API & Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 8. Testing & Demo Workflow

### 1. Fresh Start
Click **"Reset Ledger"** in the top navigation bar. This invokes `POST /api/v1/recovery/reset` to wipe historical SQLite records, returning all counters to ₹0.

### 2. Batch Injection (Synthetic Load)
Click **"Inject Batch (25 Cases)"**. The simulator distributes 25 distinct transactions across all 5 recovery tracks with guaranteed unique consumer and company names, computing:
* **Recovery Yield**: Typically converts **55%–65%** of at-risk funds.
* **Net Recovery ROI**: Yields **4,000x+** compared to baseline communication overhead (calculated at ₹2.50 per notification).

### 3. Live Mobile Phone Test
1. Click **"Connect Mobile"** to reveal the Telegram pairing QR code.
2. Open Telegram, search `@razor_loop_bot`, and tap `/start`.
3. Click any of the 5 **"Trigger Demo"** buttons on the dashboard:
   * **In-Flight UPI**: Dispatches an instant reassurance card confirming ₹0 debited with a live Razorpay checkout link.
   * **PTP Demo**: Dispatches a 2-tranche restructuring card with a 15-day dunning pause.
   * **B2B Dispute**: Reconciles a 2% TDS dispute and provisions a Net Smart Collect Virtual Account.
   * **Mandate Healer**: Reschedules an e-NACH/Autopay debit notice to `06:30 AM`.
   * **Cross-Border**: Translates an ISO-8583 decline into 1-tap HDFC/ICICI app guidance.
4. Interact directly on your phone: clicking *"Complete via Razorpay"* opens the gateway, while clicking *"Cancel Order"* immediately invokes the agent's stopping rule.

### 4. Regulatory Audit Verification
Click **"Audit Chain"** to inspect the append-only SHA-256 hash chain verifying that every recovery action adhered to RBI and NPCI guidelines.

---

## 9. API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/v1/recovery/metrics` | `GET` | Aggregated financial metrics (At-Risk, Won-Back, Yield %, ROI). |
| `/api/v1/recovery/incidents` | `GET` | Filterable stream of recovery transactions (masked chat IDs). |
| `/api/v1/recovery/simulate` | `POST` | Trigger a single live at-risk incident with Telegram dispatch. |
| `/api/v1/recovery/batch-simulate` | `POST` | Inject a batch of $N$ diverse cases with guaranteed unique names. |
| `/api/v1/recovery/bank-telemetry` | `GET` | Core banking success rates for HDFC, SBI, ICICI, and Axis. |
| `/api/v1/recovery/audit-logs` | `GET` | Cryptographic SHA-256 audit ledger entries. |
| `/api/v1/recovery/reset` | `POST` | Wipe SQLite cache to return ledger to a clean starting state. |
| `/api/v1/webhooks/razorpay` | `POST` | Razorpay webhook ingress with HMAC-SHA256 signature verification. |

---

## 10. Security & Privacy Safeguards

* **No Credentials in Frontend**: Razorpay API secrets and bot tokens are strictly isolated in `infra/.env` and consumed server-side.
* **PII & Chat ID Masking**: Telegram chat IDs and customer phone numbers are masked across all public API serialization (`6*******4` and `+91 98****3210`).
* **Non-Coercive Recovery**: All agents enforce customer opt-out mechanisms with zero retry spam after debt satisfaction or explicit cancellation.

---

## 11. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
