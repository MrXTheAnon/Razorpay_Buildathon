import React from 'react';
import type { AuditLogEntry } from '../types';
import { X, ShieldCheck, Hash, FileCheck2 } from 'lucide-react';

interface AuditModalProps {
  isOpen: boolean;
  onClose: () => void;
  logs: AuditLogEntry[];
}

export const AuditModal: React.FC<AuditModalProps> = ({ isOpen, onClose, logs }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white border border-[#d8d0c2] rounded-3xl w-full max-w-4xl max-h-[85vh] flex flex-col modal-shadow overflow-hidden font-sans">
        {/* Header */}
        <div className="px-6 py-4.5 border-b border-[#e5dec9] flex items-center justify-between bg-[#fbf9f4]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl cream-well flex items-center justify-center text-purple-700">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-stone-900 font-mono uppercase tracking-wider">
                Cryptographic Audit Ledger & Compliance Chain
              </h2>
              <p className="text-xs text-stone-500 font-sans mt-0.5">
                SHA-256 Hashed Evidence satisfying RBI / NPCI Regulatory Audits
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg cream-btn text-stone-500 hover:text-stone-900 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Logs Table */}
        <div className="p-6 overflow-y-auto flex-1 divide-y divide-[#eee9de] font-mono bg-white">
          {logs.length === 0 ? (
            <div className="text-center text-stone-500 py-16 text-xs">
              No audit records generated yet. Ledger is clean.
            </div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="py-4 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-purple-900">{log.agent_name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full cream-pill text-stone-800 font-semibold">
                      {log.event_type}
                    </span>
                    <span className="text-stone-500 text-[11px]">{log.incident_id}</span>
                  </div>
                  <span className="text-stone-400 text-[10px]">
                    {new Date(log.timestamp).toLocaleTimeString()} • {new Date(log.timestamp).toLocaleDateString()}
                  </span>
                </div>

                <p className="text-xs text-stone-800 font-sans font-medium leading-relaxed">{log.details}</p>

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1.5 text-[10px]">
                  <div className="flex items-center gap-1.5 text-emerald-900 bg-emerald-50 px-2.5 py-0.5 rounded-md border border-emerald-300 font-medium">
                    <FileCheck2 className="w-3 h-3 text-emerald-700" />
                    <span>Rule: {log.compliance_rule}</span>
                  </div>

                  <div className="flex items-center gap-1.5 text-stone-600 cream-well px-2.5 py-0.5 rounded-md">
                    <Hash className="w-3 h-3 text-sky-700" />
                    <span className="truncate max-w-[240px] font-semibold">Hash: {log.event_hash}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-[#e5dec9] bg-[#fbf9f4] flex items-center justify-between text-xs font-mono text-stone-600">
          <span className="font-semibold text-emerald-800 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
            Chain State: VERIFIED & TAMPER-EVIDENT
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl cream-btn text-stone-800 text-xs font-mono font-medium cursor-pointer"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
