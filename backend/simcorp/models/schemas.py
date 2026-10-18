"""Pydantic data models for SimCorp state, requests, and responses."""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class CompanyState(BaseModel):
    id: str
    name: str
    industry: str
    reputation: float

class GameClock(BaseModel):
    current_day: int
    is_paused: bool
    tick_speed_seconds: float

class LedgerEntry(BaseModel):
    id: str
    day: int
    timestamp: Optional[str] = None
    category: str
    amount: float
    balance_after: float
    reference_id: Optional[str] = None
    description: str

class Product(BaseModel):
    id: str
    name: str
    category: str
    status: str
    selling_price: float
    production_cost: float
    quality: float
    inventory_units: int
    daily_production_target: int
    unmet_demand_last_day: int
    units_sold_last_day: int
    total_units_sold: int
    total_revenue: float

class DailySnapshot(BaseModel):
    day: int
    cash_balance: float
    revenue: float
    cogs: float
    operating_expenses: float
    net_profit: float
    total_units_sold: int
    unmet_demand: int
    reputation: float
    inventory_value: float
    total_valuation: float
    wages_paid: float = 0.0
    marketing_spend: float = 0.0
    rd_spend: float = 0.0
    headcount: int = 0
    distress_stage: str = "HEALTHY"

class ActivityLogItem(BaseModel):
    id: int
    day: int
    category: str
    severity: str
    message: str
    details_json: Optional[str] = None
    created_at: Optional[str] = None

class Employee(BaseModel):
    id: str
    name: str
    role: str
    department: str
    daily_wage: float
    productivity: float
    morale: float
    hired_day: int
    status: str

class Loan(BaseModel):
    id: str
    principal: float
    outstanding_balance: float
    daily_interest_rate: float
    daily_repayment: float
    taken_day: int
    status: str

class MarketingCampaign(BaseModel):
    id: str
    name: str
    target_product_id: Optional[str] = None
    channel: str
    daily_budget: float
    effectiveness_multiplier: float
    demand_boost_pct: float
    started_day: int
    status: str

class RdProject(BaseModel):
    id: str
    name: str
    target_product_id: Optional[str] = None
    daily_budget: float
    progress: float
    target_quality_gain: float
    status: str
    started_day: int
    completed_day: Optional[int] = None

class GameSettings(BaseModel):
    mode: str = "sandbox"
    difficulty: str = "normal"
    campaign_goal: str = "VALUATION_TARGET"
    campaign_target_value: float = 50000.0
    campaign_deadline_days: int = 180
    game_state: str = "RUNNING"
    win_loss_reason: Optional[str] = None
    starting_cash_multiplier: float = 1.0
    demand_multiplier: float = 1.0
    cost_multiplier: float = 1.0
    event_frequency_multiplier: float = 1.0

from simcorp.models.ai_schemas import AIDecisionRecord

class FullGameState(BaseModel):
    company: CompanyState
    clock: GameClock
    cash_balance: float
    products: List[Product]
    latest_snapshot: Optional[DailySnapshot] = None
    historical_snapshots: List[DailySnapshot] = []
    recent_transactions: List[LedgerEntry] = []
    recent_activities: List[ActivityLogItem] = []
    ai_decisions: List[AIDecisionRecord] = []
    employees: List[Employee] = []
    active_loans: List[Loan] = []
    active_campaigns: List[MarketingCampaign] = []
    rd_projects: List[RdProject] = []
    game_settings: GameSettings = Field(default_factory=GameSettings)
    daily_fixed_opex: float = 50.0


class NewGameRequest(BaseModel):
    company_name: str = Field(default="Apex Dynamics", min_length=2, max_length=50)
    starting_cash: float = Field(default=10000.0)
    initial_product_name: str = Field(default="Apex Micro-Sensor")
    initial_product_price: float = Field(default=120.0, gt=0)
    initial_product_cost: float = Field(default=45.0, gt=0)
    initial_daily_target: int = Field(default=15, ge=0)
    mode: str = Field(default="sandbox", pattern="^(sandbox|campaign)$")
    difficulty: str = Field(default="normal", pattern="^(easy|normal|hard|brutal)$")
    campaign_goal: str = Field(default="VALUATION_TARGET", pattern="^(VALUATION_TARGET|CASH_TARGET)$")
    campaign_target_value: float = Field(default=50000.0, gt=0)
    campaign_deadline_days: int = Field(default=180, gt=0)

class ClockControlRequest(BaseModel):
    action: str = Field(..., pattern="^(pause|resume|set_speed|step)$")
    speed_seconds: Optional[float] = Field(None, gt=0.1, le=10.0)

class UpdateProductRequest(BaseModel):
    selling_price: Optional[float] = Field(None, gt=0)
    daily_production_target: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(ACTIVE|DISCONTINUED)$")

class HireEmployeeRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    role: str = Field(..., pattern="^(ENGINEER|MARKETER|SALES|MANAGER|RESEARCHER)$")
    department: str = Field(..., pattern="^(PRODUCTION|MARKETING|RD|ADMIN)$")
    daily_wage: float = Field(default=20.0, gt=0, le=500.0)

class TakeLoanRequest(BaseModel):
    principal: float = Field(..., gt=0, le=100000.0)
    daily_interest_rate: float = Field(default=0.002, ge=0.0005, le=0.01)
    daily_repayment: float = Field(default=0.0, ge=0)

class StartCampaignRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    target_product_id: Optional[str] = None
    channel: str = Field(default="DIGITAL", pattern="^(DIGITAL|PRINT|EVENTS|DIRECT)$")
    daily_budget: float = Field(default=30.0, gt=0, le=5000.0)

class StartRdProjectRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    target_product_id: Optional[str] = None
    daily_budget: float = Field(default=50.0, gt=0, le=5000.0)
    target_quality_gain: float = Field(default=10.0, gt=0, le=40.0)


class AIAgent(BaseModel):
    id: str
    name: str
    title: str
    department: str
    level: int
    supervisor_id: Optional[str] = None
    specialization: str
    allowed_tasks: List[str] = []
    permissions: Dict[str, Any] = {}
    current_status: str
    current_objective: str
    performance_score: float = 100.0
    tasks_completed: int = 0
    tasks_failed: int = 0


class AITask(BaseModel):
    id: str
    title: str
    description: str
    department: str
    task_type: str
    assigned_agent_id: str
    supervisor_id: str
    priority: str
    status: str
    created_day: int
    deadline_day: int
    deliverable: Optional[Dict[str, Any]] = None
    recommendation_action: Optional[Dict[str, Any]] = None
    review_status: str
    review_feedback: Optional[str] = None
    revision_count: int = 0
    blocked_reason: Optional[str] = None


class AITaskReview(BaseModel):
    id: str
    task_id: str
    reviewer_agent_id: str
    decision: str
    feedback: str
    score: float
    day: int


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=5, max_length=500)
    department: str
    task_type: str
    assigned_agent_id: str
    supervisor_id: str
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|URGENT)$")
    deadline_day: int = Field(default=5, ge=1)

