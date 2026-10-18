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

export interface Employee {
  id: string;
  name: string;
  role: string;
  department: string;
  daily_wage: number;
  productivity: number;
  morale: number;
  hired_day: number;
  status: string;
}

export interface Loan {
  id: string;
  principal: number;
  remaining_principal: number;
  interest_rate: number;
  daily_payment: number;
  term_days: number;
  start_day: number;
  status: string;
}

export interface MarketingCampaign {
  id: string;
  name: string;
  target_product_id?: string;
  daily_budget: number;
  remaining_days: number;
  effectiveness: number;
  status: string;
}

export interface RdProject {
  id: string;
  name: string;
  target_product_id: string;
  cost_per_day: number;
  days_remaining: number;
  total_days: number;
  quality_boost: number;
  status: string;
}

export interface GameSettings {
  mode: string;
  difficulty: string;
  campaign_goal?: string;
  campaign_target_value?: number;
  campaign_deadline_days?: number;
  game_state: string;
  win_loss_reason?: string;
}

export interface FullGameState {
  company: CompanyState;
  clock: GameClock;
  cash_balance: number;
  company_valuation: number;
  current_day: number;
  products: Product[];
  latest_snapshot: DailySnapshot | null;
  historical_snapshots: DailySnapshot[];
  recent_transactions: LedgerEntry[];
  recent_activities: ActivityLogItem[];
  ai_decisions: AIDecisionRecord[];
  employees: Employee[];
  active_loans: Loan[];
  active_campaigns: MarketingCampaign[];
  rd_projects: RdProject[];
  game_settings: GameSettings;
  daily_fixed_opex: number;
}
export interface AIAgent {
  id: string;
  name: string;
  title: string;
  department: string;
  level: number;
  supervisor_id?: string | null;
  specialization: string;
  allowed_tasks: string[];
  permissions: Record<string, boolean>;
  current_status: 'IDLE' | 'ANALYZING' | 'WORKING' | 'AWAITING_REVIEW' | 'AWAITING_APPROVAL' | 'BLOCKED' | 'OFFLINE';
  current_objective: string;
  performance_score: number;
  tasks_completed: number;
  tasks_failed: number;
}

export interface AITask {
  id: string;
  title: string;
  description: string;
  department: string;
  task_type: string;
  assigned_agent_id: string;
  supervisor_id: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  status: 'ASSIGNED' | 'IN_PROGRESS' | 'AWAITING_REVIEW' | 'REVISION_REQUESTED' | 'AWAITING_APPROVAL' | 'COMPLETED' | 'FAILED' | 'BLOCKED' | 'CANCELLED';
  created_day: number;
  deadline_day: number;
  deliverable?: any;
  recommendation_action?: any;
  review_status: string;
  review_feedback?: string;
  revision_count: number;
  blocked_reason?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AITaskReview {
  id: string;
  task_id: string;
  reviewer_agent_id: string;
  decision: 'APPROVED' | 'REVISION_REQUESTED' | 'ESCALATED' | 'REJECTED';
  feedback: string;
  score: number;
  day: number;
  created_at?: string;
}

export interface WorkOverview {
  tasks_in_progress: number;
  awaiting_review: number;
  awaiting_approval: number;
  blocked: number;
  completed: number;
  failed: number;
  status_counts: Record<string, number>;
  recent_reviews: AITaskReview[];
}
