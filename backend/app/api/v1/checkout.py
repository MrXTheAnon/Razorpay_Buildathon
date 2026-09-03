from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.recovery import RecoveryIncident

router = APIRouter(tags=["Mock Checkout"])

@router.get("/pay/{incident_id}", response_class=HTMLResponse)
async def mock_razorpay_checkout(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Render an authentic Razorpay mock checkout page for reliable live demo presentations."""
    res = await db.execute(select(RecoveryIncident).where(RecoveryIncident.id == incident_id))
    inc = res.scalars().first()

    customer_name = inc.customer_name if inc else "Customer"
    amount = inc.original_amount if inc else 5499.0
    status = inc.status if inc else "intervened"
    track = inc.track if inc else "cross_border"
    track_title = track.replace("_", " ").title()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Razorpay Standard Checkout — RazorLoop</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: 'Inter', sans-serif; }}
    .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
  </style>
</head>
<body class="bg-[#0c1322] min-h-screen flex items-center justify-center p-4">
  <div class="w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-200">
    <!-- Razorpay Header -->
    <div class="bg-[#0c2340] px-6 py-4 flex items-center justify-between text-white border-b border-slate-800">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white text-sm tracking-tighter">
          R
        </div>
        <div>
          <div class="text-sm font-semibold tracking-tight">RazorLoop Store</div>
          <div class="text-[11px] text-blue-200/80 font-mono">Order #{incident_id}</div>
        </div>
      </div>
      <div class="text-right">
        <span class="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
          TEST MODE
        </span>
      </div>
    </div>

    <!-- Amount Banner -->
    <div class="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center justify-between">
      <div>
        <span class="text-xs text-slate-500 font-medium block">Amount to Pay</span>
        <span class="text-2xl font-bold text-slate-900 font-mono">₹{amount:,.2f}</span>
      </div>
      <div class="text-right">
        <span class="text-[11px] text-slate-500 block">Customer</span>
        <span class="text-xs font-semibold text-slate-800">{customer_name}</span>
      </div>
    </div>

    <!-- Payment Container -->
    <div id="checkout-view" class="p-6 space-y-4">
      <!-- Advisory pill -->
      <div class="p-3 bg-blue-50/80 border border-blue-200/80 rounded-xl text-xs text-blue-900 flex items-start gap-2">
        <span class="text-base">🛡️</span>
        <div>
          <span class="font-semibold block">{track_title} Recovery Channel</span>
          <span class="text-[11px] text-blue-800/90 leading-relaxed">
            Zero debit confirmed on your previous attempt. 3DS2 re-authentication will satisfy the debt and trigger the autonomous stopping rule.
          </span>
        </div>
      </div>

      <!-- Payment Method Selection -->
      <div class="space-y-2">
        <span class="text-xs font-semibold text-slate-700 block">Payment Method</span>
        
        <!-- Cards -->
        <label class="flex items-center justify-between p-3.5 border-2 border-blue-600 bg-blue-50/30 rounded-xl cursor-pointer">
          <div class="flex items-center gap-3">
            <input type="radio" name="payment_method" value="card" checked class="text-blue-600 focus:ring-blue-500">
            <div>
              <span class="text-xs font-semibold text-slate-900 block">Cards (Credit / Debit)</span>
              <span class="text-[11px] text-slate-500">Visa, Mastercard, RuPay</span>
            </div>
          </div>
          <div class="flex gap-1">
            <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 bg-white border border-slate-200 rounded text-slate-700">VISA</span>
            <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 bg-white border border-slate-200 rounded text-slate-700">MC</span>
          </div>
        </label>

        <!-- Card Mock Input Details -->
        <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5">
          <div>
            <label class="text-[10px] font-mono text-slate-500 uppercase font-semibold block mb-1">Card Number</label>
            <div class="px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 font-medium">
              •••• •••• •••• 4242
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="text-[10px] font-mono text-slate-500 uppercase font-semibold block mb-1">Valid Thru</label>
              <div class="px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 font-medium">
                12 / 28
              </div>
            </div>
            <div>
              <label class="text-[10px] font-mono text-slate-500 uppercase font-semibold block mb-1">CVV</label>
              <div class="px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 font-medium">
                •••
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Button -->
      <button
        id="pay-btn"
        onclick="executePayment()"
        class="w-full py-3.5 px-4 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-sm font-semibold rounded-xl transition shadow-lg shadow-blue-600/25 flex items-center justify-center gap-2 cursor-pointer"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
        </svg>
        <span id="btn-text">Pay ₹{amount:,.2f}</span>
      </button>

      <!-- Security footer -->
      <div class="text-center text-[11px] text-slate-400 flex items-center justify-center gap-1.5 pt-1">
        <span>🔒 256-Bit SSL Encrypted</span>
        <span>•</span>
        <span>Secured by Razorpay</span>
      </div>
    </div>

    <!-- Success State View (Hidden Initially) -->
    <div id="success-view" class="p-8 text-center space-y-4 hidden animate-in fade-in zoom-in-95 duration-300">
      <div class="w-16 h-16 bg-emerald-100 border-2 border-emerald-500 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20">
        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
        </svg>
      </div>

      <div>
        <h2 class="text-lg font-bold text-slate-900">Payment Successful!</h2>
        <p class="text-xs text-slate-600 mt-1">₹{amount:,.2f} securely captured on Razorpay Testnet</p>
      </div>

      <div class="p-4 bg-emerald-50/80 border border-emerald-200 rounded-xl text-left space-y-1.5 text-xs font-mono">
        <div class="flex justify-between text-slate-600">
          <span>Payment ID:</span>
          <span id="pay-id-display" class="font-bold text-slate-900">pay_sim_loading</span>
        </div>
        <div class="flex justify-between text-slate-600">
          <span>Order ID:</span>
          <span class="text-slate-900">{incident_id}</span>
        </div>
        <div class="pt-2 border-t border-emerald-200 text-emerald-950 font-sans text-[11px]">
          🛡️ <b>Stopping Rule Triggered:</b> Autonomous dunning terminated. Ledger reconciled in real time.
        </div>
      </div>

      <a
        href="/"
        class="inline-block w-full py-2.5 px-4 bg-slate-900 hover:bg-black text-white text-xs font-mono font-semibold rounded-xl transition"
      >
        Return to Dashboard
      </a>
    </div>
  </div>

  <script>
    async function executePayment() {{
      const btn = document.getElementById('pay-btn');
      const btnText = document.getElementById('btn-text');
      btn.disabled = true;
      btn.classList.add('opacity-80', 'cursor-wait');
      btnText.innerHTML = '<span class="inline-block animate-spin mr-2">↻</span> Authenticating 3DS2...';

      try {{
        const res = await fetch('/api/v1/recovery/simulate-payment', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{
            incident_id: '{incident_id}',
            amount: {amount}
          }})
        }});

        const data = await res.json();
        
        // Transition to success view
        setTimeout(() => {{
          document.getElementById('checkout-view').classList.add('hidden');
          document.getElementById('success-view').classList.remove('hidden');
          if (data.incident && data.incident.razorpay_payment_id) {{
            document.getElementById('pay-id-display').innerText = data.incident.razorpay_payment_id;
          }} else {{
            document.getElementById('pay-id-display').innerText = 'pay_sim_' + Math.random().toString(36).substring(2, 8);
          }}
        }}, 800);
      }} catch (err) {{
        console.error('Payment error:', err);
        btn.disabled = false;
        btn.classList.remove('opacity-80', 'cursor-wait');
        btnText.innerText = 'Pay ₹{amount:,.2f}';
        alert('Payment simulation failed: ' + err);
      }}
    }}
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
