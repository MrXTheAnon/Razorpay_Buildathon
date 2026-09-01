import React from 'react';
import type { BankHealth } from '../types';
import { Activity, Clock } from 'lucide-react';

interface BankTelemetryBarProps {
  telemetry: BankHealth | null;
}

export const BankTelemetryBar: React.FC<BankTelemetryBarProps> = ({ telemetry }) => {
  if (!telemetry) return null;

  return (
    <div className="cream-card rounded-2xl p-3.5 px-4.5">
      <div className="flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
        <div className="flex items-center gap-2.5 text-stone-600">
          <div className="w-6 h-6 rounded-lg cream-well flex items-center justify-center text-sky-700">
            <Activity className="w-3.5 h-3.5" />
          </div>
          <span className="font-semibold text-stone-800 tracking-wide text-[11px]">
            NPCI & ISSUER CORE TELEMETRY:
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          {Object.entries(telemetry).map(([code, data]) => {
            const isDegraded = data.status === 'DEGRADED';
            return (
              <div key={code} className="flex items-center gap-2 cream-well px-3 py-1.5 rounded-xl">
                <span
                  className={`w-2 h-2 rounded-full ${
                    isDegraded
                      ? 'bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.5)]'
                      : 'bg-emerald-600 shadow-[0_0_6px_rgba(5,150,105,0.4)]'
                  }`}
                />
                <span className="font-bold text-stone-800 text-xs">{code}:</span>
                <span
                  className={`font-semibold text-xs ${
                    isDegraded ? 'text-amber-800 font-bold' : 'text-emerald-800'
                  }`}
                >
                  {data.success_rate}%
                </span>
                {isDegraded && (
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1 font-mono font-medium">
                    <Clock className="w-2.5 h-2.5" /> Next: {data.preferred_window}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
