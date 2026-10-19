"""Regression tests for starting a clean game."""
from pathlib import Path

from simcorp.engine.db import get_db_connection
from simcorp.engine.simulation import SimulationEngine


def test_new_game_clears_previous_ai_tasks_and_reviews(tmp_path: Path):
    engine = SimulationEngine(db_path=tmp_path / "reset.db", seed=123)
    engine.create_new_game(company_name="First Company")

    conn = get_db_connection(engine.db_path)
    with conn:
        conn.execute(
            """INSERT INTO ai_tasks (
                id, title, description, department, task_type,
                assigned_agent_id, supervisor_id, created_day, deadline_day
            ) VALUES ('task_old', 'Old task', 'Old game work', 'OPERATIONS',
                      'ANALYSIS', 'agent_1', 'agent_manager', 1, 3);"""
        )
        conn.execute(
            """INSERT INTO ai_task_reviews (
                id, task_id, reviewer_agent_id, decision, feedback, day
            ) VALUES ('review_old', 'task_old', 'agent_manager',
                      'APPROVED', 'Old game review', 1);"""
        )
    conn.close()

    engine.create_new_game(company_name="Second Company")

    conn = get_db_connection(engine.db_path)
    task_count = conn.execute("SELECT COUNT(*) FROM ai_tasks;").fetchone()[0]
    review_count = conn.execute("SELECT COUNT(*) FROM ai_task_reviews;").fetchone()[0]
    conn.close()

    assert task_count == 0
    assert review_count == 0
    assert engine.get_full_state()["company"]["name"] == "Second Company"
