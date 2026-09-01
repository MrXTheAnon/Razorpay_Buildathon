import React from 'react';
import { Zap, Handshake, FileSpreadsheet, RefreshCw, Globe, ArrowUpRight } from 'lucide-react';

interface AgentLanesProps {
  onTriggerSim: (track: string) => void;
  isSimulating: boolean;
}

export const AgentLanes: React.FC<AgentLanesProps> = ({ onTriggerSim, isSimulating }) => {
  const agents = [
    {
      id: 'in_flight_upi',
      name: 'In-Flight UPI Drop-Off Reassurer',
      tag: 'B2C Checkout',
      icon: Zap,
      accentColor: 'text-amber-700',
      tagStyle: 'bg-amber-100 text-amber-900 border-amber-300',
      problem: 'App-switch session killed; buyer halts fearing double-debit.',
      intervention: 'Confirms ₹0 debited on issuer + Sends 1-click fallback link.',
      stoppingRule: 'Instant halt on payment.captured or user cancel click.',
      buttonText: 'Trigger In-Flight Demo',
    },
    {
      id: 'ptp_split',
      name: 'Promise-to-Pay (PTP) Negotiator',
      tag: 'Subscriptions',
      icon: Handshake,
      accentColor: 'text-sky-700',
      tagStyle: 'bg-sky-100 text-sky-900 border-sky-300',
      problem: 'Annual renewal cash crunch causes customer churn.',
      intervention: 'Restructures into 2x 50% tranches + Pauses dunning for 15 days.',
      stoppingRule: 'Tranche 1 payment locks in grace period; halts reminders.',
      buttonText: 'Trigger PTP Demo',
    },
    {
      id: 'b2b_dispute',
      name: 'B2B TDS / GST Dispute Chaser',
      tag: 'Enterprise Invoicing',
      icon: FileSpreadsheet,
      accentColor: 'text-purple-700',
      tagStyle: 'bg-purple-100 text-purple-900 border-purple-300',
      problem: 'Client AP withholds 2% TDS (194C vs 194J); invoices stall.',
      intervention: 'Auto-checks variance ≤5% + Generates Net Smart Collect VA.',
      stoppingRule: 'Variance >5% halts dunning & routes packet to CFO.',
      buttonText: 'Trigger B2B Dispute',
    },
    {
      id: 'mandate_failure',
      name: 'Mandate Degradation Healer',
      tag: 'UPI Autopay & e-NACH',
      icon: RefreshCw,
      accentColor: 'text-emerald-700',
      tagStyle: 'bg-emerald-100 text-emerald-900 border-emerald-300',
      problem: 'NPCI 8-11 PM maintenance causes repeated blind retry failures.',
      intervention: 'Inspects bank health + Reschedules 24h notice to 06:30 AM.',
      stoppingRule: 'Suppresses blind retries; max 3 compliant attempts.',
      buttonText: 'Trigger Mandate Demo',
    },
    {
      id: 'cross_border',
      name: 'Cross-Border Decline Translator',
      tag: 'Global & LRS / 3DS2',
      icon: Globe,
      accentColor: 'text-indigo-700',
      tagStyle: 'bg-indigo-100 text-indigo-900 border-indigo-300',
      problem: 'RBI mandate disables international card e-commerce by default.',
      intervention: 'Detects issuer BIN + Sends 1-tap app toggle guide & PayPal rail.',
      stoppingRule: 'Instant halt on 3DS2 card re-auth or alternative rail selection.',
      buttonText: 'Trigger Cross-Border',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      {agents.map((agent) => {
        const Icon = agent.icon;
        return (
          <div
            key={agent.id}
            className="cream-raised rounded-2xl p-4.5 flex flex-col justify-between transition-all duration-300 hover:translate-y-[-2px] group"
          >
            <div>
              {/* Header */}
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border font-semibold ${agent.tagStyle}`}>
                  {agent.tag}
                </span>
                <div className="w-8 h-8 rounded-xl cream-well flex items-center justify-center">
                  <Icon className={`w-4 h-4 ${agent.accentColor} transition-transform group-hover:scale-110`} />
                </div>
              </div>

              <h3 className="font-semibold text-xs font-mono text-slate-900 tracking-tight leading-snug mb-3">
                {agent.name}
              </h3>

              {/* Information Wells */}
              <div className="space-y-2 text-xs font-sans">
                <div className="cream-well p-2.5 rounded-xl">
                  <span className="text-slate-500 block text-[9px] font-mono uppercase tracking-wider font-semibold">
                    Diagnosis
                  </span>
                  <p className="text-slate-800 text-[11px] leading-relaxed mt-0.5 font-medium">
                    {agent.problem}
                  </p>
                </div>

                <div className="cream-well p-2.5 rounded-xl">
                  <span className="text-slate-500 block text-[9px] font-mono uppercase tracking-wider font-semibold">
                    Intervention
                  </span>
                  <p className="text-slate-800 text-[11px] leading-relaxed mt-0.5 font-medium">
                    {agent.intervention}
                  </p>
                </div>

                <div className="cream-well p-2.5 rounded-xl border-l-2 border-emerald-600 bg-emerald-50/50">
                  <span className="text-emerald-800 block text-[9px] font-mono uppercase tracking-wider font-bold">
                    Stopping Rule
                  </span>
                  <p className="text-emerald-950 font-mono text-[10px] leading-relaxed mt-0.5 font-medium">
                    {agent.stoppingRule}
                  </p>
                </div>
              </div>
            </div>

            {/* Action Button */}
            <button
              onClick={() => onTriggerSim(agent.id)}
              disabled={isSimulating}
              className="mt-4 w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl cream-btn text-slate-800 text-xs font-mono font-semibold transition-all cursor-pointer group-hover:text-black shadow-xs"
            >
              <span>{agent.buttonText}</span>
              <ArrowUpRight className="w-3.5 h-3.5 opacity-70 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
