# RazorLoop

> **Autonomous, Bounded Revenue Recovery Engine Built on Razorpay Rails**  
> *Track 03: AI Revenue Recovery — Razorpay Buildathon*

---

## Overview

In modern payment engineering, revenue leakage is rarely caused by simple, permanent declines. It is almost always a procedural breakdown:

* An operating system terminates a mobile browser during a UPI app-switch, leaving the customer uncertain whether their account was debited.
* An annual enterprise subscriber reaches a temporary card limit and gets immediately cut off by rigid billing software.
* An enterprise Accounts Payable team withholds 2% TDS under Section 194C on a ₹50,000 invoice, triggering aggressive automated dunning against the client's finance department.
* Recurring UPI Autopay / e-NACH charges fire blindly during scheduled core banking maintenance windows, causing bank rejection penalties and mandate revocations.
* International cardholders purchasing in India face declines under RBI international e-commerce mandates, receiving only an opaque `ISO-8583 57` code.

Standard recovery solutions rely on blunt cron retries and repetitive emails. On regulated Indian payment rails, blind retries fail: they breach bank rate limits, trigger penalty fees, and damage customer trust.

**RazorLoop** is an event-driven, autonomous recovery engine designed to bridge the gap between gateway telemetry, issuing bank health, and context-aware interventions—governed by strict, deterministic **stopping rules**.

---

## Core Architecture: The Tri-State Protocol

Every recovery workflow in RazorLoop follows a bounded, three-stage lifecycle:

```
┌─────────────────────────┐       ┌───────────────────────────────┐       ┌─────────────────────────────┐
│       1. DIAGNOSE       │ ────> │     2. BOUNDED INTERVENE      │ ────> │    3. HARD STOPPING RULE    │
└─────────────────────────┘       └───────────────────────────────┘       └─────────────────────────────┘
  • Gateway error inspection        • Dynamic Razorpay Checkout             • payment.captured webhook
  • NPCI bank health telemetry      • Smart Collect Net Virtual Account     • User cancellation / opt-out
  • TDS variance calculation        • Rescheduled 24-hr mandate notice      • Dispute threshold escalation
```

1. **Diagnosis**: Upon detecting a failure, the engine evaluates gateway error codes, issuer switch health, and transaction metadata to establish root cause before executing any outreach.
2. **Bounded Intervention**: The appropriate autonomous agent executes a single, proportionate recovery action: generating dynamic checkout links, structuring multi-tranche milestone agreements, or provisioning net settlement accounts.
3. **Hard Stopping Rule**: All communication and automated retries terminate immediately when debt is satisfied (`payment.captured`), when the user explicitly cancels, or when policy ceilings are reached.

---

## The 5 Specialized Recovery Agents

| # | Agent | Failure Mode | Intervention Strategy | Stopping Rule |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **In-Flight UPI Drop-off Reassurer** | Mobile app-switch drop-off; buyer abandons session fearing duplicate charge. | Verifies ₹0 debit with issuer core; sends instant reassurance message with 15-minute cart lock and checkout link. | Halts instantly on payment capture or user cancellation. |
| **2** | **Promise-to-Pay (PTP) Negotiator** | Annual renewal failure due to temporary liquidity or card limit constraints. | Proactively offers a 2-tranche structured milestone settlement (50% today, 50% in 15 days) and pauses dunning. | Capturing Tranche 1 payment suppresses all automated dunning. |
| **3** | **B2B TDS / GST Dispute Chaser** | Enterprise AP withholds 2% statutory TDS (Section 194C/194J); invoice remains unpaid. | Validates tax deduction percentage ($\le 5\%$); automatically generates a Net Smart Collect Virtual Account and draft Credit Note. | Variances $> 5\%$ halt automation and route an escalation memo to the CFO. |
| **4** | **Mandate Degradation Healer** | Recurring UPI Autopay / e-NACH execution during bank downtime (e.g., SBI 8 PM–11 PM). | Cross-references issuer health telemetry; reschedules 24-hour pre-debit notification to 06:30 AM outside downtime. | Limits retries to maximum 3 compliant attempts; avoids mandate revocation. |
| **5** | **Cross-Border Decline Translator** | International card decline under RBI default-off international e-commerce mandate. | Identifies issuing bank (HDFC, ICICI, SBI, Axis); sends 1-tap card toggle instructions with multi-currency checkout options. | Halts upon 3DS2 re-authentication or alternative rail selection. |

---

## OmniRoute Multi-Model AI Layer

RazorLoop integrates with an **OmniRoute** gateway to bring real-time intelligence to recovery operations:

* **Real-time Incident Synthesis**: An AI Executive Debrief engine analyzes active ledger sessions to extract systemic gateway failure trends, bank downtime correlations, and revenue impact.
* **Dynamic Model Routing**: Supports seamless runtime model switching across `github/gpt-4o-mini`, `anthropic/claude-3.5-sonnet`, `meta/llama-3.3-70b`, and `google/gemini-2.0-flash`.
* **Context-Aware Telegram Support Copilot**: Customers can message the Telegram recovery bot directly. The AI copilot maintains awareness of the incident's live status, payment reference IDs, and failure reasons, answering questions accurately and reassuring users once payment is confirmed.

---

## Razorpay Platform Integrations

* **Razorpay Orders & Standard Checkout**: Creates dedicated orders (`client.order.create`) with metadata tagging, rendering the responsive Razorpay Checkout modal for customer completion.
* **Razorpay Smart Collect Virtual Accounts**: Automatically provisions virtual accounts (UPI ID + NEFT/IFSC) for B2B net settlements, enabling reconciliation of tax-disputed invoices.
* **Webhook Signature Verification**: Validates incoming events using HMAC-SHA256 with `X-Razorpay-Signature` against `RAZORPAY_WEBHOOK_SECRET` for instant payment confirmation.
* **Cryptographic Compliance Ledger**: Every agent diagnosis, intervention, and stopping rule trigger is hashed into an append-only SHA-256 audit chain (`SHA-256(prev_hash + incident_id + event + details)`), satisfying RBI digital lending and recovery audit guidelines.

---

## System Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │           React + Vite Dashboard             │
                               │  Financial Ticker • Incident Feed • Debrief  │
                               └──────────────────────┬───────────────────────┘
                                                      │ HTTP / WebSocket
                                                      ▼
┌─────────────────────────┐    ┌──────────────────────────────────────────────┐    ┌─────────────────────────┐
│     Telegram API        │<──>│               FastAPI Backend                │<──>│    OmniRoute Gateway    │
│  Interactive Cards      │    │  • Recovery Engine   • Checkout Renderer     │    │  • Model Routing        │
│  2-Way AI Copilot       │    │  • Webhook Ingress   • Bank Telemetry Feed   │    │  • Executive Debrief    │
└─────────────────────────┘    └──────────────────────┬───────────────────────┘    └─────────────────────────┘
                                                      │
                         ┌────────────────────────────┴────────────────────────────┐
                         ▼                                                         ▼
         ┌───────────────────────────────┐                         ┌───────────────────────────────┐
         │     Razorpay Platform         │                         │    SQLite (Async WAL Mode)    │
         │  Orders • Virtual Accounts    │                         │  Incidents • Audit Hash Chain │
         │  Standard Checkout • Webhooks │                         │  Bank Health Cache            │
         └───────────────────────────────┘                         └───────────────────────────────┘
```

---

## Repository Structure

```
Razorpay_Buildathon/
├── backend/
│   ├── app/
│   │   ├── agents/                     # Recovery Agents
│   │   │   ├── base_agent.py           # Abstract agent lifecycle and audit logger
│   │   │   ├── upi_dropoff_agent.py    # Track 1: In-flight UPI drop-off handler
│   │   │   ├── ptp_agent.py            # Track 2: Promise-to-Pay restructurer
│   │   │   ├── b2b_dispute_agent.py    # Track 3: B2B TDS/GST dispute reconciler
│   │   │   ├── mandate_healer_agent.py # Track 4: Mandate degradation healer
│   │   │   └── cross_border_agent.py   # Track 5: Cross-border decline translator
│   │   ├── api/v1/
│   │   │   ├── recovery.py             # Metrics, incident feed, simulation, reset
│   │   │   ├── checkout.py             # Standard Razorpay checkout renderer & quick-pay
│   │   │   └── webhooks.py             # Razorpay webhook listener & signature verifier
│   │   ├── core/
│   │   │   └── database.py             # Async SQLAlchemy engine with SQLite WAL
│   │   ├── models/
│   │   │   └── recovery.py             # Incident, AuditLog, and BankHealth schemas
│   │   ├── services/
│   │   │   ├── razorpay_service.py     # Razorpay API client wrapper
│   │   │   ├── omniroute_ai_service.py # Multi-model gateway & Telegram copilot
│   │   │   ├── telegram_service.py     # Telegram message and inline keyboard builder
│   │   │   ├── telegram_listener.py    # Long-polling listener for interactive buttons & chat
│   │   │   ├── bank_health_service.py  # Issuer bank telemetry provider
│   │   │   └── simulation_service.py   # Multi-track incident generator
│   │   ├── config.py                   # Environment configuration loader
│   │   └── main.py                     # FastAPI application entrypoint & static mount
│   └── requirements.txt                # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx              # Navigation, batch injection, reset controls
│   │   │   ├── FinancialTicker.tsx     # At-Risk, Recovered, Yield %, and ROI metrics
│   │   │   ├── BankTelemetryBar.tsx    # Live issuer health metrics (HDFC, SBI, ICICI, Axis)
│   │   │   ├── AgentLanes.tsx          # Interactive agent demo trigger cards
│   │   │   ├── LiveIncidentFeed.tsx    # Filterable ledger feed & incident drawer
│   │   │   ├── AIDebriefModal.tsx      # Multi-model executive debrief modal
│   │   │   ├── AuditModal.tsx          # SHA-256 cryptographic compliance inspector
│   │   │   └── QRModal.tsx             # Telegram mobile pairing modal
│   │   ├── App.tsx                     # Dashboard state management
│   │   ├── types.ts                    # TypeScript interface definitions
│   │   └── index.css                   # Custom theme and styling
│   ├── package.json
│   └── vite.config.ts
├── infra/
│   ├── .env.example                    # Environment template
│   └── docker-compose.yml              # Containerized deployment definition
├── run_demo.sh                         # Unified startup script
└── LICENSE                             # MIT License
```

---

## Technology Stack

* **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (Async), SQLite with Write-Ahead Logging (WAL Mode), `httpx`, `pydantic-settings`.
* **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons.
* **Payments Engine**: Official `razorpay` Python SDK, Razorpay Standard Checkout JS.
* **OmniRoute AI Gateway**: OpenAI-compatible routing interface with runtime model selection.
* **Customer Messaging**: Telegram Bot API with interactive inline keyboards and long-polling event loop.

---

## Getting Started

### Prerequisites

* Python 3.10+
* Node.js 18+ and `npm`
* A Razorpay Test Account ([dashboard.razorpay.com](https://dashboard.razorpay.com))
* A Telegram Bot token (from `@BotFather`)

### 1. Clone & Configure

```bash
git clone https://github.com/<your-username>/Razorpay_Buildathon.git
cd Razorpay_Buildathon

# Copy configuration template
cp infra/.env.example infra/.env
```

Edit `infra/.env` with your API credentials:

```ini
RAZORPAY_KEY_ID="rzp_test_yourKeyHere"
RAZORPAY_KEY_SECRET="yourSecretHere"
RAZORPAY_WEBHOOK_SECRET="whsec_yourSecretHere"

TELEGRAM_BOT_TOKEN="your_bot_token"
TELEGRAM_DEMO_CHAT_ID="your_telegram_chat_id"

# Optional OmniRoute / LLM configuration
OMNIROUTE_BASE_URL="http://127.0.0.1:20128/v1"
OMNIROUTE_API_KEY="your_omniroute_key"
OMNIROUTE_MODEL="github/gpt-4o-mini"

# Local network IP for mobile testing
APP_HOST_URL="http://localhost:8000"
```

### 2. Install Dependencies

```bash
# Python backend
python3 -m venv razorpay_env
source razorpay_env/bin/activate
pip install -r backend/requirements.txt

# Frontend
npm --prefix frontend install
```

### 3. Run Application

You can launch both services using the included startup script:

```bash
chmod +x run_demo.sh
./run_demo.sh
```

Or run them individually:

```bash
# Terminal 1: Backend
source razorpay_env/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
npm --prefix frontend run dev
```

* **Dashboard**: [http://localhost:5173](http://localhost:5173) (or [http://localhost:8000](http://localhost:8000))
* **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Demo & Verification Workflow

### 1. Reset Ledger
Click **"Reset Ledger"** in the top navigation bar. This invokes `POST /api/v1/recovery/reset` to wipe test records and return all financial metrics to baseline.

### 2. Batch Injection (Synthetic Load)
Click **"Inject Batch (20 Cases)"**. The simulator generates 20 realistic payment drop-offs and disputes across all 5 tracks with guaranteed unique customer names:
* **Recovery Yield**: Evaluates portfolio recovery percentage (typically 55%–70%).
* **Net Recovery ROI**: Computes net recovered funds relative to communication cost (estimated at ₹2.50 per notification).

### 3. Live Mobile Phone Test
1. Click **"Connect Mobile"** on the dashboard to view your Telegram pairing instructions.
2. Start the bot on Telegram (`/start`).
3. Click any **"Trigger Demo"** button on the dashboard:
   * **In-Flight UPI**: Dispatches a card verifying ₹0 debited with a quick checkout link.
   * **PTP Demo**: Offers a 2-tranche restructuring card with a 15-day dunning pause.
   * **B2B Dispute**: Reconciles a 2% TDS variance and generates a Net Smart Collect Virtual Account.
   * **Mandate Healer**: Reschedules an Autopay debit to 06:30 AM outside bank maintenance windows.
   * **Cross-Border**: Delivers 1-tap international e-commerce activation instructions for HDFC/ICICI/SBI cards.
4. Tap **[ Complete Card Checkout ]** on Telegram: it opens the checkout page in your browser.
5. Complete the payment using standard test credentials. The system updates the Telegram card to **"Payment Captured (Confirmed)"**, terminates further dunning, and returns to the dashboard.

### 4. Conversational AI Copilot Test
Send a message to your Telegram bot (e.g., *"Did my payment go through?"* or *"Why did my card get declined?"*). The AI copilot reads the live incident record and provides an accurate, context-grounded response.

### 5. Regulatory Audit Verification
Click **"Audit Chain"** to inspect the append-only SHA-256 cryptographic audit trail verifying that every action complied with regulatory constraints.

---

## API Reference

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/api/v1/recovery/metrics` | Financial metrics (At-Risk, Recovered, Recovery Yield, Net ROI). |
| `GET` | `/api/v1/recovery/incidents` | Filterable list of recovery incidents with masked PII. |
| `POST` | `/api/v1/recovery/simulate` | Trigger a single live recovery incident with Telegram dispatch. |
| `POST` | `/api/v1/recovery/batch-simulate` | Inject a batch of $N$ diverse cases across all 5 tracks. |
| `POST` | `/api/v1/recovery/simulate-payment` | Manually capture and resolve an incident to test stopping rules. |
| `GET` | `/api/v1/recovery/bank-telemetry` | Current core banking health for HDFC, SBI, ICICI, and Axis. |
| `GET` | `/api/v1/recovery/audit-logs` | Cryptographic SHA-256 audit ledger entries. |
| `POST` | `/api/v1/recovery/ai-executive-debrief` | Generate an AI summary and systemic analysis using OmniRoute. |
| `POST` | `/api/v1/recovery/reset` | Reset the ledger to a clean starting state. |
| `POST` | `/api/v1/webhooks/razorpay` | Razorpay webhook ingress with HMAC-SHA256 verification. |

---

## Security & Compliance Safeguards

* **Isolated Credentials**: All API keys, secrets, and bot tokens reside in server-side environment variables and are never bundled with frontend client assets.
* **PII Masking**: Customer contact details and Telegram chat IDs are masked across API responses (`6*******4` and `+91 98****3210`).
* **Non-Coercive Outreach**: Communications respect customer cancellation signals, enforce dunning pauses, and cease outreach upon payment confirmation.
* **Cryptographic Tamper-Evidence**: Incident audit logs are linked using SHA-256 hashing to preserve a verifiable record of automated actions.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
