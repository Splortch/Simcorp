"""Orchestrator coordinating AI decision reviews, approval policies, and execution."""
from __future__ import annotations
import json
import uuid
import sqlite3
from typing import Dict, Any, List, Optional
from simcorp.engine.db import get_db_connection
from simcorp.models.ai_schemas import (
    AIConfigModel,
    ManagerProposal,
    ManagerAction,
    AIDecisionRecord
)
from simcorp.ai.client import LMStudioClient
from simcorp.ai.prompts import (
    CEO_SYSTEM_PROMPT,
    generate_context_snapshot,
    generate_rule_based_fallback
)

class AIOrchestrator:
    def __init__(self, db_path: str = "simcorp.db"):
        self.db_path = db_path

    def get_config(self) -> AIConfigModel:
        """Loads active AI configuration from SQLite."""
        conn = get_db_connection(self.db_path)
        row = conn.execute("SELECT * FROM ai_config WHERE id = 1;").fetchone()
        conn.close()
        if not row:
            # Default configuration targeting local LM Studio
            return AIConfigModel(
                enabled=True,
                provider="lm_studio",
                base_url="http://localhost:1234/v1",
                model_id="google/gemma-4-e4b",
                autonomy_mode="autonomous",
                review_frequency_days=2,
                timeout_seconds=8.0
            )
        return AIConfigModel(
            enabled=bool(row["enabled"]),
            provider=row["provider"],
            base_url=row["base_url"],
            model_id=row["model_id"],
            autonomy_mode=row["autonomy_mode"],
            review_frequency_days=row["review_frequency_days"],
            timeout_seconds=row["timeout_seconds"]
        )

    def save_config(self, cfg: AIConfigModel) -> None:
        """Persists AI settings into SQLite."""
        conn = get_db_connection(self.db_path)
        with conn:
            conn.execute(
                """INSERT INTO ai_config (
                    id, enabled, provider, base_url, model_id, autonomy_mode, review_frequency_days, timeout_seconds
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled=excluded.enabled,
                    provider=excluded.provider,
                    base_url=excluded.base_url,
                    model_id=excluded.model_id,
                    autonomy_mode=excluded.autonomy_mode,
                    review_frequency_days=excluded.review_frequency_days,
                    timeout_seconds=excluded.timeout_seconds;""",
                (
                    1 if cfg.enabled else 0,
                    cfg.provider,
                    cfg.base_url,
                    cfg.model_id,
                    cfg.autonomy_mode,
                    cfg.review_frequency_days,
                    cfg.timeout_seconds
                )
            )
        conn.close()

    def run_management_cycle(self, state: Dict[str, Any], force: bool = False) -> List[AIDecisionRecord]:
        """Runs the management cycle: calls LM Studio or fallback, validates, and acts."""
        cfg = self.get_config()
        if not cfg.enabled:
            return []

        day = state["clock"]["current_day"]
        # Only run on configured day intervals unless forced
        if not force and (day % cfg.review_frequency_days != 0):
            return []

        client = LMStudioClient(cfg)
        snapshot_context = generate_context_snapshot(state)
        user_prompt = f"Current corporate state snapshot at Day {day}:\n{snapshot_context}\nProvide your management proposal in raw JSON."

        proposal: Optional[ManagerProposal] = None
        source_label = "LM Studio"

        # Attempt LM Studio inference first
        try:
            proposal = client.request_decision(CEO_SYSTEM_PROMPT, user_prompt)
        except Exception as err:
            print(f"[AI Cycle Error]: {err}")

        # Fallback to deterministic policy if LLM is unreachable or returned invalid JSON
        if not proposal:
            proposal = generate_rule_based_fallback(state)
            source_label = "Rule-based Fallback"

        decision_records: List[AIDecisionRecord] = []
        conn = get_db_connection(self.db_path)

        for action in proposal.actions:
            decision_id = f"dec_{day}_{uuid.uuid4().hex[:8]}"
            params_json = action.model_dump_json()

            # Autonomy check
            is_auto = cfg.autonomy_mode == "autonomous"
            status = "PENDING"
            result_summary = None

            if is_auto:
                success, msg = self._execute_action(conn, action)
                status = "EXECUTED" if success else "FAILED"
                result_summary = msg
            else:
                result_summary = "Awaiting player approval in oversight mode."

            with conn:
                conn.execute(
                    """INSERT INTO ai_decisions (
                        id, day, manager_role, action_type, parameters_json, reasoning, confidence, status, result_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    (
                        decision_id,
                        day,
                        proposal.manager,
                        action.type,
                        params_json,
                        f"[{source_label}] {action.reason}",
                        proposal.confidence,
                        status,
                        result_summary
                    )
                )

                # Log activity entry for transparency
                severity = "INFO" if status == "EXECUTED" else ("WARNING" if status == "PENDING" else "DANGER")
                conn.execute(
                    """INSERT INTO activity_log (day, category, severity, message, details_json)
                       VALUES (?, 'AI', ?, ?, ?);""",
                    (
                        day,
                        severity,
                        f"AI CEO ({source_label}): {action.type} -> {result_summary}",
                        params_json
                    )
                )

            decision_records.append(AIDecisionRecord(
                id=decision_id,
                day=day,
                manager_role=proposal.manager,
                action_type=action.type,
                parameters_json=params_json,
                reasoning=f"[{source_label}] {action.reason}",
                confidence=proposal.confidence,
                status=status,
                result_summary=result_summary
            ))

        conn.close()
        return decision_records

    def approve_decision(self, decision_id: str) -> bool:
        """Allows player to approve a pending decision in oversight mode."""
        conn = get_db_connection(self.db_path)
        row = conn.execute("SELECT * FROM ai_decisions WHERE id = ?;", (decision_id,)).fetchone()
        if not row or row["status"] != "PENDING":
            conn.close()
            return False

        action_data = json.loads(row["parameters_json"])
        action = ManagerAction(**action_data)
        success, msg = self._execute_action(conn, action)
        new_status = "EXECUTED" if success else "FAILED"

        with conn:
            conn.execute(
                "UPDATE ai_decisions SET status = ?, result_summary = ? WHERE id = ?;",
                (new_status, f"Approved by player: {msg}", decision_id)
            )
            conn.execute(
                """INSERT INTO activity_log (day, category, severity, message)
                   VALUES (?, 'AI', 'SUCCESS', ?);""",
                (row["day"], f"Player approved AI action {row['action_type']}: {msg}")
            )
        conn.close()
        return True

    def reject_decision(self, decision_id: str) -> bool:
        """Allows player to reject a pending AI decision."""
        conn = get_db_connection(self.db_path)
        row = conn.execute("SELECT * FROM ai_decisions WHERE id = ?;", (decision_id,)).fetchone()
        if not row or row["status"] != "PENDING":
            conn.close()
            return False

        with conn:
            conn.execute(
                "UPDATE ai_decisions SET status = 'REJECTED', result_summary = 'Rejected by player.' WHERE id = ?;",
                (decision_id,)
            )
        conn.close()
        return True

    def _execute_action(self, conn: sqlite3.Connection, action: ManagerAction) -> tuple[bool, str]:
        """Validates and executes the action safely within the simulation boundary."""
        prod = conn.execute("SELECT * FROM products WHERE id = ?;", (action.product_id,)).fetchone()
        if not prod:
            return False, f"Product {action.product_id} not found."

        if action.type == "adjust_price":
            if action.price is None or action.price <= 0:
                return False, "Invalid price."
            conn.execute("UPDATE products SET selling_price = ? WHERE id = ?;", (round(action.price, 2), action.product_id))
            return True, f"Updated selling price of {prod['name']} to {action.price:.2f} cr."

        elif action.type == "set_production_target":
            if action.target is None or action.target < 0:
                return False, "Invalid production target."
            conn.execute("UPDATE products SET daily_production_target = ? WHERE id = ?;", (action.target, action.product_id))
            return True, f"Set daily production target of {prod['name']} to {action.target} units/day."

        elif action.type == "pause_production":
            conn.execute("UPDATE products SET status = 'DISCONTINUED' WHERE id = ?;", (action.product_id,))
            return True, f"Paused/Discontinued line {prod['name']}."

        elif action.type == "resume_production":
            conn.execute("UPDATE products SET status = 'ACTIVE' WHERE id = ?;", (action.product_id,))
            return True, f"Resumed active production for line {prod['name']}."

        return False, f"Unsupported action {action.type}."
