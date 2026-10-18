"""AI Task and Workforce Management Service.

Handles:
- Task creation, delegation down the hierarchy.
- Execution of analytical tasks (deterministic calculations + LLM reasoning).
- Supervisor review, scoring, revisions, and executive escalation.
- Execution of approved recommendations into the simulation engine.
"""
from __future__ import annotations
import json
import uuid
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path
from simcorp.engine.db import get_db_connection
from simcorp.ai.hierarchy import seed_ai_agents
from simcorp.ai.client import LMStudioClient


class TaskWorkflowManager:
    def __init__(self, db_path: Path | str = "simcorp.db"):
        self.db_path = str(db_path)

    def initialize_workforce(self) -> None:
        """Ensures the standard agent workforce exists in SQLite."""
        conn = get_db_connection(self.db_path)
        with conn:
            seed_ai_agents(conn)
        conn.close()

    def get_agents(self) -> List[Dict[str, Any]]:
        """Returns all agents with parsed JSON fields."""
        conn = get_db_connection(self.db_path)
        rows = conn.execute("SELECT * FROM ai_agents ORDER BY level ASC, department ASC;").fetchall()
        conn.close()

        agents = []
        for r in rows:
            a = dict(r)
            a["allowed_tasks"] = json.loads(a.get("allowed_tasks_json") or "[]")
            a["permissions"] = json.loads(a.get("permissions_json") or "{}")
            agents.append(a)
        return agents

    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single agent by ID."""
        conn = get_db_connection(self.db_path)
        row = conn.execute("SELECT * FROM ai_agents WHERE id = ?;", (agent_id,)).fetchone()
        conn.close()
        if not row:
            return None
        a = dict(row)
        a["allowed_tasks"] = json.loads(a.get("allowed_tasks_json") or "[]")
        a["permissions"] = json.loads(a.get("permissions_json") or "{}")
        return a

    def get_tasks(self, status: Optional[str] = None, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves tasks with optional status or agent filter."""
        conn = get_db_connection(self.db_path)
        query = "SELECT * FROM ai_tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if agent_id:
            query += " AND (assigned_agent_id = ? OR supervisor_id = ?)"
            params.extend([agent_id, agent_id])
        query += " ORDER BY created_day DESC, id DESC LIMIT 50;"
        rows = conn.execute(query, tuple(params)).fetchall()
        conn.close()

        tasks = []
        for r in rows:
            t = dict(r)
            t["deliverable"] = json.loads(t.get("deliverable_json") or "null")
            t["recommendation_action"] = json.loads(t.get("recommendation_action_json") or "null")
            tasks.append(t)
        return tasks

    def get_work_overview(self) -> Dict[str, Any]:
        """Provides company-wide workforce statistics."""
        conn = get_db_connection(self.db_path)
        rows = conn.execute("SELECT status, COUNT(*) AS count FROM ai_tasks GROUP BY status;").fetchall()
        counts = {r["status"]: r["count"] for r in rows}

        active_count = conn.execute("SELECT COUNT(*) AS c FROM ai_tasks WHERE status IN ('IN_PROGRESS', 'ASSIGNED');").fetchone()["c"]
        awaiting_review = counts.get("AWAITING_REVIEW", 0)
        awaiting_approval = counts.get("AWAITING_APPROVAL", 0)
        blocked_count = counts.get("BLOCKED", 0)
        completed_count = counts.get("COMPLETED", 0)
        failed_count = counts.get("FAILED", 0)

        # Recent 10 reviews
        rev_rows = conn.execute("SELECT * FROM ai_task_reviews ORDER BY id DESC LIMIT 10;").fetchall()
        reviews = [dict(r) for r in rev_rows]
        conn.close()

        return {
            "tasks_in_progress": active_count,
            "awaiting_review": awaiting_review,
            "awaiting_approval": awaiting_approval,
            "blocked": blocked_count,
            "completed": completed_count,
            "failed": failed_count,
            "status_counts": counts,
            "recent_reviews": reviews,
        }

    def create_task(
        self,
        title: str,
        description: str,
        department: str,
        task_type: str,
        assigned_agent_id: str,
        supervisor_id: str,
        priority: str = "MEDIUM",
        deadline_day: int = 5,
        created_day: int = 1,
    ) -> str:
        """Creates and stores a new work task assigned to an agent."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        conn = get_db_connection(self.db_path)
        with conn:
            conn.execute(
                """INSERT INTO ai_tasks (
                    id, title, description, department, task_type,
                    assigned_agent_id, supervisor_id, priority, status,
                    created_day, deadline_day, review_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ASSIGNED', ?, ?, 'PENDING');""",
                (
                    task_id, title, description, department, task_type,
                    assigned_agent_id, supervisor_id, priority,
                    created_day, deadline_day
                )
            )
            # Update agent status to WORKING
            conn.execute(
                "UPDATE ai_agents SET current_status = 'WORKING' WHERE id = ?;",
                (assigned_agent_id,)
            )
        conn.close()
        return task_id

    def process_subordinate_task(self, task: Dict[str, Any], sim_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specialist execution: produces deterministic analyses, forecasts, and actionable recommendations.
        """
        agent_id = task["assigned_agent_id"]
        task_type = task["task_type"]
        products = sim_state.get("products", [])
        cash = sim_state.get("cash_balance", 0.0)
        current_day = sim_state.get("clock", {}).get("current_day", 1)

        deliverable = {}
        action = None

        if agent_id == "agent_spec_production" or task_type == "CALCULATE_OPTIMAL_TARGET":
            # Match production with recent sales demand, factoring inventory
            p = products[0] if products else None
            if p:
                sold_yesterday = p.get("units_sold_last_day", 0)
                inv = p.get("inventory_units", 0)
                unmet = p.get("unmet_demand_last_day", 0)
                # Calculate buffer: target demand + unmet - 50% of current unsold inventory
                optimal = max(5, int(sold_yesterday + unmet * 0.8 - inv * 0.3))
                deliverable = {
                    "product_id": p["id"],
                    "current_inventory": inv,
                    "units_sold_last_day": sold_yesterday,
                    "unmet_demand": unmet,
                    "recommended_daily_target": optimal,
                    "methodology": "Demand-matching inventory buffer algorithm"
                }
                action = {
                    "type": "set_production_target",
                    "product_id": p["id"],
                    "target": optimal,
                    "reason": f"Adjust daily production to {optimal} units to match demand ({sold_yesterday} sold, {unmet} unmet, {inv} in stock)."
                }

        elif agent_id == "agent_spec_pricing" or task_type == "PRICE_ELASTICITY_STUDY":
            # Pricing specialist evaluates margins and elasticity
            p = products[0] if products else None
            if p:
                cost = p.get("production_cost", 45.0)
                current_price = p.get("selling_price", 120.0)
                unmet = p.get("unmet_demand_last_day", 0)
                inv = p.get("inventory_units", 0)
                
                # If high unmet demand and zero stock, price can rise; if high unsold stock, price lowers slightly
                if unmet > 5 and inv < 5:
                    recommended_price = round(current_price * 1.05, 2)
                    reason = f"High excess demand ({unmet} unmet units). Raising price to capture consumer surplus."
                elif inv > 40:
                    recommended_price = round(max(cost * 1.5, current_price * 0.95), 2)
                    reason = f"High inventory buildup ({inv} units). Trimming price to accelerate turnover."
                else:
                    recommended_price = current_price
                    reason = "Price is currently well-balanced relative to demand elasticity and margins."

                deliverable = {
                    "product_id": p["id"],
                    "current_price": current_price,
                    "recommended_price": recommended_price,
                    "unit_cost": cost,
                    "estimated_margin_pct": round(((recommended_price - cost) / recommended_price) * 100, 1),
                }
                if recommended_price != current_price:
                    action = {
                        "type": "adjust_price",
                        "product_id": p["id"],
                        "price": recommended_price,
                        "reason": reason
                    }

        elif agent_id == "agent_spec_cashflow" or task_type == "CASHFLOW_PROJECTION":
            # Cash flow specialist forecasts runway
            latest_snap = sim_state.get("latest_snapshot") or {}
            cogs = latest_snap.get("cogs", 0.0)
            opex = latest_snap.get("operating_expenses", 50.0)
            daily_burn = cogs + opex
            runway_days = round(cash / max(daily_burn, 1.0), 1)

            deliverable = {
                "liquid_cash": cash,
                "estimated_daily_burn": round(daily_burn, 2),
                "runway_days": runway_days,
                "solvency_risk": "HIGH" if runway_days < 7 else ("MODERATE" if runway_days < 20 else "LOW"),
            }
            # If severe risk, recommend taking emergency credit or lowering production
            if runway_days < 5 and cash < 2000:
                action = {
                    "type": "pause_production",
                    "product_id": products[0]["id"] if products else "prod_001",
                    "reason": f"CRITICAL: Cash runway is only {runway_days} days. Pausing production to preserve liquidity."
                }

        elif agent_id == "agent_spec_rd" or task_type == "QUALITY_GAP_ANALYSIS":
            p = products[0] if products else None
            if p:
                q = p.get("quality", 50.0)
                deliverable = {
                    "product_id": p["id"],
                    "current_quality": q,
                    "benchmark_target": 80.0,
                    "quality_gap": max(0.0, 80.0 - q),
                    "recommendation": "Initiate incremental calibration R&D project once cash reserves exceed 15,000 cr."
                }

        else:
            deliverable = {
                "summary": f"Completed routine task {task_type}.",
                "agent_id": agent_id,
                "day": current_day
            }

        return {"deliverable": deliverable, "action": action}

    def review_and_escalate_task(
        self,
        task_id: str,
        reviewer_id: str,
        current_day: int,
        sim_engine: Any,
    ) -> Dict[str, Any]:
        """
        Supervisor checks subordinate work against company objectives and constraints.
        - If approved and minor: executes immediately.
        - If approved and major/executive: escalates to CEO (Level 0).
        - If flawed: requests revision (up to limit of 2).
        """
        conn = get_db_connection(self.db_path)
        task_row = conn.execute("SELECT * FROM ai_tasks WHERE id = ?;", (task_id,)).fetchone()
        if not task_row:
            conn.close()
            return {"error": "Task not found"}

        task = dict(task_row)
        action = json.loads(task.get("recommendation_action_json") or "null")
        deliverable = json.loads(task.get("deliverable_json") or "{}")
        revision_count = task.get("revision_count", 0)

        # Quality Assurance validation
        passed_qa = True
        rejection_reason = ""

        if action:
            # Check sanity constraints
            if action.get("type") == "adjust_price" and action.get("price", 0) <= 0:
                passed_qa = False
                rejection_reason = "Price must be strictly positive."
            if action.get("type") == "set_production_target" and action.get("target", 0) < 0:
                passed_qa = False
                rejection_reason = "Production target cannot be negative."

        review_id = f"rev_{uuid.uuid4().hex[:8]}"

        if not passed_qa and revision_count < 2:
            # Request revision
            with conn:
                conn.execute(
                    """UPDATE ai_tasks SET
                        status = 'REVISION_REQUESTED',
                        review_status = 'REVISION_REQUESTED',
                        review_feedback = ?,
                        revision_count = revision_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;""",
                    (f"Supervisor Revision Request: {rejection_reason}", task_id)
                )
                conn.execute(
                    """INSERT INTO ai_task_reviews (id, task_id, reviewer_agent_id, decision, feedback, score, day)
                       VALUES (?, ?, ?, 'REVISION_REQUESTED', ?, 60.0, ?);""",
                    (review_id, task_id, reviewer_id, rejection_reason, current_day)
                )
                conn.execute("UPDATE ai_agents SET current_status = 'ANALYZING' WHERE id = ?;", (task["assigned_agent_id"],))
            conn.close()
            return {"status": "REVISION_REQUESTED", "feedback": rejection_reason}

        # If it has an action and reviewer is department manager (level 1), escalate to CEO for executive sign-off
        reviewer = self.get_agent_by_id(reviewer_id)
        is_manager = reviewer and reviewer.get("level") == 1

        if is_manager and action:
            with conn:
                conn.execute(
                    """UPDATE ai_tasks SET
                        status = 'AWAITING_APPROVAL',
                        review_status = 'ESCALATED',
                        review_feedback = 'Manager approved deliverable; escalated to CEO for final execution authorization.',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;""",
                    (task_id,)
                )
                conn.execute(
                    """INSERT INTO ai_task_reviews (id, task_id, reviewer_agent_id, decision, feedback, score, day)
                       VALUES (?, ?, ?, 'ESCALATED', 'Validated by Department Manager and forwarded to Executive Leadership.', 95.0, ?);""",
                    (review_id, task_id, reviewer_id, current_day)
                )
                conn.execute("UPDATE ai_agents SET current_status = 'AWAITING_APPROVAL' WHERE id = ?;", (task["assigned_agent_id"],))
            conn.close()
            return {"status": "ESCALATED", "message": "Escalated to CEO"}

        # Full Approval and Execution (by CEO or direct non-escalated work)
        with conn:
            conn.execute(
                """UPDATE ai_tasks SET
                    status = 'COMPLETED',
                    review_status = 'APPROVED',
                    review_feedback = 'Executive authorization granted and completed.',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;""",
                (task_id,)
            )
            conn.execute(
                """INSERT INTO ai_task_reviews (id, task_id, reviewer_agent_id, decision, feedback, score, day)
                   VALUES (?, ?, ?, 'APPROVED', 'Deliverable fully approved and executed.', 100.0, ?);""",
                (review_id, task_id, reviewer_id, current_day)
            )
            # Update agent metrics
            conn.execute(
                """UPDATE ai_agents SET
                    current_status = 'IDLE',
                    tasks_completed = tasks_completed + 1,
                    performance_score = MIN(100.0, performance_score + 1.0)
                WHERE id = ?;""",
                (task["assigned_agent_id"],)
            )

            # Record in ai_decisions & execute through simulation engine if actionable
            if action:
                decision_id = f"dec_agent_{uuid.uuid4().hex[:8]}"
                action_type = action.get("type", "unknown")
                conn.execute(
                    """INSERT INTO ai_decisions (
                        id, day, manager_role, action_type, parameters_json, reasoning, confidence, status, result_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, 0.95, 'EXECUTED', 'Executed via Hierarchical AI Workflow');""",
                    (
                        decision_id,
                        current_day,
                        reviewer.get("title", "Executive Leadership") if reviewer else "AI Workforce",
                        action_type,
                        json.dumps(action),
                        action.get("reason", "Approved hierarchical task deliverable"),
                    )
                )
                # Log to activity log
                conn.execute(
                    """INSERT INTO activity_log (day, category, severity, message, details_json)
                       VALUES (?, 'AI', 'SUCCESS', ?, ?);""",
                    (
                        current_day,
                        f"AI Workflow Executed: {action_type} for product {action.get('product_id')}",
                        json.dumps(action)
                    )
                )

        conn.close()

        # Apply action in simulation engine
        if action and sim_engine:
            if action["type"] == "adjust_price":
                sim_engine.update_product(action["product_id"], price=float(action["price"]))
            elif action["type"] == "set_production_target":
                sim_engine.update_product(action["product_id"], target=int(action["target"]))
            elif action["type"] == "pause_production":
                sim_engine.update_product(action["product_id"], status="PAUSED")
            elif action["type"] == "resume_production":
                sim_engine.update_product(action["product_id"], status="ACTIVE")

        return {"status": "COMPLETED", "action": action}

    def execute_daily_workforce_cycle(self, sim_engine: Any, sim_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinates daily agent workload cycle:
        1. Ensures baseline recurring tasks exist for department specialists.
        2. Specialists analyze state and submit deliverables to supervisors.
        3. Department managers review and escalate to CEO.
        4. CEO gives final execution authorization.
        """
        self.initialize_workforce()
        current_day = sim_state.get("clock", {}).get("current_day", 1)

        # 1. Create routine analysis tasks if agents are idle
        conn = get_db_connection(self.db_path)
        active_tasks = conn.execute("SELECT COUNT(*) AS c FROM ai_tasks WHERE status IN ('ASSIGNED', 'IN_PROGRESS', 'AWAITING_REVIEW');").fetchone()["c"]
        conn.close()

        if active_tasks == 0:
            # Spawn specialized tasks for specialists
            self.create_task(
                title="Daily Production-Demand Calibration",
                description="Analyze inventory buffer and unmet demand to compute optimal daily output target.",
                department="OPERATIONS",
                task_type="CALCULATE_OPTIMAL_TARGET",
                assigned_agent_id="agent_spec_production",
                supervisor_id="agent_coo",
                priority="HIGH",
                deadline_day=current_day + 2,
                created_day=current_day
            )
            self.create_task(
                title="Price Elasticity & Margin Study",
                description="Evaluate contribution margins and market elasticity against inventory levels.",
                department="MARKETING",
                task_type="PRICE_ELASTICITY_STUDY",
                assigned_agent_id="agent_spec_pricing",
                supervisor_id="agent_cmo",
                priority="MEDIUM",
                deadline_day=current_day + 2,
                created_day=current_day
            )
            self.create_task(
                title="Cash Flow & Working Capital Runway Audit",
                description="Forecast daily burn and working capital safety runway.",
                department="FINANCE",
                task_type="CASHFLOW_PROJECTION",
                assigned_agent_id="agent_spec_cashflow",
                supervisor_id="agent_cfo",
                priority="HIGH",
                deadline_day=current_day + 2,
                created_day=current_day
            )

        # 2. Process open tasks (assigned / in progress)
        open_tasks = self.get_tasks()
        processed_count = 0

        for t in open_tasks:
            # Step A: Assigned / In Progress -> Produce deliverable and submit to supervisor
            if t["status"] in ("ASSIGNED", "IN_PROGRESS", "REVISION_REQUESTED"):
                result = self.process_subordinate_task(t, sim_state)
                conn = get_db_connection(self.db_path)
                with conn:
                    conn.execute(
                        """UPDATE ai_tasks SET
                            deliverable_json = ?,
                            recommendation_action_json = ?,
                            status = 'AWAITING_REVIEW',
                            review_status = 'SUBMITTED',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?;""",
                        (
                            json.dumps(result["deliverable"]),
                            json.dumps(result["action"]) if result["action"] else None,
                            t["id"],
                        )
                    )
                    conn.execute("UPDATE ai_agents SET current_status = 'AWAITING_REVIEW' WHERE id = ?;", (t["assigned_agent_id"],))
                conn.close()
                processed_count += 1

            # Step B: Awaiting Review -> Supervisor reviews & approves/escalates
            elif t["status"] == "AWAITING_REVIEW":
                self.review_and_escalate_task(
                    task_id=t["id"],
                    reviewer_id=t["supervisor_id"],
                    current_day=current_day,
                    sim_engine=sim_engine,
                )
                processed_count += 1

            # Step C: Awaiting Approval -> CEO gives final green light
            elif t["status"] == "AWAITING_APPROVAL":
                self.review_and_escalate_task(
                    task_id=t["id"],
                    reviewer_id="agent_ceo",
                    current_day=current_day,
                    sim_engine=sim_engine,
                )
                processed_count += 1

        return {
            "processed_tasks": processed_count,
            "day": current_day,
            "work_overview": self.get_work_overview()
        }
