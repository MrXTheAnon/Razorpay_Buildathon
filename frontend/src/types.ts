export interface RecoveryIncident {
  id: string;
  created_at: string;
  customer_name: string;
  customer_phone: string;
  telegram_chat_id: string;
  track: 'in_flight_upi' | 'ptp_split' | 'b2b_dispute' | 'mandate_failure';
  original_amount: number;
  currency: string;
  status: 'pending' | 'diagnosed' | 'intervened' | 'recovered' | 'halted' | 'escalated';
  root_cause: string;
  intervention_action: string;
  stopping_rule_triggered?: string | null;
  razorpay_payment_id?: string | null;
  payment_link_id?: string | null;
  payment_link_url?: string | null;
  telegram_message_id?: number | null;
  recovered_amount: number;
  extra_data?: any;
}

export interface MetricSummary {
  total_incidents: number;
  total_at_risk_inr: number;
  total_recovered_inr: number;
  recovery_rate_percent: number;
  status_breakdown: {
    pending: number;
    intervened: number;
    recovered: number;
    halted: number;
    escalated: number;
  };
  track_breakdown: Array<{
    track: string;
    count: number;
    at_risk_inr: number;
    recovered_inr: number;
    recovery_rate: number;
  }>;
  estimated_messaging_cost_inr: number;
  roi_multiplier: number;
}

export interface AuditLogEntry {
  id: number;
  incident_id: string;
  timestamp: string;
  agent_name: string;
  event_type: string;
  details: string;
  compliance_rule: string;
  event_hash: string;
}

export interface BankHealth {
  [key: string]: {
    name: string;
    success_rate: number;
    status: string;
    npci_window_active: boolean;
    preferred_window: string;
  };
}
