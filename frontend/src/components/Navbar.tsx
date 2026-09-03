import React from 'react';
import { Shield, Radio, Terminal, QrCode, ScrollText, Play, RefreshCw, Trash2, Sparkles } from 'lucide-react';

interface NavbarProps {
  onInjectBatch: () => void;
  onOpenQR: () => void;
  onOpenAudit: () => void;
  onOpenAIDebrief: () => void;
  onRefresh: () => void;
  onResetLedger: () => void;
  isBatchRunning: boolean;
  isRefreshing: boolean;
  isResetting: boolean;
  isLiveSync: boolean;
  onToggleLiveSync: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  onInjectBatch,
  onOpenQR,
  onOpenAudit,
  onOpenAIDebrief,
  onRefresh,
  onResetLedger,
  isBatchRunning,
  isRefreshing,
  isResetting,
  isLiveSync,
  onToggleLiveSync,
}) => {
  return (
    <header className="px-6 py-3.5 sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
      <div className="max-w-[1680px] mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Brand & Identity */}
        <div className="flex items-center gap-3.5">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-slate-900 text-white shadow-[0_4px_10px_rgba(0,0,0,0.2)]">
            <Shield className="w-5 h-5 text-sky-400" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <span className="font-bold tracking-tight text-slate-900 font-mono text-base">RAZORLOOP</span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200 font-semibold shadow-xs">
                Track 03 • AI Revenue Recovery
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-sans tracking-wide">
              Autonomous Bounded Recovery Engine for Razorpay
            </p>
          </div>
        </div>

        {/* Center: System Telemetry */}
        <div className="hidden xl:flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl cream-well text-slate-700">
            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]"></span>
            <span>GATEWAY: <strong className="text-slate-900 font-semibold">RAZORPAY TESTNET</strong></span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl cream-well text-slate-700">
            <Radio className="w-3.5 h-3.5 text-sky-600" />
            <span>CHANNEL: <strong className="text-sky-700 font-semibold">@razor_loop_bot</strong></span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl cream-well text-slate-700">
            <Terminal className="w-3.5 h-3.5 text-amber-600" />
            <span>TRIAGE: <strong className="text-slate-900 font-semibold">T+90s BOUNDED</strong></span>
          </div>
        </div>

        {/* Right Action Controls */}
        <div className="flex items-center gap-2.5">
          {/* Live Sync Toggle */}
          <button
            onClick={onToggleLiveSync}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-mono rounded-xl cream-btn cursor-pointer ${
              isLiveSync ? 'text-emerald-700 font-semibold' : 'text-slate-400'
            }`}
            title="Toggle background auto-polling"
          >
            <span className={`w-2 h-2 rounded-full ${isLiveSync ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`} />
            <span>{isLiveSync ? 'Live Sync: ON' : 'Live Sync: PAUSED'}</span>
          </button>

          {/* Manual Refresh */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center justify-center w-9 h-9 rounded-xl cream-btn text-slate-600 hover:text-slate-900 transition cursor-pointer"
            title="Refresh Ledger"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-sky-600' : ''}`} />
          </button>

          {/* Reset Ledger (Start Fresh / Wipe Cache) */}
          <button
            onClick={onResetLedger}
            disabled={isResetting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded-xl cream-btn text-rose-700 hover:text-rose-900 hover:border-rose-300 transition cursor-pointer"
            title="Clear all incidents & audit cache to start fresh"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-600" />
            <span>{isResetting ? 'Wiping...' : 'Reset Ledger'}</span>
          </button>

          {/* Connect Mobile (QR Code) */}
          <button
            onClick={onOpenQR}
            className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-mono rounded-xl cream-btn text-slate-700 hover:text-slate-900 transition cursor-pointer font-medium"
          >
            <QrCode className="w-3.5 h-3.5 text-sky-600" />
            <span>Connect Mobile</span>
          </button>

          {/* Audit Chain */}
          <button
            onClick={onOpenAudit}
            className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-mono rounded-xl cream-btn text-slate-700 hover:text-slate-900 transition cursor-pointer font-medium"
          >
            <ScrollText className="w-3.5 h-3.5 text-purple-600" />
            <span>Audit Chain</span>
          </button>

          {/* AI Executive Debrief */}
          <button
            onClick={onOpenAIDebrief}
            className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-mono rounded-xl cream-btn text-indigo-950 hover:text-indigo-900 border-indigo-300 transition cursor-pointer font-semibold shadow-xs"
            title="Synthesize real-time AI Executive Summary via OmniRoute"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-700" />
            <span>AI Debrief</span>
          </button>

          {/* Primary Action: Inject Batch */}
          <button
            onClick={onInjectBatch}
            disabled={isBatchRunning}
            className={`flex items-center gap-2 px-4.5 py-1.5 text-xs font-mono font-semibold rounded-xl transition-all cursor-pointer ${
              isBatchRunning
                ? 'bg-amber-100 text-amber-900 border border-amber-300 cursor-wait'
                : 'bg-slate-900 hover:bg-slate-800 text-white shadow-[0_6px_18px_rgba(0,0,0,0.22)] border border-slate-900 hover:shadow-[0_8px_24px_rgba(0,0,0,0.3)]'
            }`}
          >
            <Play className={`w-3.5 h-3.5 ${isBatchRunning ? 'animate-spin' : 'text-emerald-400'}`} />
            <span>{isBatchRunning ? 'Simulating Batch...' : 'Inject Batch (20 Cases)'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
