"""FastAPI REST server exposing the simulation state and control endpoints."""
from __future__ import annotations
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from simcorp.engine.simulation import SimulationEngine
from simcorp.models.schemas import (
    FullGameState,
    NewGameRequest,
    ClockControlRequest,
    UpdateProductRequest
)

from simcorp.ai.orchestrator import AIOrchestrator
from simcorp.ai.client import LMStudioClient
from simcorp.models.ai_schemas import AIConfigModel, AIHealthStatus

DB_PATH = Path("simcorp.db")
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
        initial_daily_target=req.initial_daily_target
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

# Mount static frontend production build if available
frontend_dist_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = frontend_dist_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist_dir / "index.html")

