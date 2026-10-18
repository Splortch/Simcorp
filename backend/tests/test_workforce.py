"""Unit tests for the AI Workforce Hierarchy and Task Workflow."""
import pytest
import tempfile
import os
from simcorp.engine.simulation import SimulationEngine
from simcorp.ai.tasks import TaskWorkflowManager


@pytest.fixture
def isolated_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    engine = SimulationEngine(db_path=db_path)
    engine.create_new_game(company_name="TestCorp", starting_cash=15000.0)
    tm = TaskWorkflowManager(db_path=db_path)
    tm.initialize_workforce()

    yield engine, tm, db_path

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


def test_workforce_seeding(isolated_env):
    engine, tm, db_path = isolated_env
    agents = tm.get_agents()
    assert len(agents) >= 9
    ceo = next(a for a in agents if a["id"] == "agent_ceo")
    assert ceo["level"] == 0
    assert ceo["department"] == "EXECUTIVE"

    cfo = next(a for a in agents if a["id"] == "agent_cfo")
    assert cfo["supervisor_id"] == "agent_ceo"
    assert cfo["level"] == 1


def test_task_creation_and_execution_cycle(isolated_env):
    engine, tm, db_path = isolated_env
    state = engine.get_full_state()

    # Create a production task
    task_id = tm.create_task(
        title="Production Target Test",
        description="Calculate optimal target",
        department="OPERATIONS",
        task_type="CALCULATE_OPTIMAL_TARGET",
        assigned_agent_id="agent_spec_production",
        supervisor_id="agent_coo",
        priority="HIGH"
    )

    tasks = tm.get_tasks()
    assert any(t["id"] == task_id for t in tasks)

    # Run cycle 1: Specialist analyzes & submits deliverable to supervisor
    cycle1 = tm.execute_daily_workforce_cycle(sim_engine=engine, sim_state=state)
    assert cycle1["processed_tasks"] > 0

    t1 = next(t for t in tm.get_tasks() if t["id"] == task_id)
    # Delivered and escalated to manager/CEO
    assert t1["status"] in ("AWAITING_REVIEW", "AWAITING_APPROVAL", "COMPLETED")
    assert t1["deliverable"] is not None

    # Run cycle 2: Escalated to CEO (AWAITING_APPROVAL)
    cycle2 = tm.execute_daily_workforce_cycle(sim_engine=engine, sim_state=state)
    t2 = next(t for t in tm.get_tasks() if t["id"] == task_id)
    assert t2["status"] in ("AWAITING_APPROVAL", "COMPLETED")

    # Run cycle 3: CEO signs off and executes into simulation
    cycle3 = tm.execute_daily_workforce_cycle(sim_engine=engine, sim_state=state)
    overview = tm.get_work_overview()
    assert overview["completed"] >= 1
    t3 = next(t for t in tm.get_tasks() if t["id"] == task_id)
    assert t3["status"] == "COMPLETED"

