import React, { useState, useEffect, useCallback } from 'react';
import type { RecoveryIncident, MetricSummary, AuditLogEntry, BankHealth } from './types';
import { Navbar } from './components/Navbar';
import { FinancialTicker } from './components/FinancialTicker';
import { AgentLanes } from './components/AgentLanes';
import { BankTelemetryBar } from './components/BankTelemetryBar';
import { LiveIncidentFeed } from './components/LiveIncidentFeed';
import { AuditModal } from './components/AuditModal';
import { QRModal } from './components/QRModal';

export const App: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricSummary | null>(null);
  const [incidents, setIncidents] = useState<RecoveryIncident[]>([]);
  const [bankTelemetry, setBankTelemetry] = useState<BankHealth | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);

  const [isBatchRunning, setIsBatchRunning] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isAuditOpen, setIsAuditOpen] = useState(false);
  const [isQROpen, setIsQROpen] = useState(false);
  const [userChatId, setUserChatId] = useState('');
  const [isLiveSync, setIsLiveSync] = useState(true);

  // Fetch core ledger and metrics
  const fetchLedger = useCallback(async () => {
    try {
      const [mRes, iRes] = await Promise.all([
        fetch('/api/v1/recovery/metrics'),
        fetch('/api/v1/recovery/incidents?limit=50'),
      ]);

      if (mRes.ok) {
        const mData = await mRes.json();
        setMetrics(mData);
      }
      if (iRes.ok) {
        const iData = await iRes.json();
        setIncidents(iData);
      }
    } catch (e) {
      console.error('Error fetching ledger data:', e);
    }
  }, []);

  // Fetch bank telemetry once
  const fetchBankTelemetry = useCallback(async () => {
    try {
      const bRes = await fetch('/api/v1/recovery/bank-telemetry');
      if (bRes.ok) {
        const bData = await bRes.json();
        setBankTelemetry(bData);
      }
    } catch (e) {
      console.error('Error fetching bank telemetry:', e);
    }
  }, []);

  // Manual refresh handler
  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([fetchLedger(), fetchBankTelemetry()]);
    setTimeout(() => setIsRefreshing(false), 300);
  };

  // Reset Ledger (Wipe Database / Cache to start fresh)
  const handleResetLedger = async () => {
    if (!window.confirm('Clear all previous incidents and start fresh with ₹0 ledger?')) {
      return;
    }
    setIsResetting(true);
    try {
      const res = await fetch('/api/v1/recovery/reset', { method: 'POST' });
      if (res.ok) {
        setIncidents([]);
        setMetrics({
          total_incidents: 0,
          total_at_risk_inr: 0,
          total_recovered_inr: 0,
          recovery_rate_percent: 0,
          status_breakdown: { pending: 0, intervened: 0, recovered: 0, halted: 0, escalated: 0 },
          track_breakdown: [],
          estimated_messaging_cost_inr: 0,
          roi_multiplier: 0,
        });
      }
    } catch (e) {
      console.error('Reset error:', e);
    } finally {
      setIsResetting(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchLedger();
    fetchBankTelemetry();
  }, [fetchLedger, fetchBankTelemetry]);

  // Calm background sync (15s, toggleable)
  useEffect(() => {
    if (!isLiveSync) return;
    const interval = setInterval(fetchLedger, 15000);
    return () => clearInterval(interval);
  }, [isLiveSync, fetchLedger]);

  // Fetch audit logs when opening modal
  const handleOpenAudit = async () => {
    try {
      const res = await fetch('/api/v1/recovery/audit-logs?limit=50');
      if (res.ok) {
        const logs = await res.json();
        setAuditLogs(logs);
      }
    } catch (e) {
      console.error('Error fetching audit logs:', e);
    }
    setIsAuditOpen(true);
  };

  // 1. Inject Batch (25 cases)
  const handleInjectBatch = async () => {
    setIsBatchRunning(true);
    try {
      const res = await fetch('/api/v1/recovery/batch-simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: 25 }),
      });
      if (res.ok) {
        await fetchLedger();
      }
    } catch (e) {
      console.error('Batch simulate error:', e);
    } finally {
      setIsBatchRunning(false);
    }
  };

  // 2. Trigger Single Simulation (Dispatches real card to Telegram mobile)
  const handleTriggerSim = async (track: string, customChatId?: string) => {
    setIsSimulating(true);
    try {
      const res = await fetch('/api/v1/recovery/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          track,
          telegram_chat_id: customChatId || userChatId || undefined,
          amount: track === 'in_flight_upi' ? 1499 : track === 'ptp_split' ? 8999 : track === 'b2b_dispute' ? 45000 : track === 'cross_border' ? 12500 : 1999,
        }),
      });
      if (res.ok) {
        await fetchLedger();
      }
    } catch (e) {
      console.error('Simulate incident error:', e);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f7f5ee] text-stone-900 flex flex-col font-sans cream-canvas">
      {/* Top Navbar */}
      <Navbar
        onInjectBatch={handleInjectBatch}
        onOpenQR={() => setIsQROpen(true)}
        onOpenAudit={handleOpenAudit}
        onRefresh={handleManualRefresh}
        onResetLedger={handleResetLedger}
        isBatchRunning={isBatchRunning}
        isRefreshing={isRefreshing}
        isResetting={isResetting}
        isLiveSync={isLiveSync}
        onToggleLiveSync={() => setIsLiveSync((prev) => !prev)}
      />

      {/* Main Executive Command Canvas */}
      <main className="flex-1 p-6 max-w-[1680px] w-full mx-auto space-y-6">
        {/* Row 1: Neumorphic Cream Financial Ticker */}
        <FinancialTicker metrics={metrics} />

        {/* Row 2: Bank Telemetry Health Bar */}
        <BankTelemetryBar telemetry={bankTelemetry} />

        {/* Row 3: The 4 Bounded Agent Command Lanes */}
        <section className="space-y-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-stone-700">
              Active Bounded Recovery Agents
            </h2>
            <span className="text-[11px] font-mono text-stone-500 font-medium">
              Tri-State Protocol: Diagnosis → Intervention → Hard Stopping Rule
            </span>
          </div>
          <AgentLanes onTriggerSim={(track) => handleTriggerSim(track)} isSimulating={isSimulating} />
        </section>

        {/* Row 4: Full-Width Executive Recovery Ledger */}
        <section className="w-full">
          <LiveIncidentFeed incidents={incidents} />
        </section>
      </main>

      {/* Modals */}
      <AuditModal
        isOpen={isAuditOpen}
        onClose={() => setIsAuditOpen(false)}
        logs={auditLogs}
      />

      <QRModal
        isOpen={isQROpen}
        onClose={() => setIsQROpen(false)}
        onSendToChatId={(chatId) => {
          setUserChatId(chatId);
          handleTriggerSim('in_flight_upi', chatId);
        }}
        defaultChatId={userChatId}
      />
    </div>
  );
};

export default App;
