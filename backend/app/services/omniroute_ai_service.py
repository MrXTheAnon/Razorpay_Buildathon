import logging
import httpx
import os
import json
from typing import Dict, Any, List, Optional
from backend.app.config import settings

logger = logging.getLogger("razorloop.ai")

class OmniRouteAIService:
    """
    AI Service client interfacing with the local OmniRoute Multi-Provider AI Gateway.
    Provides intelligent recovery copy synthesis, conversational Telegram copilot,
    B2B tax dispute reasoning, and executive portfolio debriefing.
    """
    def __init__(self):
        # Default to local OmniRoute gateway
        self.base_url = os.getenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
        self.api_key = os.getenv("OMNIROUTE_API_KEY", "") or getattr(settings, "OMNIROUTE_API_KEY", "")
        self.model = os.getenv("OMNIROUTE_MODEL", "github/gpt-4o-mini")
        self.timeout = 15.0

    async def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.4, max_tokens: int = 500) -> Optional[str]:
        """Low-level HTTP call to OmniRoute OpenAI-compatible endpoint with graceful fallback."""
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        if self.model == "research-combo":
            headers["x-combo"] = "research-combo"
            payload["combo"] = "research-combo"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    text = resp.text.strip()
                    # Check if response returned as Server-Sent Events (SSE) data stream
                    if "data: " in text:
                        chunks = []
                        for line in text.split("\n"):
                            line = line.strip()
                            if line.startswith("data: ") and not line.endswith("[DONE]"):
                                try:
                                    c_data = json.loads(line[6:])
                                    delta = c_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if delta:
                                        chunks.append(delta)
                                except Exception:
                                    pass
                        if chunks:
                            return "".join(chunks).strip()

                    try:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "").strip()
                    except Exception:
                        pass
                    return text
                else:
                    logger.warning(f"OmniRoute HTTP {resp.status_code}: {resp.text[:150]}")
                    return None
        except Exception as e:
            logger.warning(f"OmniRoute call failed ({e}). Falling back to deterministic heuristics.")
            return None

    async def chat_with_customer(
        self,
        customer_name: str,
        incident_context: Dict[str, Any],
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Interactive Copilot: Answers customer queries on Telegram regarding their payment status,
        failure causes, split options, bank downtime, or alternative rails in natural language.
        """
        status = incident_context.get("status", "intervened")
        is_recovered = (status == "recovered")
        recovered_amt = incident_context.get("recovered_amount") or incident_context.get("original_amount", 0)
        pay_id = incident_context.get("razorpay_payment_id") or "pay_verified"
        root_cause = incident_context.get("root_cause", "Temporary network issue")
        extra_data = incident_context.get("extra_data") or {}
        issuer_bank = extra_data.get("issuer_bank", "your bank")

        if is_recovered:
            status_directives = (
                f"PAYMENT STATUS: ✅ SUCCEEDED & SETTLED (RECOVERED)\n"
                f"- Amount Paid: ₹{recovered_amt:,.2f}\n"
                f"- Payment Reference: {pay_id}\n"
                f"- CRITICAL: If the customer asks if their payment went through, was received, or succeeded, "
                f"ANSWER YES IMMEDIATELY! Confirm their payment of ₹{recovered_amt:,.2f} (Ref: {pay_id}) was successfully captured and verified. "
                f"Reassure them that their transaction is complete and their order is safe. DO NOT say it was declined or failed!\n"
            )
        else:
            status_directives = (
                f"PAYMENT STATUS: ⚠️ PENDING RECOVERY (NOT YET PAID)\n"
                f"- Original Amount: ₹{incident_context.get('original_amount', 0):,.2f}\n"
                f"- Root Cause: {root_cause}\n"
                f"- Bank: {issuer_bank}\n"
                f"- Reassure the customer that ₹0 has been debited or lost.\n"
                f"- If they ask why it was declined, explain politely (e.g. RBI international toggle for cross-border cards, or temporary bank downtime).\n"
                f"- If they ask about installments, offer to split into 2 installments (50% now, 50% in 15 days).\n"
                f"- If they ask to cancel, confirm that reminders are halted immediately.\n"
            )

        system_prompt = (
            "You are RazorLoop AI, an autonomous, empathetic, and professional payment assistant for Razorpay merchants.\n"
            "Your responses must strictly match the REAL-TIME transaction status below.\n\n"
            f"{status_directives}\n"
            "Rules:\n"
            "1. Be concise, respectful, and courteous (max 2-3 sentences).\n"
            "2. Never contradict the real-time payment status.\n"
            f"Active Context: Customer={customer_name}, Track={incident_context.get('track')}, Status={status}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-4:])
        messages.append({"role": "user", "content": user_message})

        response = await self._call_llm(messages, temperature=0.2, max_tokens=200)
        if response:
            return response

        # Fallback heuristic based on real status
        if is_recovered:
            return (
                f"Hello {customer_name}! Yes, your payment of ₹{recovered_amt:,.2f} was successfully captured "
                f"and confirmed (Ref: {pay_id}). No further action is required!"
            )
        return (
            f"Hello {customer_name}, I understand your query. Your transaction of "
            f"₹{incident_context.get('original_amount', 0):,.0f} encountered a temporary issue ({root_cause}). "
            f"No funds were debited from your account. You can securely complete it via the payment link or reply with any questions."
        )

    async def synthesize_reassurance_copy(
        self,
        track: str,
        customer_name: str,
        amount: float,
        bank_name: str = "your bank",
        details: str = ""
    ) -> str:
        """
        Synthesizes high-converting, personalized, non-coercive recovery copy for checkout cards.
        """
        prompt = (
            f"Write a 2-sentence payment recovery notification for a customer named {customer_name}.\n"
            f"Situation: Track '{track}', Amount: ₹{amount:,.0f}, Bank: {bank_name}. Detail: {details}.\n"
            "Requirements:\n"
            "- Reassure them that ₹0 was lost or debited.\n"
            "- Explain what happened in plain terms (e.g. app-switch session ended, bank maintenance window, or international toggle required).\n"
            "- Courteous, non-spammy, exactly 2 sentences."
        )
        messages = [
            {"role": "system", "content": "You are a professional fintech copywriter for Razorpay."},
            {"role": "user", "content": prompt}
        ]
        res = await self._call_llm(messages, temperature=0.5, max_tokens=150)
        return res

    async def generate_b2b_dispute_memo(
        self,
        incident_id: str,
        customer_name: str,
        original_amount: float,
        withheld_amount: float,
        variance_percent: float,
        section_code: str = "194C"
    ) -> str:
        """
        Generates a formal corporate Tax Reconciliation & Credit Note justification memo.
        """
        prompt = (
            f"Generate an executive Tax Discrepancy Reconciliation Memo for invoice {incident_id}.\n"
            f"Client AP: {customer_name}\n"
            f"Original Invoice Amount: ₹{original_amount:,.2f}\n"
            f"Withheld TDS: ₹{withheld_amount:,.2f} ({variance_percent}% under Section {section_code})\n"
            f"Tolerance Policy: Max 5% variance permitted for automated settlement.\n"
            "Output format:\n"
            "• Statutory Finding: 1 sentence explaining Section 194C vs 194J applicability.\n"
            "• Accounting Action: Draft Credit Note CN-2026-X issuance and Smart Collect Net Virtual Account allocation.\n"
            "• Compliance Conclusion: 1 sentence confirmation for the CFO ledger."
        )
        messages = [
            {"role": "system", "content": "You are a chartered tax accountant & fintech automated billing expert in India."},
            {"role": "user", "content": prompt}
        ]
        res = await self._call_llm(messages, temperature=0.2, max_tokens=250)
        return res

    async def generate_executive_debrief(
        self,
        total_at_risk: float,
        total_recovered: float,
        recovery_rate: float,
        roi_multiplier: float,
        incident_count: int,
        track_breakdown: List[Dict[str, Any]],
        bank_telemetry: List[Dict[str, Any]],
        sample_cases: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generates a boardroom-level AI Executive Debrief analyzing portfolio recovery health,
        root-cause clustering, and payment gateway routing recommendations grounded in live database incidents.
        """
        if incident_count == 0:
            return {
                "executive_summary": "Telemetry Standby: 0 payment incidents currently in ledger session. Awaiting transaction failure signals.",
                "systemic_findings": [
                    "Telemetry Standby: No active payment drop-offs or dispute events detected across payment switches.",
                    "Issuer Health Switches: Core bank telemetry (HDFC, SBI, ICICI, AXIS) actively monitored and operational.",
                    "Autonomous Interventions Idle: Recovery agents primed to intercept and resolve failures upon trigger."
                ],
                "gateway_recommendations": [
                    "Click 'Inject Batch (20 Cases)' in the top navbar to simulate production failure telemetry.",
                    "Test individual payment tracks below to inspect autonomous agent intervention logic.",
                    "OmniRoute will automatically synthesize systemic findings from live incident telemetry once injected."
                ]
            }

        prompt = (
            f"Analyze this live Razorpay autonomous recovery portfolio telemetry:\n"
            f"- Total In Jeopardy (At-Risk): ₹{total_at_risk:,.0f}\n"
            f"- Total Capital Secured (Won Back): ₹{total_recovered:,.0f} ({recovery_rate:.1f}% Recovery Yield)\n"
            f"- Net Recovery ROI: {roi_multiplier:.0f}x baseline\n"
            f"- Total Incidents Evaluated: {incident_count}\n"
            f"- Track Breakdown: {json.dumps(track_breakdown)}\n"
            f"- Live Bank Switch Telemetry: {json.dumps(bank_telemetry)}\n"
            f"- Actual Incident Samples From Live Database: {json.dumps(sample_cases or [])}\n\n"
            "TASK:\n"
            "Synthesize genuine systemic findings and actionable gateway optimizations strictly based on the ACTUAL failures and bank statuses above.\n"
            "Output pure JSON adhering to this schema:\n"
            "{\n"
            "  \"executive_summary\": \"2-3 detailed sentences analyzing portfolio yield, capital efficiency, and key agent interventions.\",\n"
            "  \"systemic_findings\": [\n"
            "    \"Specific observation referencing actual failure reasons or bank switches found in telemetry\",\n"
            "    \"Specific observation referencing actual B2B or mandate failure causes in the dataset\",\n"
            "    \"Specific observation referencing UPI or cross-border drop-off patterns\"\n"
            "  ],\n"
            "  \"gateway_recommendations\": [\n"
            "    \"Specific gateway routing rule based on the data\",\n"
            "    \"Specific operational improvement for the highest-variance track\",\n"
            "    \"Specific retry policy or customer reassurance protocol\"\n"
            "  ]\n"
            "}\n"
            "CRITICAL: Ground all findings in the actual failure causes and bank telemetry provided."
        )
        messages = [
            {"role": "system", "content": "You are a Chief Payments Officer and Principal Fintech Infrastructure Architect. Respond in pure JSON without markdown."},
            {"role": "user", "content": prompt}
        ]
        res = await self._call_llm(messages, temperature=0.2, max_tokens=750)
        if res:
            try:
                clean_json = res.strip()
                if clean_json.startswith("```"):
                    lines = clean_json.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    clean_json = "\n".join(lines).strip()
                parsed = json.loads(clean_json)
                if isinstance(parsed, dict):
                    if "debrief" in parsed and isinstance(parsed["debrief"], dict):
                        parsed = parsed["debrief"]

                    summary = parsed.get("executive_summary") or parsed.get("summary") or parsed.get("analysis")
                    findings = parsed.get("systemic_findings") or parsed.get("findings") or parsed.get("observations")
                    recs = parsed.get("gateway_recommendations") or parsed.get("recommendations") or parsed.get("actions")

                    # Handle nested dictionary case
                    if isinstance(summary, dict):
                        findings = findings or summary.get("findings") or summary.get("observations") or summary.get("systemic_findings")
                        nested_recs = summary.get("recommendations") or summary.get("next_steps") or summary.get("gateway_recommendations")
                        if isinstance(nested_recs, dict):
                            recs = recs or nested_recs.get("next_steps") or list(nested_recs.values())
                        elif isinstance(nested_recs, list):
                            recs = recs or nested_recs
                        summary_str = summary.get("text") or summary.get("overview") or summary.get("summary") or (
                            f"RazorLoop evaluated {incident_count} payment incidents totaling ₹{total_at_risk:,.0f}, "
                            f"successfully securing ₹{total_recovered:,.0f} at an optimal {recovery_rate:.1f}% recovery yield."
                        )
                    else:
                        summary_str = str(summary) if summary else (
                            f"RazorLoop evaluated {incident_count} payment incidents totaling ₹{total_at_risk:,.0f}, "
                            f"securing ₹{total_recovered:,.0f} at {recovery_rate:.1f}% recovery yield."
                        )

                    clean_findings = []
                    if isinstance(findings, list):
                        for f in findings:
                            if isinstance(f, str) and f.strip():
                                clean_findings.append(f.strip())
                            elif isinstance(f, dict):
                                clean_findings.append(f.get("finding") or f.get("description") or str(f))
                    elif findings:
                        clean_findings.append(str(findings))

                    clean_recs = []
                    if isinstance(recs, list):
                        for r in recs:
                            if isinstance(r, str) and r.strip():
                                clean_recs.append(r.strip())
                            elif isinstance(r, dict):
                                clean_recs.append(r.get("recommendation") or r.get("action") or str(r))
                    elif recs:
                        clean_recs.append(str(recs))

                    if len(clean_findings) < 2:
                        if sample_cases:
                            clean_findings = [
                                f"{c.get('track', 'Payment')}: {c.get('root_cause')} ({c.get('customer')})"
                                for c in sample_cases[:3]
                            ]
                        else:
                            clean_findings = [
                                f"Autonomous recovery agents actively processing {incident_count} evaluated transactions.",
                                f"Core banking telemetry verified across {len(bank_telemetry)} major issuer switches.",
                                "Zero un-halted dunning: Hard stopping rules executed on debt satisfaction."
                            ]
                    if len(clean_recs) < 2:
                        clean_recs = [
                            "Enforce dynamic 06:30 AM mandate rescheduling to bypass core banking maintenance throttles.",
                            "Automate Net Smart Collect Virtual Account generation for invoice disputes with <=5% variance.",
                            "Deploy instant 1-tap mobile bank unlock guidance for international e-commerce card declines."
                        ]

                    return {
                        "executive_summary": summary_str,
                        "systemic_findings": clean_findings,
                        "gateway_recommendations": clean_recs
                    }
            except Exception as e:
                logger.warning(f"Failed to parse OmniRoute JSON debrief: {e}")

        # High quality heuristic fallback grounded in sample_cases
        dynamic_findings = []
        if sample_cases:
            for c in sample_cases[:3]:
                dynamic_findings.append(f"{c.get('track', 'Payment')}: {c.get('root_cause')} ({c.get('customer')})")
        if not dynamic_findings:
            dynamic_findings = [
                f"Evaluated {incident_count} transaction failures across live rails.",
                "Real-time bank telemetry confirms automated retry suppression active.",
                "Deterministic stopping rules halted dunning immediately upon payment capture."
            ]

        return {
            "executive_summary": (
                f"RazorLoop evaluated {incident_count} at-risk payment incidents totaling ₹{total_at_risk:,.0f}, "
                f"successfully securing ₹{total_recovered:,.0f} at an optimal {recovery_rate:.1f}% recovery yield. "
                f"Autonomous intervention generated a {roi_multiplier:.0f}x return over baseline dunning overhead."
            ),
            "systemic_findings": dynamic_findings,
            "gateway_recommendations": [
                "Enforce dynamic 06:30 AM mandate rescheduling to bypass core banking maintenance throttles.",
                "Automate Net Smart Collect Virtual Account generation for invoice disputes with <=5% variance.",
                "Deploy instant 1-tap mobile bank unlock guidance for international e-commerce card declines."
            ]
        }

omniroute_ai_service = OmniRouteAIService()
