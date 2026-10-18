"""Tests for LM Studio integration, AI orchestrator, and fallback policies."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from simcorp.engine.simulation import SimulationEngine
from simcorp.ai.orchestrator import AIOrchestrator
from simcorp.models.ai_schemas import AIConfigModel, ManagerProposal, ManagerAction

@pytest.fixture
def ai_test_setup(tmp_path: Path):
    db_file = tmp_path / "test_ai.db"
    engine = SimulationEngine(db_path=db_file, seed=42)
    engine.create_new_game(
        company_name="Apex Neural Corp",
        starting_cash=10000.0,
        initial_product_name="Neural Processor",
        initial_product_price=120.0,
        initial_product_cost=50.0,
        initial_daily_target=10
    )
    orchestrator = AIOrchestrator(db_path=str(db_file))
    return engine, orchestrator

def test_ai_rule_based_fallback_execution(ai_test_setup):
    engine, orchestrator = ai_test_setup

    # Advance a day to generate sales history
    engine.advance_day()
    state = engine.get_full_state()

    # Trigger management review cycle (with LM Studio simulated unavailable)
    with patch("simcorp.ai.client.LMStudioClient.request_decision", return_value=None):
        decisions = orchestrator.run_management_cycle(state, force=True)
        assert len(decisions) > 0
        dec = decisions[0]
        assert "Rule-based Fallback" in dec.reasoning
        assert dec.status == "EXECUTED"

def test_lm_studio_mocked_proposal_execution(ai_test_setup):
    engine, orchestrator = ai_test_setup

    state = engine.get_full_state()
    mock_proposal = ManagerProposal(
        manager="ceo",
        summary="Raising prices to capture higher margin",
        confidence=0.9,
        actions=[
            ManagerAction(
                type="adjust_price",
                product_id="prod_001",
                price=135.0,
                reason="Demand elasticity is favorable."
            ),
            ManagerAction(
                type="set_production_target",
                product_id="prod_001",
                target=25,
                reason="Scaling production batch."
            )
        ]
    )

    with patch("simcorp.ai.client.LMStudioClient.request_decision", return_value=mock_proposal):
        decisions = orchestrator.run_management_cycle(state, force=True)
        assert len(decisions) == 2
        assert all(d.status == "EXECUTED" for d in decisions)

        # Confirm changes applied in database
        updated_state = engine.get_full_state()
        prod = updated_state["products"][0]
        assert prod["selling_price"] == 135.0
        assert prod["daily_production_target"] == 25

def test_oversight_approval_mode(ai_test_setup):
    engine, orchestrator = ai_test_setup

    # Set oversight mode
    cfg = orchestrator.get_config()
    cfg.autonomy_mode = "oversight"
    orchestrator.save_config(cfg)

    state = engine.get_full_state()
    mock_proposal = ManagerProposal(
        manager="ceo",
        summary="Proposing price adjustment needing player consent",
        confidence=0.85,
        actions=[
            ManagerAction(
                type="adjust_price",
                product_id="prod_001",
                price=150.0,
                reason="Testing oversight approval."
            )
        ]
    )

    with patch("simcorp.ai.client.LMStudioClient.request_decision", return_value=mock_proposal):
        decisions = orchestrator.run_management_cycle(state, force=True)
        assert len(decisions) == 1
        dec = decisions[0]
        assert dec.status == "PENDING"

        # Price shouldn't have changed yet
        assert engine.get_full_state()["products"][0]["selling_price"] == 120.0

        # Player approves
        approved = orchestrator.approve_decision(dec.id)
        assert approved is True
        assert engine.get_full_state()["products"][0]["selling_price"] == 150.0
