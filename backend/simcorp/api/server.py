"""FastAPI REST server exposing the simulation state and control endpoints."""
from __future__ import annotations
import asyncio
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from simcorp.engine.simulation import SimulationEngine
from simcorp.engine.db import get_db_connection
from simcorp.models.schemas import (
    FullGameState,
    NewGameRequest,
    ClockControlRequest,
    UpdateProductRequest,
    HireEmployeeRequest,
    TakeLoanRequest,
    StartCampaignRequest,
    StartRdProjectRequest,
)

from simcorp.ai.orchestrator import AIOrchestrator
from simcorp.ai.client import LMStudioClient
from simcorp.models.ai_schemas import AIConfigModel, AIHealthStatus

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "simcorp.db"
engine = SimulationEngine(db_path=DB_PATH)
ai_orchestrator = AIOrchestrator(db_path=str(DB_PATH))

app = FastAPI(
    title="SimCorp Simulation API",
    description="Authoritative local backend for SimCorp business simulation",
    version="0.1.0"
)

# Enable CORS for local desktop UI / dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background tick loop task reference
clock_task: asyncio.Task | None = None

async def simulation_clock_loop():
    """Background task advancing days when clock is unpaused."""
    while True:
        try:
            state = engine.get_full_state()
            clock = state["clock"]
            if not clock["is_paused"]:
                engine.advance_day()
                # Run AI executive management review cycle
                new_state = engine.get_full_state()
                # Execute asynchronously to not block the clock interval
                asyncio.create_task(asyncio.to_thread(ai_orchestrator.run_management_cycle, new_state))
                asyncio.create_task(asyncio.to_thread(task_manager.execute_daily_workforce_cycle, engine, new_state))
            await asyncio.sleep(clock["tick_speed_seconds"])
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Clock Loop Error]: {e}")
            await asyncio.sleep(2.0)

@app.on_event("startup")
async def startup_event():
    global clock_task
    # Ensure database is primed
    state = engine.get_full_state()
    if not state.get("company") or not state.get("products"):
        engine.create_new_game()
    clock_task = asyncio.create_task(simulation_clock_loop())

@app.on_event("shutdown")
async def shutdown_event():
    global clock_task
    if clock_task:
        clock_task.cancel()

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "simcorp-engine", "version": "0.1.0"}

@app.get("/api/state", response_model=FullGameState)
def get_game_state():
    return engine.get_full_state()

@app.post("/api/new-game")
def create_new_game(req: NewGameRequest):
    engine.create_new_game(
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
    return {"status": "success", "message": f"Company '{req.company_name}' created.", "state": engine.get_full_state()}

@app.post("/api/clock/control")
def control_clock(req: ClockControlRequest):
    if req.action == "pause":
        updated = engine.set_clock_state(is_paused=True)
    elif req.action == "resume":
        updated = engine.set_clock_state(is_paused=False)
    elif req.action == "set_speed":
        if req.speed_seconds is None:
            raise HTTPException(status_code=400, detail="speed_seconds required for set_speed")
        updated = engine.set_clock_state(speed_seconds=req.speed_seconds)
    elif req.action == "step":
        res = engine.advance_day()
        return {"status": "success", "action": "step", "day_result": res, "clock": engine.get_full_state()["clock"]}
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    return {"status": "success", "clock": updated}

@app.post("/api/products/{product_id}")
def update_product_parameters(product_id: str, req: UpdateProductRequest):
    success = engine.update_product(
        product_id=product_id,
        price=req.selling_price,
        target=req.daily_production_target,
        status=req.status
    )
    if not success:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return {"status": "success", "product_id": product_id}

@app.get("/api/ai/config", response_model=AIConfigModel)
def get_ai_config():
    return ai_orchestrator.get_config()

@app.post("/api/ai/config")
def update_ai_config(cfg: AIConfigModel):
    ai_orchestrator.save_config(cfg)
    return {"status": "success", "config": cfg}

@app.get("/api/ai/health", response_model=AIHealthStatus)
def check_ai_health():
    cfg = ai_orchestrator.get_config()
    client = LMStudioClient(cfg)
    return client.check_health()

@app.post("/api/ai/review-now")
def trigger_ai_review_now():
    state = engine.get_full_state()
    decisions = ai_orchestrator.run_management_cycle(state, force=True)
    return {"status": "success", "decisions_count": len(decisions), "decisions": decisions}

@app.post("/api/ai/decisions/{decision_id}/approve")
def approve_ai_decision(decision_id: str):
    success = ai_orchestrator.approve_decision(decision_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot approve decision (not pending or not found)")
    return {"status": "success", "decision_id": decision_id}

@app.post("/api/ai/decisions/{decision_id}/reject")
def reject_ai_decision(decision_id: str):
    success = ai_orchestrator.reject_decision(decision_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot reject decision (not pending or not found)")
    return {"status": "success", "decision_id": decision_id}

# ---- HR: Employees --------------------------------------------------------

@app.get("/api/employees")
def list_employees():
    conn = get_db_connection(DB_PATH)
    rows = conn.execute("SELECT * FROM employees WHERE status = 'ACTIVE';").fetchall()
    conn.close()
    return {"employees": [dict(r) for r in rows]}

@app.post("/api/employees/hire")
def hire_employee(req: HireEmployeeRequest):
    conn = get_db_connection(DB_PATH)
    day = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
    current_day = day["current_day"] if day else 1
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

@app.post("/api/employees/{employee_id}/fire")
def fire_employee(employee_id: str):
    conn = get_db_connection(DB_PATH)
    day = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
    current_day = day["current_day"] if day else 1
    emp = conn.execute("SELECT * FROM employees WHERE id = ?;", (employee_id,)).fetchone()
    if not emp:
        conn.close()
        raise HTTPException(status_code=404, detail="Employee not found")
    with conn:
        conn.execute("UPDATE employees SET status = 'LAID_OFF' WHERE id = ?;", (employee_id,))
        conn.execute(
            "INSERT INTO activity_log (day, category, severity, message) VALUES (?, 'HR', 'WARNING', ?);",
            (current_day, f"Laid off {emp['role']} '{emp['name']}'.")
        )
    conn.close()
    return {"status": "success", "employee_id": employee_id}

# ---- Finance: Loans -------------------------------------------------------

@app.get("/api/loans")
def list_loans():
    conn = get_db_connection(DB_PATH)
    rows = conn.execute("SELECT * FROM loans;").fetchall()
    conn.close()
    return {"loans": [dict(r) for r in rows]}

@app.post("/api/loans/take")
def take_loan(req: TakeLoanRequest):
    conn = get_db_connection(DB_PATH)
    day = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
    current_day = day["current_day"] if day else 1
    loan_id = f"loan_{uuid.uuid4().hex[:8]}"
    with conn:
        conn.execute(
            """INSERT INTO loans (id, principal, outstanding_balance, daily_interest_rate, daily_repayment, taken_day, status)
               VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE');""",
            (loan_id, req.principal, req.principal, req.daily_interest_rate, req.daily_repayment, current_day)
        )
        # Credit proceeds to ledger
        current_cash = engine.get_current_cash(conn)
        new_balance = round(current_cash + req.principal, 2)
        tx_id = f"tx_{current_day}_{uuid.uuid4().hex[:6]}"
        conn.execute(
            """INSERT INTO ledger (id, day, category, amount, balance_after, reference_id, description)
               VALUES (?, ?, 'LOAN_PROCEEDS', ?, ?, ?, ?);""",
            (tx_id, current_day, req.principal, new_balance, loan_id, f"Loan proceeds: {req.principal:.0f} cr at {req.daily_interest_rate*100:.2f}%/day")
        )
        conn.execute(
            "INSERT INTO activity_log (day, category, severity, message) VALUES (?, 'FINANCE', 'INFO', ?);",
            (current_day, f"Loan of {req.principal:.0f} cr taken at {req.daily_interest_rate*100:.2f}%/day interest.")
        )
    conn.close()
    return {"status": "success", "loan_id": loan_id}

# ---- Marketing: Campaigns -------------------------------------------------

@app.get("/api/campaigns")
def list_campaigns():
    conn = get_db_connection(DB_PATH)
    rows = conn.execute("SELECT * FROM marketing_campaigns;").fetchall()
    conn.close()
    return {"campaigns": [dict(r) for r in rows]}

@app.post("/api/campaigns/start")
def start_campaign(req: StartCampaignRequest):
    conn = get_db_connection(DB_PATH)
    day = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
    current_day = day["current_day"] if day else 1
    camp_id = f"camp_{uuid.uuid4().hex[:8]}"
    with conn:
        conn.execute(
            """INSERT INTO marketing_campaigns (id, name, target_product_id, channel, daily_budget, effectiveness_multiplier, demand_boost_pct, started_day, status)
               VALUES (?, ?, ?, ?, ?, 1.0, 0.0, ?, 'ACTIVE');""",
            (camp_id, req.name, req.target_product_id, req.channel, req.daily_budget, current_day)
        )
        conn.execute(
            "INSERT INTO activity_log (day, category, severity, message) VALUES (?, 'MARKETING', 'SUCCESS', ?);",
            (current_day, f"Campaign '{req.name}' launched on {req.channel} at {req.daily_budget:.0f} cr/day.")
        )
    conn.close()
    return {"status": "success", "campaign_id": camp_id}

@app.post("/api/campaigns/{campaign_id}/end")
def end_campaign(campaign_id: str):
    conn = get_db_connection(DB_PATH)
    with conn:
        conn.execute("UPDATE marketing_campaigns SET status = 'ENDED' WHERE id = ?;", (campaign_id,))
    conn.close()
    return {"status": "success", "campaign_id": campaign_id}

# ---- R&D: Projects --------------------------------------------------------

@app.get("/api/rd-projects")
def list_rd_projects():
    conn = get_db_connection(DB_PATH)
    rows = conn.execute("SELECT * FROM rd_projects;").fetchall()
    conn.close()
    return {"rd_projects": [dict(r) for r in rows]}

@app.post("/api/rd-projects/start")
def start_rd_project(req: StartRdProjectRequest):
    conn = get_db_connection(DB_PATH)
    day = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
    current_day = day["current_day"] if day else 1
    proj_id = f"rd_{uuid.uuid4().hex[:8]}"
    with conn:
        conn.execute(
            """INSERT INTO rd_projects (id, name, target_product_id, daily_budget, progress, target_quality_gain, status, started_day)
               VALUES (?, ?, ?, ?, 0.0, ?, 'ACTIVE', ?);""",
            (proj_id, req.name, req.target_product_id, req.daily_budget, req.target_quality_gain, current_day)
        )
        conn.execute(
            "INSERT INTO activity_log (day, category, severity, message) VALUES (?, 'RESEARCH', 'INFO', ?);",
            (current_day, f"R&D project '{req.name}' started at {req.daily_budget:.0f} cr/day, targeting +{req.target_quality_gain:.0f} quality.")
        )
    conn.close()
    return {"status": "success", "project_id": proj_id}

@app.post("/api/rd-projects/{project_id}/cancel")
def cancel_rd_project(project_id: str):
    conn = get_db_connection(DB_PATH)
    with conn:
        conn.execute("UPDATE rd_projects SET status = 'CANCELLED' WHERE id = ?;", (project_id,))
    conn.close()
    return {"status": "success", "project_id": project_id}

from simcorp.ai.tasks import TaskWorkflowManager
from simcorp.models.schemas import CreateTaskRequest

task_manager = TaskWorkflowManager(db_path=DB_PATH)
task_manager.initialize_workforce()

# ---- AI Workforce, Agents, and Hierarchy ----------------------------------

@app.get("/api/ai/agents")
def get_ai_agents():
    """Returns the full AI organizational hierarchy and specialist profiles."""
    return task_manager.get_agents()

@app.get("/api/ai/agents/{agent_id}")
def get_ai_agent_detail(agent_id: str):
    agent = task_manager.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    tasks = task_manager.get_tasks(agent_id=agent_id)
    return {
        "agent": agent,
        "tasks": tasks
    }

@app.get("/api/ai/tasks")
def get_ai_tasks(status: str | None = None, agent_id: str | None = None):
    """Lists company tasks with optional filters."""
    return task_manager.get_tasks(status=status, agent_id=agent_id)

@app.post("/api/ai/tasks")
def create_ai_task(req: CreateTaskRequest):
    """Allows manual or managerial assignment of a task to an agent."""
    state = engine.get_full_state()
    current_day = state["clock"]["current_day"]
    task_id = task_manager.create_task(
        title=req.title,
        description=req.description,
        department=req.department,
        task_type=req.task_type,
        assigned_agent_id=req.assigned_agent_id,
        supervisor_id=req.supervisor_id,
        priority=req.priority,
        deadline_day=req.deadline_day,
        created_day=current_day
    )
    return {"status": "success", "task_id": task_id}

@app.get("/api/ai/work-overview")
def get_ai_work_overview():
    """Returns company-wide task distribution, bottlenecks, and review activity."""
    return task_manager.get_work_overview()

@app.post("/api/ai/workforce/cycle")
def run_workforce_cycle():
    """Manually triggers a full agent workflow cycle (specialist -> manager -> CEO -> execution)."""
    state = engine.get_full_state()
    res = task_manager.execute_daily_workforce_cycle(sim_engine=engine, sim_state=state)
    return res

# ---- Game Settings --------------------------------------------------------

@app.get("/api/settings")
def get_game_settings():
    conn = get_db_connection(DB_PATH)
    row = conn.execute("SELECT * FROM game_settings WHERE id = 1;").fetchone()
    conn.close()
    if not row:
        return {"mode": "sandbox", "difficulty": "normal", "game_state": "RUNNING"}
    return dict(row)


# Mount static frontend production build if available
frontend_dist_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        base_dir = frontend_dist_dir.resolve()
        requested = Path(full_path)

        # Reject absolute paths and traversal attempts from user input.
        if requested.is_absolute() or ".." in requested.parts:
            return FileResponse(base_dir / "index.html")

        file_path = (base_dir / requested).resolve()
        try:
            file_path.relative_to(base_dir)
        except ValueError:
            return FileResponse(base_dir / "index.html")

        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(base_dir / "index.html")

