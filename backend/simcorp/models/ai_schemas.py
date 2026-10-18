"""Data schemas for AI actions, proposals, and configuration."""
from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class ManagerAction(BaseModel):
    type: Literal["adjust_price", "set_production_target", "pause_production", "resume_production"]
    product_id: str
    price: Optional[float] = Field(None, gt=0, le=10000)
    target: Optional[int] = Field(None, ge=0, le=1000)
    reason: str = Field(..., min_length=3, max_length=250)

class ManagerProposal(BaseModel):
    manager: Literal["ceo", "operations", "cfo", "marketing"]
    summary: str
    actions: List[ManagerAction]
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

class AIDecisionRecord(BaseModel):
    id: str
    day: int
    manager_role: str
    action_type: str
    parameters_json: str
    reasoning: str
    confidence: float
    status: str # PENDING, APPROVED, REJECTED, EXECUTED, FAILED
    result_summary: Optional[str] = None
    created_at: Optional[str] = None

class AIConfigModel(BaseModel):
    enabled: bool = True
    provider: str = "lm_studio"
    base_url: str = "http://localhost:1234/v1"
    model_id: str = "google/gemma-4-e4b"
    autonomy_mode: Literal["autonomous", "oversight", "player_approval"] = "autonomous"
    review_frequency_days: int = Field(default=2, ge=1, le=10)
    timeout_seconds: float = Field(default=45.0, gt=1.0, le=180.0)

class AIHealthStatus(BaseModel):
    connected: bool
    provider: str
    base_url: str
    model_id: str
    models_available: List[str] = []
    error_message: Optional[str] = None
