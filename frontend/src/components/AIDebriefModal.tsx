import React from 'react';
import { X, Sparkles, Brain, CheckCircle2, TrendingUp, AlertTriangle, Cpu } from 'lucide-react';

interface AIDebriefData {
  executive_summary: string;
  systemic_findings: string[];
  gateway_recommendations: string[];
}

interface AIDebriefModalProps {
  isOpen: boolean;
  onClose: () => void;
  debrief: AIDebriefData | null;
  isLoading: boolean;
  onRefresh: (model?: string) => void;
  modelName: string;
}

export const AIDebriefModal: React.FC<AIDebriefModalProps> = ({
  isOpen,
  onClose,
  debrief,
  isLoading,
  onRefresh,
  modelName = 'github/gpt-4o-mini',
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
      <div className="cream-card modal-shadow w-full max-w-2xl rounded-2xl overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-5 border-b border-[#e5dec9] bg-[#fbf9f4] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-amber-700 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-mono text-sm font-bold text-stone-900 tracking-tight">
                  OmniRoute AI Executive Debrief
                </h3>
                <span className="cream-pill text-[10px] font-mono px-2 py-0.5 rounded-full text-indigo-950 font-bold bg-indigo-100 border border-indigo-300 flex items-center gap-1">
                  <Cpu className="w-2.5 h-2.5" /> LIVE AI
                </span>
              </div>
              <p className="text-[11px] text-stone-500 font-sans mt-0.5">
                Multi-model portfolio diagnosis & payment rail optimization
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg cream-btn flex items-center justify-center text-stone-500 hover:text-stone-900 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-stone-800 text-xs font-sans">
          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
              <Brain className="w-8 h-8 text-amber-700 animate-bounce" />
              <div className="font-mono text-xs font-semibold text-stone-700">
                Synthesizing Gateway Telemetry via OmniRoute...
              </div>
              <p className="text-[11px] text-stone-500 max-w-sm">
                Clustering failure root causes, auditing banking maintenance windows, and generating CFO debrief.
              </p>
            </div>
          ) : debrief ? (
            <>
              {/* Executive Summary Callout */}
              <div className="p-4 rounded-xl cream-well border-l-4 border-amber-600 bg-amber-50/40">
                <span className="text-amber-900 font-mono text-[10px] uppercase tracking-wider font-bold block mb-1 flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-amber-700" /> Strategic Portfolio Health
                </span>
                <p className="text-stone-900 text-xs leading-relaxed font-medium">
                  {debrief.executive_summary}
                </p>
              </div>

              {/* Systemic Findings */}
              <div className="space-y-2">
                <span className="text-stone-700 font-mono text-[11px] uppercase tracking-wider font-bold flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-orange-600" /> Systemic Rail Findings
                </span>
                <div className="cream-well rounded-xl p-3.5 space-y-2">
                  {debrief.systemic_findings.map((finding, idx) => (
                    <div key={idx} className="flex items-start gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-1.5 shrink-0" />
                      <p className="text-stone-800 text-[11px] leading-relaxed">
                        {finding}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Gateway Recommendations */}
              <div className="space-y-2">
                <span className="text-emerald-900 font-mono text-[11px] uppercase tracking-wider font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" /> Gateway Optimization Steps
                </span>
                <div className="cream-well rounded-xl p-3.5 space-y-2 border border-emerald-200/60 bg-emerald-50/20">
                  {debrief.gateway_recommendations.map((rec, idx) => (
                    <div key={idx} className="flex items-start gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mt-1.5 shrink-0" />
                      <p className="text-stone-900 text-[11px] font-medium leading-relaxed">
                        {rec}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="py-8 text-center text-stone-500">
              No debrief available. Click re-analyze below.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#e5dec9] bg-[#fbf9f4] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-mono text-stone-600">
            <span className="font-semibold text-stone-800">Model:</span>
            <select
              value={modelName}
              onChange={(e) => onRefresh(e.target.value)}
              disabled={isLoading}
              className="bg-white border border-[#d6cfbe] text-stone-800 px-2.5 py-1.5 rounded-xl text-xs font-mono font-semibold cursor-pointer focus:outline-none focus:ring-1 focus:ring-amber-500 shadow-xs max-w-[280px]"
            >
              <option value="github/gpt-4o-mini">github/gpt-4o-mini</option>
              <option value="github/gpt-4o-2024-11-20">github/gpt-4o</option>
              <option value="antigravity/gemini-3.6-flash-high">antigravity/gemini-3.6-flash-high</option>
              <option value="antigravity/gemini-3.1-pro-low">antigravity/gemini-3.1-pro-low</option>
              <option value="claude-web/claude-opus-5">claude-web/claude-opus-5</option>
              <option value="chatgpt-web/gpt-5.6-pro">chatgpt-web/gpt-5.6-pro</option>
              <option value="deepseek-web/deepseek-v4-pro-think">deepseek-web/deepseek-v4-pro-think</option>
              <option value="cline/anthropic/claude-opus-4.8">cline/anthropic/claude-opus-4.8</option>
              <option value="codex/gpt-5.6-terra-ultra">codex/gpt-5.6-terra-ultra</option>
              <option value="kiro/qwen3-coder-next">kiro/qwen3-coder-next</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onRefresh(modelName)}
              disabled={isLoading}
              className="px-3 py-1.5 rounded-xl cream-btn text-xs font-mono text-stone-700 font-semibold cursor-pointer disabled:opacity-50"
            >
              ↻ Re-Analyze
            </button>
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-xl bg-stone-900 text-white text-xs font-mono font-semibold cursor-pointer hover:bg-black transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
