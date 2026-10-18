export interface CompanyState {
  id: string;
  name: string;
  industry: string;
  reputation: number;
}

export interface GameClock {
  current_day: number;
  is_paused: boolean;
  tick_speed_seconds: number;
}

export interface LedgerEntry {
  id: string;
  day: number;
  timestamp?: string;
  category: 'REVENUE' | 'COGS' | 'WAGES' | 'OPEX' | 'MARKETING' | 'RD' | 'EQUITY_INJECTION' | 'MISC';
  amount: number;
  balance_after: number;
  reference_id?: string;
  description: string;
}

export interface Product {
  id: string;
  name: string;
  category: string;
  status: 'ACTIVE' | 'DISCONTINUED' | 'IN_DEVELOPMENT';
  selling_price: number;
  production_cost: number;
  quality: number;
  inventory_units: number;
  daily_production_target: number;
  unmet_demand_last_day: number;
  units_sold_last_day: number;
  total_units_sold: number;
  total_revenue: number;
}

export interface DailySnapshot {
  day: number;
  cash_balance: number;
  revenue: number;
  cogs: number;
  operating_expenses: number;
  net_profit: number;
  total_units_sold: number;
  unmet_demand: number;
  reputation: number;
  inventory_value: number;
  total_valuation: number;
}

export interface ActivityLogItem {
  id: number;
  day: number;
  category: 'SYSTEM' | 'FINANCE' | 'OPERATIONS' | 'MARKETING' | 'RESEARCH' | 'AI';
  severity: 'INFO' | 'WARNING' | 'SUCCESS' | 'DANGER';
  message: string;
  details_json?: string;
  created_at?: string;
}

export interface AIDecisionRecord {
  id: string;
  day: number;
  manager_role: string;
  action_type: string;
  parameters_json: string;
  reasoning: string;
  confidence: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXECUTED' | 'FAILED';
  result_summary?: string;
  created_at?: string;
}

export interface AIConfig {
  enabled: boolean;
  provider: string;
  base_url: string;
  model_id: string;
  autonomy_mode: 'autonomous' | 'oversight' | 'player_approval';
  review_frequency_days: number;
  timeout_seconds: number;
}

export interface AIHealthStatus {
  connected: boolean;
  provider: string;
  base_url: string;
  model_id: string;
  models_available: string[];
  error_message?: string;
}

export interface FullGameState {
  company: CompanyState;
  clock: GameClock;
  cash_balance: number;
  products: Product[];
  latest_snapshot: DailySnapshot | null;
  historical_snapshots: DailySnapshot[];
  recent_transactions: LedgerEntry[];
  recent_activities: ActivityLogItem[];
  ai_decisions: AIDecisionRecord[];
  daily_fixed_opex: number;
}
