import React from 'react';
import type { MetricSummary } from '../types';
import { AlertCircle, TrendingUp, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';

interface FinancialTickerProps {
  metrics: MetricSummary | null;
}

export const FinancialTicker: React.FC<FinancialTickerProps> = ({ metrics }) => {
  const atRisk = metrics?.total_at_risk_inr || 0;
  const recovered = metrics?.total_recovered_inr || 0;
  const rate = metrics?.recovery_rate_percent || 0;
  const roi = metrics?.roi_multiplier || 0;
  const incidents = metrics?.total_incidents || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4.5">
      {/* 1. At-Risk Revenue Card */}
      <div className="cream-raised rounded-2xl p-5 relative overflow-hidden transition-all duration-300 hover:translate-y-[-1px]">
        <div className="flex items-center justify-between text-stone-500 text-xs font-mono mb-2.5">
          <span className="flex items-center gap-2 text-amber-800 font-semibold tracking-wide">
            <span className="p-1 rounded-lg cream-well text-amber-700">
              <AlertCircle className="w-3.5 h-3.5" />
            </span>
            REVENUE AT-RISK
          </span>
          <span className="cream-pill px-2.5 py-0.5 rounded-full text-[11px] text-stone-700 font-mono font-medium">
            {incidents} cases
          </span>
        </div>

        <div className="text-3xl font-bold font-mono tracking-tight text-stone-900">
          ₹{atRisk.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
        </div>

        <div className="mt-3 flex items-center gap-2 text-[11px] font-sans text-stone-500">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          <span>In-flight drop-offs & procedurally stalled invoices</span>
        </div>
      </div>

      {/* 2. Successfully Recovered Card */}
      <div className="cream-raised rounded-2xl p-5 relative overflow-hidden transition-all duration-300 hover:translate-y-[-1px] border-emerald-200">
        <div className="flex items-center justify-between text-stone-500 text-xs font-mono mb-2.5">
          <span className="flex items-center gap-2 text-emerald-800 font-semibold tracking-wide">
            <span className="p-1 rounded-lg cream-well text-emerald-700">
              <CheckCircle2 className="w-3.5 h-3.5" />
            </span>
            WON-BACK REVENUE
          </span>
          <span className="cream-pill px-2.5 py-0.5 rounded-full text-[11px] text-emerald-800 font-mono font-bold bg-emerald-50 border-emerald-200">
            +{rate}%
          </span>
        </div>

        <div className="text-3xl font-bold font-mono tracking-tight text-emerald-700">
          ₹{recovered.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
        </div>

        <div className="mt-3 flex items-center gap-2 text-[11px] font-sans text-stone-500">
          <span className="w-2 h-2 rounded-full bg-emerald-600" />
          <span>Captured via Gateway & Net Smart Collect</span>
        </div>
      </div>

      {/* 3. Recovery Yield Card */}
      <div className="cream-raised rounded-2xl p-5 relative overflow-hidden transition-all duration-300 hover:translate-y-[-1px]">
        <div className="flex items-center justify-between text-stone-500 text-xs font-mono mb-2.5">
          <span className="flex items-center gap-2 text-sky-800 font-semibold tracking-wide">
            <span className="p-1 rounded-lg cream-well text-sky-700">
              <TrendingUp className="w-3.5 h-3.5" />
            </span>
            RECOVERY YIELD
          </span>
          <span className="cream-pill px-2.5 py-0.5 rounded-full text-[11px] text-stone-700 font-mono font-medium">
            {metrics?.status_breakdown.recovered || 0} secured
          </span>
        </div>

        <div className="text-3xl font-bold font-mono tracking-tight text-stone-900">
          {rate}%
        </div>

        {/* Recessed Cream Progress Well */}
        <div className="mt-3 w-full cream-well h-2.5 rounded-full overflow-hidden p-[1px]">
          <div
            className="bg-gradient-to-r from-sky-600 via-teal-600 to-emerald-600 h-full rounded-full transition-all duration-700 ease-out shadow-sm"
            style={{ width: `${Math.min(100, Math.max(4, rate))}%` }}
          />
        </div>
      </div>

      {/* 4. ROI Multiplier Card */}
      <div className="cream-raised rounded-2xl p-5 relative overflow-hidden transition-all duration-300 hover:translate-y-[-1px]">
        <div className="flex items-center justify-between text-stone-500 text-xs font-mono mb-2.5">
          <span className="flex items-center gap-2 text-purple-800 font-semibold tracking-wide">
            <span className="p-1 rounded-lg cream-well text-purple-700">
              <Zap className="w-3.5 h-3.5" />
            </span>
            NET RECOVERY ROI
          </span>
          <span className="cream-pill px-2.5 py-0.5 rounded-full text-[11px] text-stone-700 font-mono font-medium">
            Cost: ₹{metrics?.estimated_messaging_cost_inr || 0}
          </span>
        </div>

        <div className="text-3xl font-bold font-mono tracking-tight text-purple-900">
          {roi.toLocaleString('en-IN')}x
        </div>

        <div className="mt-3 flex items-center gap-1.5 text-[11px] font-sans text-stone-500">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
          <span>100% Deterministic Stopping Rules</span>
        </div>
      </div>
    </div>
  );
};
