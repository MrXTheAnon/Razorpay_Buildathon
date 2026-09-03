import React, { useState } from 'react';
import type { RecoveryIncident } from '../types';
import {
  CheckCircle2,
  Ban,
  Clock,
  AlertTriangle,
  ExternalLink,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Filter
} from 'lucide-react';

interface LiveIncidentFeedProps {
  incidents: RecoveryIncident[];
}

export const LiveIncidentFeed: React.FC<LiveIncidentFeedProps> = ({ incidents }) => {
  const [filter, setFilter] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'recovered':
        return (
          <span className="flex items-center gap-1.5 text-[11px] font-mono font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" /> RECOVERED (CONFIRMED)
          </span>
        );
      case 'halted':
        return (
          <span className="flex items-center gap-1.5 text-[11px] font-mono font-semibold px-2.5 py-1 rounded-full bg-rose-100 text-rose-900 border border-rose-300">
            <Ban className="w-3.5 h-3.5 text-rose-700" /> STOPPED (OPT-OUT)
          </span>
        );
      case 'escalated':
        return (
          <span className="flex items-center gap-1.5 text-[11px] font-mono font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-700" /> ESCALATED TO CFO
          </span>
        );
      case 'intervened':
      default:
        return (
          <span className="flex items-center gap-1.5 text-[11px] font-mono font-semibold px-2.5 py-1 rounded-full bg-sky-100 text-sky-900 border border-sky-300">
            <Clock className="w-3.5 h-3.5 text-sky-700 animate-spin" /> INTERVENED
          </span>
        );
    }
  };

  const getTrackTag = (track: string) => {
    switch (track) {
      case 'in_flight_upi':
        return <span className="cream-pill text-amber-900 font-mono text-[10px] px-2 py-0.5 rounded-full font-semibold">UPI INTENT</span>;
      case 'ptp_split':
        return <span className="cream-pill text-sky-900 font-mono text-[10px] px-2 py-0.5 rounded-full font-semibold">PTP SPLIT</span>;
      case 'b2b_dispute':
        return <span className="cream-pill text-purple-900 font-mono text-[10px] px-2 py-0.5 rounded-full font-semibold">B2B TDS</span>;
      case 'mandate_failure':
        return <span className="cream-pill text-emerald-900 font-mono text-[10px] px-2 py-0.5 rounded-full font-semibold">MANDATE</span>;
      case 'cross_border':
        return <span className="cream-pill text-indigo-900 font-mono text-[10px] px-2 py-0.5 rounded-full font-semibold">INTL 3DS2</span>;
      default:
        return <span className="cream-pill text-stone-600 font-mono text-[10px] px-2 py-0.5 rounded-full">{track}</span>;
    }
  };

  const filteredIncidents = incidents.filter((inc) => {
    if (filter === 'all') return true;
    if (filter === 'recovered') return inc.status === 'recovered';
    if (filter === 'intervened') return inc.status === 'intervened';
    if (filter === 'escalated') return inc.status === 'escalated';
    return inc.track === filter;
  });

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="cream-card rounded-2xl overflow-hidden flex flex-col shadow-sm">
      {/* Header & Category Tabs */}
      <div className="p-5 border-b border-[#e5dec9] bg-[#fbf9f4]/80 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-600 shadow-[0_0_6px_rgba(5,150,105,0.6)]" />
          <h3 className="font-mono text-xs font-bold text-stone-900 uppercase tracking-wider">
            Revenue Recovery Ledger & Incident Feed
          </h3>
          <span className="cream-pill text-[10px] font-mono px-2.5 py-0.5 rounded-full text-stone-700 font-medium">
            {incidents.length} total
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          <span className="text-stone-500 text-[11px] mr-1 flex items-center gap-1 font-sans">
            <Filter className="w-3 h-3 text-stone-400" /> Filter:
          </span>
          {[
            { id: 'all', label: 'All Cases' },
            { id: 'in_flight_upi', label: 'In-Flight UPI' },
            { id: 'ptp_split', label: 'PTP Split' },
            { id: 'b2b_dispute', label: 'B2B TDS' },
            { id: 'mandate_failure', label: 'Mandate' },
            { id: 'cross_border', label: 'Cross-Border' },
            { id: 'recovered', label: 'Secured' },
            { id: 'escalated', label: 'CFO Escalations' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              className={`px-3 py-1 rounded-xl transition cursor-pointer text-[11px] font-medium ${
                filter === tab.id
                  ? 'bg-sky-700 text-white font-semibold shadow-sm'
                  : 'cream-btn text-stone-700 hover:text-stone-950'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Incidents Stream */}
      <div className="divide-y divide-[#eee9de] max-h-[620px] overflow-y-auto bg-white">
        {filteredIncidents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-stone-400 font-mono text-xs text-center">
            <div className="w-10 h-10 rounded-full cream-well flex items-center justify-center text-stone-400 mb-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            </div>
            <p className="font-semibold text-stone-700">Ledger is clean and ready.</p>
            <p className="mt-1 text-stone-500">Click "Inject Batch (25 Cases)" or trigger an agent above to start your recording.</p>
          </div>
        ) : (
          filteredIncidents.map((inc) => {
            const isExpanded = expandedId === inc.id;
            return (
              <div
                key={inc.id}
                className="p-4.5 transition-all hover:bg-[#faf8f2] flex flex-col gap-2.5"
              >
                {/* Main Row */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-sm text-stone-900">
                      {inc.customer_name}
                    </span>
                    {getTrackTag(inc.track)}
                    <span className="font-mono text-[11px] text-stone-500">
                      {inc.id}
                    </span>
                    {inc.telegram_chat_id && (
                      <span className="text-[10px] font-mono text-stone-600 cream-pill px-2 py-0.5 rounded-full font-medium">
                        TG: {inc.telegram_chat_id}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-base text-stone-900">
                      ₹{inc.original_amount.toLocaleString('en-IN')}
                    </span>
                    {getStatusBadge(inc.status)}
                    <button
                      onClick={() => toggleExpand(inc.id)}
                      className="cream-btn p-1.5 rounded-lg text-stone-600 hover:text-stone-900 transition cursor-pointer"
                      title="Inspect Details"
                    >
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Summary Action */}
                <div className="text-xs text-stone-600 flex items-center justify-between gap-2 font-sans">
                  <div className="flex items-center gap-2 truncate">
                    <span className="text-stone-500 font-mono text-[10px] uppercase font-bold">
                      Intervention:
                    </span>
                    <span className="text-stone-800 font-medium truncate">
                      {inc.intervention_action || inc.root_cause}
                    </span>
                  </div>

                  {inc.payment_link_url && (
                    <a
                      href={inc.payment_link_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1.5 text-sky-800 hover:text-sky-950 font-mono text-[11px] shrink-0 font-semibold transition"
                    >
                      <span>Razorpay Checkout</span>
                      <ExternalLink className="w-3 h-3 text-sky-700" />
                    </a>
                  )}
                </div>

                {/* Stopping Rule Notification Banner */}
                {inc.stopping_rule_triggered && (
                  <div className="flex items-center gap-2 text-[11px] font-mono text-emerald-950 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-300 shadow-sm font-medium">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
                    <span className="truncate">{inc.stopping_rule_triggered}</span>
                  </div>
                )}

                {/* Expanded Inspection Drawer */}
                {isExpanded && (
                  <div className="mt-2 cream-well rounded-xl p-3.5 space-y-2 text-xs font-mono">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <span className="text-stone-600 uppercase text-[10px] block font-bold">
                          Root Cause Telemetry
                        </span>
                        <p className="text-stone-900 font-sans text-xs mt-0.5 font-medium">
                          {inc.root_cause || 'Detected drop-off via gateway telemetry.'}
                        </p>
                      </div>

                      <div>
                        <span className="text-stone-600 uppercase text-[10px] block font-bold">
                          Timestamp & Gateway ID
                        </span>
                        <p className="text-stone-900 text-xs mt-0.5 font-medium">
                          {new Date(inc.created_at).toLocaleString()} • {inc.razorpay_payment_id || 'Awaiting Settlement'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
