"""
Controller class for SimCorp simulation, bridging the backend engine and AI orchestrator 
with the PySide6 native UI.
"""
from __future__ import annotations
import threading
import time
from pathlib import Path
from typing import List, Dict, Any

from simcorp.engine.simulation import SimulationEngine
from simcorp.engine.db import get_db_connection
from simcorp.ai.orchestrator import AIOrchestrator
from simcorp.ai.client import LMStudioClient
from simcorp.models.schemas import (
    FullGameState,
    NewGameRequest,
    ClockControlRequest,
    UpdateProductRequest,
    HireEmployeeRequest,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "simcorp.db"

class SimCorpController:
    def __init__(self):
        self.engine = SimulationEngine(db_path=str(DB_PATH))
        self.ai_orchestrator = AIOrchestrator(db_path=str(DB_PATH))
        self._stop_clock = False
        self._clock_thread: threading.Thread | None = None

    def start_app(self):
        """Initialize the app state and start background tasks."""
        state = self.engine.get_full_state()
        if not state.get("company") or not state.get("products"):
            self.create_new_game(
                company_name="Default Corp",
                starting_cash=100000,
                initial_product_name="Product A",
                initial_product_price=50,
                initial_product_cost=20,
                initial_daily_target=10,
                mode="Standard",
                difficulty="Normal",
                campaign_goal="Profitability",
                campaign_target_value=1000000,
                campaign_deadline_days=365,
            )
        
        # Start the background clock loop in a separate thread
        self._stop_clock = False
        self._clock_thread = threading.Thread(target=self._simulation_clock_loop, daemon=True)
        self._clock_thread.start()

    def stop_app(self):
        """Stop background tasks."""
        self._stop_clock = True
        if self._clock_thread:
            self._clock_thread.join(timeout=2.0)

    def _simulation_clock_loop(self):
        """Background thread advancing days when clock is unpaused."""
        while not self._stop_clock:
            try:
                state = self.engine.get_full_state()
                clock = state["clock"]
                if not clock["is_paused"]:
                    self.engine.advance_day()
                    new_state = self.engine.get_full_state()
                    # Run AI cycles (blocking call in thread is fine)
                    self.ai_orchestrator.run_management_cycle(new_state)
                time.sleep(clock["tick_speed_seconds"])
            except Exception as e:
                print(f"[Clock Loop Error]: {e}")
                time.sleep(2.0)

    # --- Game State & Control ---

    def get_game_state(self) -> FullGameState:
        return self.engine.get_full_state()

    def create_new_game(self, req: NewGameRequest) -> Dict[str, Any]:
        self.engine.create_new_game(
            company_name=req.company_name,
            starting_cash=req.starting_cash,
            initial_product_name=req.initial_product_name,
            initial_product_price=req.initial_product_price,
            initial_product_cost=req.initial_product_cost,
            initial_daily_target=req.initial_daily_target,
            mode=req.mode,
            difficulty=req.difficulty,
            campaign_goal=req.campaign_goal,
            campaign_target_value=req.campaign_target_value,
            campaign_deadline_days=req.campaign_deadline_days,
        )
        return {"status": "success", "message": f"Company '{req.company_name}' created.", "state": self.engine.get_full_state()}

    def control_clock(self, req: ClockControlRequest) -> Dict[str, Any]:
        if req.action == "pause":
            updated = self.engine.set_clock_state(is_paused=True)
        elif req.action == "resume":
            updated = self.engine.set_clock_state(is_paused=False)
        elif req.action == "set_speed":
            if req.speed_seconds is None:
                raise ValueError("speed_seconds required for set_speed")
            updated = self.engine.set_clock_state(speed_seconds=req.speed_seconds)
        elif req.action == "step":
            res = self.engine.advance_day()
            return {"status": "success", "action": "step", "day_result": res, "clock": self.engine.get_full_state()["clock"]}
        else:
            raise ValueError("Unknown action")
        return {"status": "success", "clock": updated}

    def update_product(self, product_id: str, req: UpdateProductRequest) -> Dict[str, Any]:
        success = self.engine.update_product(
            product_id=product_id,
            price=req.selling_price,
            target=req.daily_production_target,
            status=req.status
        )
        if not success:
            raise ValueError(f"Product {product_id} not found")
        return {"status": "success", "product_id": product_id}

    # --- AI Management ---

    def get_ai_config(self) -> Dict[str, Any]:
        return self.ai_orchestrator.get_config()

    def update_ai_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        self.ai_orchestrator.save_config(cfg)
        return {"status": "success", "config": cfg}

    def check_ai_health(self) -> Dict[str, Any]:
        cfg = self.ai_orchestrator.get_config()
        client = LMStudioClient(cfg)
        return client.check_health()

    def trigger_ai_review_now(self) -> Dict[str, Any]:
        state = self.engine.get_full_state()
        decisions = self.ai_orchestrator.run_management_cycle(state, force=True)
        return {"status": "success", "decisions_count": len(decisions), "decisions": decisions}

    def approve_ai_decision(self, decision_id: str) -> Dict[str, Any]:
        success = self.ai_orchestrator.approve_decision(decision_id)
        if not success:
            raise ValueError("Cannot approve decision (not pending or not found)")
        return {"status": "success", "decision_id": decision_id}

    def reject_ai_decision(self, decision_id: str) -> Dict[str, Any]:
        success = self.ai_orchestrator.reject_decision(decision_id)
        if not success:
            raise ValueError("Cannot reject decision (not pending or not found)")
        return {"status": "success", "decision_id": decision_id}

    # --- HR & Employees ---

    def list_employees(self) -> List[Dict[str, Any]]:
        conn = get_db_connection(DB_PATH)
        rows = conn.execute("SELECT * FROM employees WHERE status = 'ACTIVE';").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def hire_employee(self, req: HireEmployeeRequest) -> Dict[str, Any]:
        conn = get_db_connection(DB_PATH)
        day_row = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
        current_day = day_row["current_day"] if day_row else 1
        emp_id = f"emp_{uuid.uuid4().hex[:8]}"
        with conn:
            conn.execute(
                """INSERT INTO employees (id, name, role, department, daily_wage, productivity, morale, hired_day, status)
                   VALUES (?, ?, ?, ?, ?, 1.0, 75.0, ?, 'ACTIVE');""",
                (emp_id, req.name, req.role, req.department, req.daily_wage, current_day)
            )
            conn.execute(
                "INSERT INTO activity_log (day, category, severity, message) VALUES (?, 'HR', 'SUCCESS', ?);",
                (current_day, f"Hired {req.role} '{req.name}' at {req.daily_wage:.0f} cr/day.")
            )
        conn.close()
        return {"status": "success", "employee_id": emp_id}
