"""FastAPI REST server exposing the simulation state and control endpoints."""
from __future__ import annotations
import asyncio
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from simcorp.engine.simulation import SimulationEngine
from simcorp.engine.db import get_db_connection, close_db_connection
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
from simcorp.api.resources import get_project_root, get_data_dir, verify_frontend_available, get_app_data_path

# Security: Restrict CORS to local frontend origins only
app = FastAPI(
    title="SimCorp Simulation API",
    description="Authoritative local backend for SimCorp business simulation",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "Origin"],
)

# Simple token-based authentication for state-changing operations
SIMCORP_API_TOKEN = os.environ.get("SIMCORP_API_TOKEN", "dev-token-change-in-production")


def get_db_connection_safe():
    """Get database connection with proper error handling."""
    try:
        return get_db_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "simcorp.db"
engine = SimulationEngine(db_path=DB_PATH)
ai_orchestrator = AIOrchestrator(db_path=str(DB_PATH))

# Track background tasks per game session to prevent stale writes
active_background_tasks: dict[str, set[asyncio.Task]] = {}


def get_game_session_id() -> str | None:
    """Extract game session ID from request headers or generate new one."""
    # In a real implementation, this would come from auth token or session cookie
    return None  # For now, we'll use a simple approach


async def verify_auth(request: Request) -> bool:
    """Verify authentication for state-changing operations."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header[7:]  # Remove "Bearer " prefix
    return token == SIMCORP_API_TOKEN


@app.middleware("http")
async def security_middleware(request: Request, call_next) -> Response:
    """Add security middleware for all requests."""
    try:
        response = await call_next(request)
        
        # Don't expose internal errors to clients
        if response.status_code >= 500:
            response = JSONResponse(
                content={"detail": "Internal server error"},
                status_code=response.status_code
            )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.get("/api/health")
def health_check():
    """Health check endpoint - no auth required."""
    return {"status": "ok", "service": "simcorp-engine", "version": "0.1.0"}

app = FastAPI(
    title="SimCorp Simulation API",
    description="Authoritative local backend for SimCorp business simulation",
    version="0.1.0"
)

# Security: Restrict CORS to local frontend origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "file:///w:/Github_projects/Simcorp/desktop/dist"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "Origin"],
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
                # Run AI executive management review cycle and workforce cycle sequentially
                new_state = engine.get_full_state()
                await asyncio.to_thread(ai_orchestrator.run_management_cycle, new_state)
                await asyncio.to_thread(task_manager.execute_daily_workforce_cycle, engine, new_state)
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
    """Get current game state - read-only, no auth required."""
    return engine.get_full_state()

@app.post("/api/new-game")
async def create_new_game(req: NewGameRequest):
    """Create a new game session. Requires authentication for state-changing operations."""
    if not await verify_auth(None):  # Simplified - in production would use request param
        raise HTTPException(status_code=401, detail="Authentication required")
    
    engine.create_new_game(
        company_name=req.company_name,
        starting_cash=max(req.starting_cash, 1000),  # Validate: minimum 1000 cr
        initial_product_name=req.initial_product_name or "Product A",
        initial_product_price=max(req.initial_product_price, 10.0) if req.initial_product_price else 10.0,  # Validate: positive price
        initial_product_cost=max(0, min(req.initial_product_cost, req.initial_product_price - 1)) if req.initial_product_cost else 5.0,  # Validate: cost < price, non-negative
        initial_daily_target=req.initial_daily_target or 10,
        mode=req.mode or "normal",
        difficulty=req.difficulty or "normal",
        campaign_goal=req.campaign_goal or None,
        campaign_target_value=req.campaign_target_value or None,
        campaign_deadline_days=req.campaign_deadline_days or None,
    )
    return {"status": "success", "message": f"Company '{req.company_name}' created.", "state": engine.get_full_state()}

@app.post("/api/clock/control")
async def control_clock(req: ClockControlRequest):
    """Control simulation clock. Requires authentication for state-changing operations."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if req.action == "pause":
        updated = engine.set_clock_state(is_paused=True)
    elif req.action == "resume":
        updated = engine.set_clock_state(is_paused=False)
    elif req.action == "set_speed":
        if req.speed_seconds is None or req.speed_seconds <= 0:
            raise HTTPException(status_code=400, detail="speed_seconds must be a positive number")
        updated = engine.set_clock_state(speed_seconds=req.speed_seconds)
    elif req.action == "step":
        res = engine.advance_day()
        return {"status": "success", "action": "step", "day_result": res, "clock": engine.get_full_state()["clock"]}
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    return {"status": "success", "clock": updated}

@app.post("/api/products/{product_id}")
async def update_product_parameters(product_id: str, req: UpdateProductRequest):
    """Update product parameters. Requires authentication for state-changing operations."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate inputs
    price = max(req.selling_price or 0, 10.0)  # Minimum price of 10 cr
    target = req.daily_production_target or 10
    
    success = engine.update_product(
        product_id=product_id,
        price=price,
        target=target,
        status=req.status or "active"
    )
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return {"status": "success", "product_id": product_id}

@app.get("/api/ai/config", response_model=AIConfigModel)
def get_ai_config():
    """Get AI configuration - read-only."""
    return ai_orchestrator.get_config()

@app.post("/api/ai/config")
async def update_ai_config(cfg: AIConfigModel):
    """Update AI configuration. Requires authentication for state-changing operations."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    ai_orchestrator.save_config(cfg)
    return {"status": "success", "config": cfg}

@app.get("/api/ai/health", response_model=AIHealthStatus)
def check_ai_health():
    """Check AI service health - read-only."""
    cfg = ai_orchestrator.get_config()
    client = LMStudioClient(cfg)
    return client.check_health()

@app.post("/api/ai/review-now")
async def trigger_ai_review_now():
    """Trigger immediate AI review. Requires authentication for state-changing operations."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    state = engine.get_full_state()
    decisions = ai_orchestrator.run_management_cycle(state, force=True)
    return {"status": "success", "decisions_count": len(decisions), "decisions": decisions}

@app.post("/api/ai/decisions/{decision_id}/approve")
async def approve_ai_decision(decision_id: str):
    """Approve AI decision. Requires authentication for state-changing operations."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    success = ai_orchestrator.approve_decision(decision_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot approve decision (not pending or not found)")
    return {"status": "success", "decision_id": decision_id}

@app.post("/api/ai/decisions/{decision_id}/reject")
async def reject_ai_decision(decision_id: str):
    """Reject AI decision. Requires authentication for state-changing operations."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    success = ai_orchestrator.reject_decision(decision_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot reject decision (not pending or not found)")
    return {"status": "success", "decision_id": decision_id}

# ---- HR: Employees --------------------------------------------------------

@app.get("/api/employees")
def list_employees():
    """List employees - read-only."""
    conn = get_db_connection(DB_PATH)
    rows = conn.execute("SELECT * FROM employees WHERE status = 'ACTIVE';").fetchall()
    conn.close()
    return {"employees": [dict(r) for r in rows]}

@app.post("/api/employees/hire")
async def hire_employee(req: HireEmployeeRequest):
    """Hire employee - requires authentication."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate inputs
    name = req.name.strip() if req.name else None
    role = req.role or "General Employee"
    department = req.department or "General"
    daily_wage = max(req.daily_wage or 50, 10)  # Minimum wage of 10 cr
    
    conn = get_db_connection(DB_PATH)
    day = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
    current_day = day["current_day"] if day else 1
    emp_id = f"emp_{uuid.uuid4().hex[:8]}"
    with conn:
        conn.execute(
            """INSERT INTO employees (id, name, role, department, daily_wage, productivity, morale, hired_day, status)
               VALUES (?, ?, ?, ?, ?, 1.0, 75.0, ?, 'ACTIVE');""",
            (emp_id, name, role, department, daily_wage, current_day)
        )
        conn.execute(
            "INSERT INTO activity_log (day, category, severity, message) VALUES (?, 'HR', 'SUCCESS', ?);",
            (current_day, f"Hired {role} '{name}' at {daily_wage:.0f} cr/day.")
        )
    conn.close()
    return {"status": "success", "employee_id": emp_id}

@app.post("/api/employees/{employee_id}/fire")
async def fire_employee(employee_id: str):
    """Fire employee - requires authentication."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
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
    """List loans - read-only."""
    conn = get_db_connection(DB_PATH)
    rows = conn.execute("SELECT * FROM loans;").fetchall()
    conn.close()
    return {"loans": [dict(r) for r in rows]}

@app.post("/api/loans/take")
async def take_loan(req: TakeLoanRequest):
    """Take a loan - requires authentication."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate inputs
    principal = max(req.principal or 0, 1000)  # Minimum loan of 1000 cr
    daily_interest_rate = req.daily_interest_rate or 0.05  # Default 5% per day
    
    conn = get_db_connection(DB_PATH)
    day = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
    current_day = day["current_day"] if day else 1
    loan_id = f"loan_{uuid.uuid4().hex[:8]}"
    
    # Check available cash constraint (simplified - in production would check ledger)
    state = engine.get_full_state()
    current_cash = state.get("cash", {}).get("balance", 0)
    
    with conn:
        conn.execute(
            """INSERT INTO loans (id, principal, outstanding_balance, daily_interest_rate, daily_repayment, taken_day, status)
               VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE');""",
            (loan_id, principal, principal, daily_interest_rate, max(principal * 0.1, 10), current_day)
        )
        # Credit proceeds to ledger
        new_balance = round(current_cash + principal, 2)
        tx_id = f"tx_{current_day}_{uuid.uuid4().hex[:6]}"
        conn.execute(
            """INSERT INTO ledger (id, day, category, amount, balance_after, reference_id, description)
               VALUES (?, ?, 'LOAN_PROCEEDS', ?, ?, ?, ?);""",
            (tx_id, current_day, principal, new_balance, loan_id, f"Loan proceeds: {principal:.0f} cr at {daily_interest_rate*100:.2f}%/day")
        )
        conn.execute(
            "INSERT INTO activity_log (day, category, severity, message) VALUES (?, 'FINANCE', 'INFO', ?);",
            (current_day, f"Loan of {principal:.0f} cr taken at {daily_interest_rate*100:.2f}%/day interest.")
        )
    conn.close()
    return {"status": "success", "loan_id": loan_id}

# ---- Marketing: Campaigns -------------------------------------------------

@app.get("/api/campaigns")
def list_campaigns():
    """List campaigns - read-only."""
    conn = get_db_connection(DB_PATH)
    rows = conn.execute("SELECT * FROM marketing_campaigns;").fetchall()
    conn.close()
    return {"campaigns": [dict(r) for r in rows]}

@app.post("/api/campaigns/start")
async def start_campaign(req: StartCampaignRequest):
    """Start a marketing campaign - requires authentication."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate inputs
    name = req.name.strip() if req.name else None
    channel = req.channel or "social_media"
    daily_budget = max(req.daily_budget or 50, 10)  # Minimum budget of 10 cr
    
    conn = get_db_connection(DB_PATH)
    day = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
    current_day = day["current_day"] if day else 1
    camp_id = f"camp_{uuid.uuid4().hex[:8]}"
    
    with conn:
        conn.execute(
            """INSERT INTO marketing_campaigns (id, name, target_product_id, channel, daily_budget, effectiveness_multiplier, demand_boost_pct, started_day, status)
               VALUES (?, ?, ?, ?, ?, 1.0, 0.0, ?, 'ACTIVE');""",
            (camp_id, name, req.target_product_id or None, channel, daily_budget, current_day)
        )
        conn.execute(
            "INSERT INTO activity_log (day, category, severity, message) VALUES (?, 'MARKETING', 'SUCCESS', ?);",
            (current_day, f"Campaign '{name}' launched on {channel} at {daily_budget:.0f} cr/day.")
        )
    conn.close()
    return {"status": "success", "campaign_id": camp_id}

@app.post("/api/campaigns/{campaign_id}/end")
async def end_campaign(campaign_id: str):
    """End a campaign - requires authentication."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    conn = get_db_connection(DB_PATH)
    with conn:
        conn.execute("UPDATE marketing_campaigns SET status = 'ENDED' WHERE id = ?;", (campaign_id,))
    conn.close()
    return {"status": "success", "campaign_id": campaign_id}

# ---- R&D: Projects --------------------------------------------------------

@app.get("/api/rd-projects")
def list_rd_projects():
    """List R&D projects - read-only."""
    conn = get_db_connection(DB_PATH)
    rows = conn.execute("SELECT * FROM rd_projects;").fetchall()
    conn.close()
    return {"rd_projects": [dict(r) for r in rows]}

@app.post("/api/rd-projects/start")
async def start_rd_project(req: StartRdProjectRequest):
    """Start an R&D project - requires authentication."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate inputs
    name = req.name.strip() if req.name else None
    daily_budget = max(req.daily_budget or 50, 10)  # Minimum budget of 10 cr
    target_quality_gain = req.target_quality_gain or 10
    
    conn = get_db_connection(DB_PATH)
    day = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
    current_day = day["current_day"] if day else 1
    proj_id = f"rd_{uuid.uuid4().hex[:8]}"
    
    with conn:
        conn.execute(
            """INSERT INTO rd_projects (id, name, target_product_id, daily_budget, progress, target_quality_gain, status, started_day)
               VALUES (?, ?, ?, ?, 0.0, ?, 'ACTIVE', ?);""",
            (proj_id, name, req.target_product_id or None, daily_budget, target_quality_gain, current_day)
        )
        conn.execute(
            "INSERT INTO activity_log (day, category, severity, message) VALUES (?, 'RESEARCH', 'INFO', ?);",
            (current_day, f"R&D project '{name}' started at {daily_budget:.0f} cr/day, targeting +{target_quality_gain:.0f} quality.")
        )
    conn.close()
    return {"status": "success", "project_id": proj_id}

@app.post("/api/rd-projects/{project_id}/cancel")
async def cancel_rd_project(project_id: str):
    """Cancel an R&D project - requires authentication."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
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
async def get_ai_agent_detail(agent_id: str):
    agent = task_manager.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    tasks = task_manager.get_tasks(agent_id=agent_id)
    return {
        "agent": agent,
        "tasks": tasks
    }

@app.get("/api/ai/tasks")
async def get_ai_tasks(status: str | None = None, agent_id: str | None = None):
    """Lists company tasks with optional filters."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return task_manager.get_tasks(status=status, agent_id=agent_id)

@app.post("/api/ai/tasks")
async def create_ai_task(req: CreateTaskRequest):
    """Allows manual or managerial assignment of a task to an agent."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate inputs
    title = req.title.strip() if req.title else None
    description = req.description.strip() if req.description else None
    
    state = engine.get_full_state()
    current_day = state["clock"]["current_day"]
    task_id = task_manager.create_task(
        title=title,
        description=description,
        department=req.department or "General",
        task_type=req.task_type or "general",
        assigned_agent_id=req.assigned_agent_id or None,
        supervisor_id=req.supervisor_id or None,
        priority=req.priority or 50,
        deadline_day=req.deadline_day or current_day + 7,
        created_day=current_day
    )
    return {"status": "success", "task_id": task_id}

@app.get("/api/ai/work-overview")
async def get_ai_work_overview():
    """Returns company-wide task distribution, bottlenecks, and review activity."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return task_manager.get_work_overview()

@app.post("/api/ai/workforce/cycle")
async def run_workforce_cycle():
    """Manually triggers a full agent workflow cycle (specialist -> manager -> CEO -> execution)."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    state = engine.get_full_state()
    res = task_manager.execute_daily_workforce_cycle(sim_engine=engine, sim_state=state)
    return res

# ---- Game Settings --------------------------------------------------------

@app.get("/api/settings")
async def get_game_settings():
    """Get game settings - requires authentication."""
    if not await verify_auth(None):
        raise HTTPException(status_code=401, detail="Authentication required")
    
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
    async def serve_spa(full_path: str):
        """SPA fallback - serves index.html for client-side routes."""
        if not await verify_auth(None):
            raise HTTPException(status_code=401, detail="Authentication required")
        
        file_path = frontend_dist_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # SPA fallback - serve index.html for any unknown route
        return FileResponse(frontend_dist_dir / "index.html")

