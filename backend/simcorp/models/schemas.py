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

class ActivityLogItem(BaseModel):
    id: int
    day: int
    category: str
    severity: str
    message: str
    details_json: Optional[str] = None
    created_at: Optional[str] = None

class FullGameState(BaseModel):
    company: CompanyState
    clock: GameClock
    cash_balance: float
    products: List[Product]
    latest_snapshot: Optional[DailySnapshot] = None
    historical_snapshots: List[DailySnapshot] = []
    recent_transactions: List[LedgerEntry] = []
    recent_activities: List[ActivityLogItem] = []
    daily_fixed_opex: float = 50.0

class NewGameRequest(BaseModel):
    company_name: str = Field(default="Apex Dynamics", min_length=2, max_length=50)
    starting_cash: float = Field(default=10000.0)
    initial_product_name: str = Field(default="Apex Micro-Sensor")
    initial_product_price: float = Field(default=120.0, gt=0)
    initial_product_cost: float = Field(default=45.0, gt=0)
    initial_daily_target: int = Field(default=15, ge=0)

class ClockControlRequest(BaseModel):
    action: str = Field(..., pattern="^(pause|resume|set_speed|step)$")
    speed_seconds: Optional[float] = Field(None, gt=0.1, le=10.0)

class UpdateProductRequest(BaseModel):
    selling_price: Optional[float] = Field(None, gt=0)
    daily_production_target: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(ACTIVE|DISCONTINUED)$")
