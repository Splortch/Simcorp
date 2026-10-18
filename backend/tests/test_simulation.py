"""Tests for the SimCorp economic simulation engine and ledger."""
import pytest
from pathlib import Path
from simcorp.engine.simulation import SimulationEngine
from simcorp.engine.db import get_db_connection

@pytest.fixture
def test_engine(tmp_path: Path):
    db_file = tmp_path / "test_simcorp.db"
    engine = SimulationEngine(db_path=db_file, seed=123)
    engine.create_new_game(
        company_name="Apex Test Corp",
        starting_cash=10000.0,
        initial_product_name="Test Widget",
        initial_product_price=100.0,
        initial_product_cost=40.0,
        initial_daily_target=10
    )
    return engine

def test_initial_company_state(test_engine: SimulationEngine):
    state = test_engine.get_full_state()
    assert state["company"]["name"] == "Apex Test Corp"
    assert state["cash_balance"] == 10000.0
    assert state["clock"]["current_day"] == 1
    assert len(state["products"]) == 1
    prod = state["products"][0]
    assert prod["name"] == "Test Widget"
    assert prod["selling_price"] == 100.0
    assert prod["production_cost"] == 40.0
    assert prod["inventory_units"] == 20

def test_advance_day_executes_transactions(test_engine: SimulationEngine):
    # Day 1 -> Day 2
    res = test_engine.advance_day()
    assert res["day"] == 2
    assert "cash_balance" in res
    assert res["revenue"] >= 0
    assert res["cogs"] >= 0
    assert res["opex"] == 50.0

    state = test_engine.get_full_state()
    assert state["clock"]["current_day"] == 2
    assert len(state["recent_transactions"]) > 0

    # Ensure ledger integrity: cash_balance matches last transaction balance_after
    conn = get_db_connection(test_engine.db_path)
    last_tx = conn.execute("SELECT balance_after FROM ledger ORDER BY rowid DESC LIMIT 1;").fetchone()
    conn.close()
    assert round(state["cash_balance"], 2) == round(float(last_tx["balance_after"]), 2)

def test_no_negative_inventory_on_sales(test_engine: SimulationEngine):
    # Set price very low to maximize demand, target to 0 so no new inventory is made
    test_engine.update_product("prod_001", price=10.0, target=0)
    for _ in range(5):
        test_engine.advance_day()
    
    state = test_engine.get_full_state()
    prod = state["products"][0]
    assert prod["inventory_units"] >= 0

def test_cash_depletion_stops_production(test_engine: SimulationEngine):
    # Drain cash by recording large OPEX manually
    conn = get_db_connection(test_engine.db_path)
    with conn:
        test_engine.record_transaction(conn, 1, "OPEX", -9990.0, "Forced Test Drain")
    conn.close()

    assert test_engine.get_full_state()["cash_balance"] == 10.0

    # Unit cost is 40.0, but cash is only 10.0 -> production must be 0
    test_engine.update_product("prod_001", target=50)
    test_engine.advance_day()

    state = test_engine.get_full_state()
    # Check that warning activity was logged
    warnings = [a for a in state["recent_activities"] if a["category"] == "OPERATIONS"]
    assert any("curtailed" in w["message"] for w in warnings)
