"""Simulation engine executing deterministic business days and transactions."""
from __future__ import annotations
import math
import random
import uuid
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from simcorp.engine.db import get_db_connection, initialize_database

# ---------------------------------------------------------------------------
# Difficulty presets — every multiplier is applied during advance_day().
# These tune how forgiving or punishing each scenario is.
# ---------------------------------------------------------------------------
DIFFICULTY_PRESETS: Dict[str, Dict[str, float]] = {
    "easy":   {"demand_mult": 1.30, "cost_mult": 0.80, "event_freq": 0.50, "starting_cash_mult": 1.50},
    "normal": {"demand_mult": 1.00, "cost_mult": 1.00, "event_freq": 1.00, "starting_cash_mult": 1.00},
    "hard":   {"demand_mult": 0.80, "cost_mult": 1.20, "event_freq": 1.50, "starting_cash_mult": 0.75},
    "brutal": {"demand_mult": 0.60, "cost_mult": 1.50, "event_freq": 2.00, "starting_cash_mult": 0.50},
}

# ---------------------------------------------------------------------------
# Financial distress thresholds (cash as fraction of last-day total expenses)
# ---------------------------------------------------------------------------
DISTRESS_STAGES = {
    "HEALTHY":  (float("inf"), 500.0),   # cash > 500
    "WATCH":    (500.0,  200.0),          # 200 <= cash <= 500
    "DISTRESS": (200.0,   50.0),          # 50  <= cash <= 200
    "CRITICAL": (50.0,    0.0),           # 0   <= cash <= 50
}

class SimulationEngine:
    def __init__(self, db_path: Path | str = "simcorp.db", seed: int = 42):
        self.db_path = db_path
        self.random = random.Random(seed)
        initialize_database(self.db_path)

    def create_new_game(
        self,
        company_name: str = "Apex Dynamics",
        starting_cash: float = 10000.0,
        initial_product_name: str = "Apex Micro-Sensor",
        initial_product_price: float = 120.0,
        initial_product_cost: float = 45.0,
        initial_daily_target: int = 15,
        mode: str = "sandbox",
        difficulty: str = "normal",
        campaign_goal: str = "VALUATION_TARGET",
        campaign_target_value: float = 50000.0,
        campaign_deadline_days: int = 180,
    ) -> None:
        """Initializes a brand new company with starting capital, difficulty settings, and a seed engineer."""
        preset = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS["normal"])
        effective_cash = starting_cash * preset["starting_cash_mult"]

        conn = get_db_connection(self.db_path)
        with conn:
            # Clear existing data for fresh game
            for tbl in [
                "ledger", "products", "market_segments", "market_events",
                "daily_snapshots", "ai_decisions", "activity_log", "company",
                "game_clock", "employees", "rd_projects", "marketing_campaigns",
                "loans", "game_settings", "ai_agents", "ai_tasks", "ai_task_reviews",
                "ai_decisions", # Added explicit clear for AI decisions
            ]:
                conn.execute(f"DELETE FROM {tbl};")

            company_id = "comp_001"
            conn.execute(
                "INSERT INTO company (id, name, industry, reputation) VALUES (?, ?, ?, ?);",
                (company_id, company_name, "Hardware & Electronics", 50.0)
            )

            conn.execute(
                "INSERT INTO game_clock (id, current_day, is_paused, tick_speed_seconds) VALUES (1, 1, 1, 3.0);"
            )

            # Game settings / difficulty
            conn.execute(
                """INSERT INTO game_settings (
                    id, mode, difficulty, campaign_goal, campaign_target_value,
                    campaign_deadline_days, game_state,
                    starting_cash_multiplier, demand_multiplier, cost_multiplier, event_frequency_multiplier
                ) VALUES (1, ?, ?, ?, ?, ?, 'RUNNING', ?, ?, ?, ?);""",
                (
                    mode, difficulty, campaign_goal, campaign_target_value,
                    campaign_deadline_days,
                    preset["starting_cash_mult"], preset["demand_mult"],
                    preset["cost_mult"], preset["event_freq"]
                )
            )

            # Record initial starting capital in ledger
            tx_id = f"tx_init_{uuid.uuid4().hex[:8]}"
            conn.execute(
                """INSERT INTO ledger (id, day, category, amount, balance_after, reference_id, description)
                   VALUES (?, 1, 'EQUITY_INJECTION', ?, ?, NULL, 'Initial Seed Capital');""",
                (tx_id, effective_cash, effective_cash)
            )

            # Seed default product
            prod_id = "prod_001"
            conn.execute(
                """INSERT INTO products (
                    id, name, category, status, selling_price, production_cost, quality,
                    inventory_units, daily_production_target, unmet_demand_last_day,
                    units_sold_last_day, total_units_sold, total_revenue
                ) VALUES (?, ?, 'Sensors', 'ACTIVE', ?, ?, 65.0, 20, ?, 0, 0, 0, 0.0);""",
                (prod_id, initial_product_name, initial_product_price, initial_product_cost, initial_daily_target)
            )

            # Seed default market segments
            conn.execute(
                """INSERT INTO market_segments (id, name, base_demand, price_sensitivity, quality_importance, marketing_responsiveness)
                   VALUES ('seg_sme', 'SME Hardware Integrators', 25, 0.015, 0.8, 1.2);"""
            )

            # Seed a starting engineer employee
            conn.execute(
                """INSERT INTO employees (id, name, role, department, daily_wage, productivity, morale, hired_day, status)
                   VALUES ('emp_001', 'Alex Chen', 'ENGINEER', 'PRODUCTION', 18.0, 1.1, 80.0, 1, 'ACTIVE');"""
            )

            # Log startup event
            conn.execute(
                """INSERT INTO activity_log (day, category, severity, message, details_json)
                   VALUES (1, 'SYSTEM', 'SUCCESS', ?, NULL);""",
                (f"Company '{company_name}' incorporated | {effective_cash:.0f} cr | Mode: {mode} | Difficulty: {difficulty}",)
            )

            # Record initial day 1 baseline snapshot
            inv_val = 20 * initial_product_cost
            conn.execute(
                """INSERT INTO daily_snapshots (
                    day, cash_balance, revenue, cogs, operating_expenses, net_profit,
                    total_units_sold, unmet_demand, reputation, inventory_value, total_valuation,
                    wages_paid, marketing_spend, rd_spend, headcount, distress_stage
                ) VALUES (1, ?, 0.0, 0.0, 0.0, 0.0, 0, 0, 50.0, ?, ?, 0.0, 0.0, 0.0, 1, 'HEALTHY');""",
                (effective_cash, inv_val, effective_cash + inv_val)
            )
        conn.close()

    def get_current_cash(self, conn: sqlite3.Connection) -> float:
        """Retrieves the latest cash balance directly from the authoritative ledger."""
        row = conn.execute("SELECT balance_after FROM ledger ORDER BY rowid DESC LIMIT 1;").fetchone()
        return float(row["balance_after"]) if row else 0.0

    def record_transaction(
        self,
        conn: sqlite3.Connection,
        day: int,
        category: str,
        amount: float,
        description: str,
        reference_id: Optional[str] = None
    ) -> float:
        """Records an auditable ledger entry and returns the updated cash balance."""
        current_cash = self.get_current_cash(conn)
        new_balance = round(current_cash + amount, 2)
        tx_id = f"tx_{day}_{uuid.uuid4().hex[:8]}"
        conn.execute(
            """INSERT INTO ledger (id, day, category, amount, balance_after, reference_id, description)
               VALUES (?, ?, ?, ?, ?, ?, ?);""",
            (tx_id, day, category, round(amount, 2), new_balance, reference_id, description)
        )
        return new_balance

    def calculate_product_demand(
        self,
        price: float,
        cost: float,
        quality: float,
        reputation: float,
        base_demand: int = 25
    ) -> int:
        """
        Microeconomic demand formula based on price ratio, quality, and company reputation.
        Fair price reference is ~2.5x base cost.
        """
        fair_price = cost * 2.5
        price_ratio = price / max(fair_price, 1.0)
        # Elasticity curve: demand drops sharply if overpriced, expands if discounted
        elasticity_factor = max(0.05, 1.0 - (price_ratio - 1.0) * 1.2)
        quality_factor = (quality / 50.0) * 0.5 + 0.5
        rep_factor = (reputation / 50.0) * 0.3 + 0.7
        random_market_noise = self.random.uniform(0.85, 1.15)

        raw_demand = base_demand * elasticity_factor * quality_factor * rep_factor * random_market_noise
        return max(0, int(round(raw_demand)))

    def _get_settings_multipliers(self, conn: sqlite3.Connection) -> Dict[str, float]:
        """Loads difficulty multipliers from game_settings; returns normal defaults if missing."""
        row = conn.execute("SELECT * FROM game_settings WHERE id = 1;").fetchone()
        if not row:
            return {"demand": 1.0, "cost": 1.0, "event_freq": 1.0}
        return {
            "demand": float(row["demand_multiplier"]),
            "cost":   float(row["cost_multiplier"]),
            "event_freq": float(row["event_frequency_multiplier"]),
        }

    def _classify_distress(self, cash: float) -> str:
        """Returns the financial distress stage based on cash balance."""
        if cash > 500:
            return "HEALTHY"
        elif cash > 200:
            return "WATCH"
        elif cash > 50:
            return "DISTRESS"
        else:
            return "CRITICAL"

    def _check_win_loss(self, conn: sqlite3.Connection, day: int, cash: float, valuation: float) -> None:
        """Evaluates campaign win/loss conditions and marks game_state accordingly."""
        row = conn.execute("SELECT * FROM game_settings WHERE id = 1;").fetchone()
        if not row or row["mode"] != "campaign" or row["game_state"] != "RUNNING":
            return

        goal = row["campaign_goal"]
        target = float(row["campaign_target_value"])
        deadline = int(row["campaign_deadline_days"])

        # Loss conditions
        if cash <= 0:
            conn.execute(
                "UPDATE game_settings SET game_state='LOST', win_loss_reason=? WHERE id=1;",
                ("Company became insolvent — cash balance reached zero.",)
            )
            conn.execute(
                "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                (day, "SYSTEM", "DANGER", "GAME OVER: Insolvency. Cash balance reached zero.")
            )
            return

        if day >= deadline and row["game_state"] == "RUNNING":
            # Check win before declaring deadline loss
            achieved = (goal == "VALUATION_TARGET" and valuation >= target) or \
                       (goal == "CASH_TARGET" and cash >= target)
            if not achieved:
                conn.execute(
                    "UPDATE game_settings SET game_state='LOST', win_loss_reason=? WHERE id=1;",
                    (f"Deadline reached on day {deadline} without achieving {goal} target of {target:.0f}.",)
                )
                conn.execute(
                    "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                    (day, "SYSTEM", "DANGER", f"GAME OVER: Deadline exceeded. Target was {target:.0f}.")
                )
                return

        # Win condition
        achieved = (goal == "VALUATION_TARGET" and valuation >= target) or \
                   (goal == "CASH_TARGET" and cash >= target)
        if achieved:
            conn.execute(
                "UPDATE game_settings SET game_state='WON', win_loss_reason=? WHERE id=1;",
                (f"Achieved {goal} of {target:.0f} on day {day}!",)
            )
            conn.execute(
                "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                (day, "SYSTEM", "SUCCESS", f"VICTORY: {goal} target of {target:.0f} reached on day {day}!")
            )

    def _handle_market_event(self, conn: sqlite3.Connection, day: int) -> None:
        """Checks for and applies a random market event based on difficulty multipliers."""
        mults = self._get_settings_multipliers(conn)
        event_freq = mults["event_frequency_multiplier"]

        # Event occurs if random roll is less than the frequency multiplier (e.g., 1.5x chance for hard mode)
        if self.random.uniform(0, 1) < event_freq:
            event_type = self.random.choice(["BOOM", "CRASH", "REGULATION"])
            conn.execute("INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                         (day, "SYSTEM", "INFO", f"MARKET EVENT: {event_type} detected!"));

            if event_type == "BOOM":
                # Tech Boom: Increases demand and reputation temporarily
                conn.execute("UPDATE products SET selling_price = selling_price * 1.1 WHERE id = 'prod_001';")
                conn.execute("UPDATE company SET reputation = reputation + 5 WHERE id = 'comp_001';")
                self.record_transaction(
                    conn=conn, day=day, category="MARKET", amount=0.0, description="Market Boom: Price increase and rep boost.", reference_id=None
                )
            elif event_type == "CRASH":
                # Supply Chain Shock: Increases costs and reduces demand temporarily
                conn.execute("UPDATE products SET production_cost = production_cost * 1.2 WHERE id = 'prod_001';")
                self.record_transaction(
                    conn=conn, day=day, category="MARKET", amount=0.0, description="Market Crash: Cost increase.", reference_id=None
                )
            elif event_type == "REGULATION":
                # Government Regulation: Reduces max selling price and reputation gain potential
                conn.execute("UPDATE products SET selling_price = selling_price * 0.9 WHERE id = 'prod_001';")
                self.record_transaction(
                    conn=conn, day=day, category="MARKET", amount=0.0, description="Market Regulation: Price reduction.", reference_id=None
                )

            # Log the event details in a dedicated table (assuming it exists or will be created)
            conn.execute("INSERT INTO market_events (day, type, impact_description) VALUES (?, ?, ?);",
                         (day, event_type, f"Applied {event_type} effect."))
        conn = get_db_connection(self.db_path)
        with conn:
            clock_row = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
            if not clock_row:
                self.create_new_game()
                current_day = 1
            else:
                current_day = clock_row["current_day"] + 1
                conn.execute(
                    "UPDATE game_clock SET current_day = ?, last_tick_at = CURRENT_TIMESTAMP WHERE id = 1;",
                    (current_day,)
                )

            mults = self._get_settings_multipliers(conn)
            cost_mult = mults["cost"]
            demand_mult = mults["demand"]

            comp_row = conn.execute("SELECT reputation, name FROM company WHERE id = 'comp_001';").fetchone()
            reputation = comp_row["reputation"] if comp_row else 50.0

            # ---- 1. WAGES ---------------------------------------------------
            active_employees = conn.execute(
                "SELECT * FROM employees WHERE status = 'ACTIVE';"
            ).fetchall()
            headcount = len(active_employees)
            total_wages_today = 0.0
            for emp in active_employees:
                wage = round(emp["daily_wage"] * cost_mult, 2)
                total_wages_today += wage
            if total_wages_today > 0:
                self.record_transaction(
                    conn=conn, day=current_day, category="WAGES",
                    amount=-total_wages_today,
                    description=f"Daily wages for {headcount} employee(s)"
                )

            # ---- 2. LOAN SERVICING ------------------------------------------
            active_loans = conn.execute(
                "SELECT * FROM loans WHERE status = 'ACTIVE';"
            ).fetchall()
            total_loan_cost_today = 0.0
            for loan in active_loans:
                interest = round(loan["outstanding_balance"] * loan["daily_interest_rate"], 2)
                repayment = round(loan["daily_repayment"], 2)
                payment = interest + repayment
                new_balance = round(loan["outstanding_balance"] - repayment, 2)
                total_loan_cost_today += payment
                if payment > 0:
                    # Check if we can afford the full payment before recording
                    current_cash_check = self.get_current_cash(conn)
                    if current_cash_check >= payment:
                        self.record_transaction(
                            conn=conn, day=current_day, category="LOAN_REPAYMENT",
                            amount=-payment,
                            description=f"Loan {loan['id']}: {interest:.2f} interest + {repayment:.2f} principal",
                            reference_id=loan["id"]
                        )
                        if new_balance <= 0:
                            conn.execute("UPDATE loans SET outstanding_balance=0, status='REPAID' WHERE id=?;", (loan["id"],))
                            conn.execute(
                                "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                                (current_day, "FINANCE", "SUCCESS", f"Loan {loan['id']} fully repaid!")
                            )
                        else:
                            conn.execute("UPDATE loans SET outstanding_balance=? WHERE id=?;", (new_balance, loan["id"]))
                    else:
                        # Partial payment due to insufficient funds
                        affordable = current_cash_check
                        if affordable > 0:
                            self.record_transaction(
                                conn=conn, day=current_day, category="LOAN_REPAYMENT",
                                amount=-affordable,
                                description=f"Loan {loan['id']}: Partial payment due to insufficient funds.",
                                reference_id=loan["id"]
                            )
                            # Calculate how much of the required payment was covered
                            covered_ratio = affordable / payment
                            partial_payment = round(payment * covered_ratio, 2)
                            new_balance_after_partial = round(loan["outstanding_balance"] - partial_payment, 2)

                            conn.execute("UPDATE loans SET outstanding_balance=? WHERE id=?;", (new_balance_after_partial, loan["id"]))
                            conn.execute(
                                "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                                (current_day, "FINANCE", "WARNING", f"Loan {loan['id']} only partially paid ({affordable:.2f} cr) due to insufficient funds.")
                            )
                        else:
                            conn.execute(
                                "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                                (current_day, "FINANCE", "WARNING", f"Loan {loan['id']} only partially paid ({affordable:.2f} cr) due to insufficient funds.")
                            )

            # ---- 3. R&D PROJECTS --------------------------------------------
            total_rd_spend_today = 0.0
            active_rd = conn.execute(
                "SELECT * FROM rd_projects WHERE status = 'ACTIVE';"
            ).fetchall()
            for proj in active_rd:
                rd_cost = round(proj["daily_budget"] * cost_mult, 2)
                current_cash_check = self.get_current_cash(conn)
                if current_cash_check < rd_cost:
                    conn.execute(
                        "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                        (current_day, "RESEARCH", "WARNING", f"R&D project '{proj['name']}' paused: insufficient cash.")
                    )
                    continue
                self.record_transaction(
                    conn=conn, day=current_day, category="RD",
                    amount=-rd_cost,
                    description=f"R&D: {proj['name']}",
                    reference_id=proj["id"]
                )
                total_rd_spend_today += rd_cost
                # Progress: each 100cr = ~1% progress (normalized to 100)
                progress_gain = min(rd_cost / 100.0, 2.0)
                new_progress = min(100.0, proj["progress"] + progress_gain)
                if new_progress >= 100.0 and proj["target_product_id"]:
                    # Apply quality gain to target product
                    gain = proj["target_quality_gain"]
                    conn.execute(
                        "UPDATE products SET quality = MIN(100.0, quality + ?) WHERE id = ?;",
                        (gain, proj["target_product_id"])
                    )
                    conn.execute(
                        "UPDATE rd_projects SET progress=100.0, status='COMPLETED', completed_day=? WHERE id=?;",
                        (current_day, proj["id"])
                    )
                    conn.execute(
                        "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                        (current_day, "RESEARCH", "SUCCESS",
                         f"R&D Complete: '{proj['name']}' raised product quality by +{gain:.0f} pts.")
                    )
                else:
                    conn.execute(
                        "UPDATE rd_projects SET progress=? WHERE id=?;",
                        (new_progress, proj["id"])
                    )

            # ---- 4. MARKETING DEMAND BOOST ----------------------------------
            total_marketing_spend_today = 0.0
            marketing_demand_boost = 1.0  # multiplicative
            active_campaigns = conn.execute(
                "SELECT * FROM marketing_campaigns WHERE status = 'ACTIVE';"
            ).fetchall()
            for camp in active_campaigns:
                mkt_cost = round(camp["daily_budget"] * cost_mult, 2)
                current_cash_check = self.get_current_cash(conn)
                if current_cash_check < mkt_cost:
                    conn.execute(
                        "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                        (current_day, "MARKETING", "WARNING", f"Campaign '{camp['name']}' paused: insufficient cash.")
                    )
                    continue
                self.record_transaction(
                    conn=conn, day=current_day, category="MARKETING",
                    amount=-mkt_cost,
                    description=f"Marketing: {camp['name']} ({camp['channel']})",
                    reference_id=camp["id"]
                )
                total_marketing_spend_today += mkt_cost
                # Each campaign contributes a small additive demand boost (+2-5%)
                boost = 0.02 * camp["effectiveness_multiplier"]
                marketing_demand_boost += boost

            self._handle_market_event(conn, current_day) # <-- NEW: Apply market event shocks

            # ---- 5. PRODUCTION PHASE ----------------------------------------
            active_products = conn.execute(
                "SELECT * FROM products WHERE status = 'ACTIVE';"
            ).fetchall()
            total_cogs_today = 0.0
            for prod in active_products:
                prod_id = prod["id"]
                target = prod["daily_production_target"]
                unit_cost = round(prod["production_cost"] * cost_mult, 4)
                current_cash = self.get_current_cash(conn)

                max_affordable = max(0, int(current_cash // unit_cost)) if unit_cost > 0 else target
                actual_production = min(target, max_affordable)
                prod_expense = round(actual_production * unit_cost, 2)

                if prod_expense > 0:
                    self.record_transaction(
                        conn=conn, day=current_day, category="COGS",
                        amount=-prod_expense,
                        description=f"Manufactured {actual_production} units of {prod['name']}",
                        reference_id=prod_id
                    )
                    total_cogs_today += prod_expense

                if actual_production < target:
                    conn.execute(
                        """INSERT INTO activity_log (day, category, severity, message)
                           VALUES (?, 'OPERATIONS', 'WARNING', ?);""",
                        (current_day, f"Production of {prod['name']} curtailed ({actual_production}/{target}) due to cash constraints.")
                    )

                new_inv = prod["inventory_units"] + actual_production
                conn.execute("UPDATE products SET inventory_units = ? WHERE id = ?;", (new_inv, prod_id))

            # ---- 6. DEMAND & SALES PHASE ------------------------------------
            total_revenue_today = 0.0
            total_units_sold_today = 0
            total_unmet_demand_today = 0

            products_for_sales = conn.execute(
                "SELECT * FROM products WHERE status = 'ACTIVE';"
            ).fetchall()

            for prod in products_for_sales:
                prod_id = prod["id"]
                price = prod["selling_price"]
                cost = prod["production_cost"]
                quality = prod["quality"]
                inv = prod["inventory_units"]

                base_demand = self.calculate_product_demand(
                    price=price, cost=cost, quality=quality, reputation=reputation
                )
                # Apply difficulty demand multiplier and marketing boost
                calculated_demand = max(0, int(round(base_demand * demand_mult * marketing_demand_boost)))

                actual_sales = min(calculated_demand, inv)
                unmet = max(0, calculated_demand - actual_sales)
                revenue = round(actual_sales * price, 2)

                if actual_sales > 0:
                    self.record_transaction(
                        conn=conn, day=current_day, category="REVENUE",
                        amount=revenue,
                        description=f"Sold {actual_sales} units of {prod['name']} @ {price:.2f}",
                        reference_id=prod_id
                    )

                new_inv = inv - actual_sales
                new_total_sold = prod["total_units_sold"] + actual_sales
                new_total_rev = prod["total_revenue"] + revenue

                conn.execute(
                    """UPDATE products SET
                       inventory_units = ?,
                       unmet_demand_last_day = ?,
                       units_sold_last_day = ?,
                       total_units_sold = ?,
                       total_revenue = ?
                       WHERE id = ?;""",
                    (new_inv, unmet, actual_sales, new_total_sold, new_total_rev, prod_id)
                )

                total_revenue_today += revenue
                total_units_sold_today += actual_sales
                total_unmet_demand_today += unmet

                if unmet > 0:
                    conn.execute(
                        """INSERT INTO activity_log (day, category, severity, message)
                           VALUES (?, 'OPERATIONS', 'WARNING', ?);""",
                        (current_day, f"Stockout: missed {unmet} potential sales for {prod['name']}.")
                    )

            # ---- 7. FIXED OPERATING EXPENSES --------------------------------
            fixed_opex = round(50.0 * cost_mult, 2)
            self.record_transaction(
                conn=conn, day=current_day, category="OPEX",
                amount=-fixed_opex,
                description="Daily facility rent, utilities, and administrative overhead"
            )

            # ---- 8. REPUTATION DYNAMICS ------------------------------------
            rep_delta = 0.0
            if total_unmet_demand_today > 10:
                rep_delta -= 0.5
            elif total_units_sold_today > 10 and total_unmet_demand_today == 0:
                rep_delta += 0.3
            # Distress-stage reputation penalty
            distress = self._classify_distress(self.get_current_cash(conn))
            if distress == "DISTRESS":
                rep_delta -= 0.2
            elif distress == "CRITICAL":
                rep_delta -= 0.5
            new_reputation = max(10.0, min(100.0, reputation + rep_delta))
            conn.execute("UPDATE company SET reputation = ? WHERE id = 'comp_001';", (new_reputation,))

            # ---- 9. FINANCIAL SNAPSHOT --------------------------------------
            ending_cash = self.get_current_cash(conn)
            total_opex = fixed_opex
            net_profit = total_revenue_today - (total_cogs_today + total_opex + total_wages_today + total_marketing_spend_today + total_rd_spend_today)

            inv_rows = conn.execute("SELECT inventory_units, production_cost FROM products;").fetchall()
            inventory_val = sum(r["inventory_units"] * r["production_cost"] for r in inv_rows)
            company_valuation = max(0.0, ending_cash + inventory_val + (new_reputation * 100))

            distress_stage = self._classify_distress(ending_cash)

            conn.execute(
                """INSERT INTO daily_snapshots (
                    day, cash_balance, revenue, cogs, operating_expenses, net_profit,
                    total_units_sold, unmet_demand, reputation, inventory_value, total_valuation,
                    wages_paid, marketing_spend, rd_spend, headcount, distress_stage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (
                    current_day, ending_cash, total_revenue_today, total_cogs_today,
                    total_opex, net_profit, total_units_sold_today,
                    total_unmet_demand_today, new_reputation, inventory_val, company_valuation,
                    total_wages_today, total_marketing_spend_today, total_rd_spend_today,
                    headcount, distress_stage
                )
            )

            # ---- 10. DISTRESS ALERTS & WIN/LOSS EVALUATION ------------------
            if distress_stage == "WATCH":
                conn.execute(
                    "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                    (current_day, "FINANCE", "WARNING", f"Liquidity Watch: Cash at {ending_cash:.2f} cr — monitor expenses.")
                )
            elif distress_stage == "DISTRESS":
                conn.execute(
                    "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                    (current_day, "FINANCE", "DANGER", f"Financial Distress: Cash critically low at {ending_cash:.2f} cr!")
                )
            elif distress_stage == "CRITICAL":
                conn.execute(
                    "INSERT INTO activity_log (day,category,severity,message) VALUES (?,?,?,?);",
                    (current_day, "FINANCE", "DANGER", f"CRITICAL INSOLVENCY RISK: Cash = {ending_cash:.2f} cr. Immediate action required!")
                )

            self._check_win_loss(conn, current_day, ending_cash, company_valuation)

        conn.close()

        return {
            "day": current_day,
            "cash_balance": ending_cash,
            "revenue": total_revenue_today,
            "cogs": total_cogs_today,
            "opex": total_opex,
            "net_profit": net_profit,
            "units_sold": total_units_sold_today,
            "unmet_demand": total_unmet_demand_today,
            "reputation": new_reputation,
            "wages": total_wages_today,
            "marketing_spend": total_marketing_spend_today,
            "rd_spend": total_rd_spend_today,
            "distress_stage": distress_stage,
        }

    def get_full_state(self) -> Dict[str, Any]:
        """Collects full game state for dashboard rendering."""
        conn = get_db_connection(self.db_path)
        company = conn.execute("SELECT * FROM company WHERE id = 'comp_001';").fetchone()
        clock = conn.execute("SELECT * FROM game_clock WHERE id = 1;").fetchone()
        products = conn.execute("SELECT * FROM products;").fetchall()
        snapshots = conn.execute("SELECT * FROM daily_snapshots ORDER BY day ASC;").fetchall()
        latest_snapshot = snapshots[-1] if snapshots else None
        transactions = conn.execute("SELECT * FROM ledger ORDER BY rowid DESC LIMIT 30;").fetchall()
        activities = conn.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT 50;").fetchall()
        ai_decisions = conn.execute("SELECT * FROM ai_decisions ORDER BY created_at DESC, rowid DESC LIMIT 20;").fetchall()
        employees = conn.execute("SELECT * FROM employees WHERE status = 'ACTIVE';").fetchall()
        loans = conn.execute("SELECT * FROM loans WHERE status = 'ACTIVE';").fetchall()
        campaigns = conn.execute("SELECT * FROM marketing_campaigns WHERE status = 'ACTIVE';").fetchall()
        rd_projects = conn.execute("SELECT * FROM rd_projects WHERE status != 'CANCELLED';").fetchall()
        settings = conn.execute("SELECT * FROM game_settings WHERE id = 1;").fetchone()

        current_cash = self.get_current_cash(conn)
        conn.close()

        return {
            "company": dict(company) if company else {"id": "comp_001", "name": "SimCorp", "industry": "General", "reputation": 50.0},
            "clock": {
                "current_day": clock["current_day"] if clock else 1,
                "is_paused": bool(clock["is_paused"]) if clock else True,
                "tick_speed_seconds": clock["tick_speed_seconds"] if clock else 3.0
            },
            "cash_balance": current_cash,
            "products": [dict(p) for p in products],
            "latest_snapshot": dict(latest_snapshot) if latest_snapshot else None,
            "historical_snapshots": [dict(s) for s in snapshots],
            "recent_transactions": [dict(t) for t in transactions],
            "recent_activities": [dict(a) for a in activities],
            "ai_decisions": [dict(d) for d in ai_decisions],
            "employees": [dict(e) for e in employees],
            "active_loans": [dict(l) for l in loans],
            "active_campaigns": [dict(c) for c in campaigns],
            "rd_projects": [dict(r) for r in rd_projects],
            "game_settings": dict(settings) if settings else {"mode": "sandbox", "difficulty": "normal", "game_state": "RUNNING"},
            "daily_fixed_opex": 50.0
        }

    def update_product(self, product_id: str, price: Optional[float] = None, target: Optional[int] = None, status: Optional[str] = None) -> bool:
        """Allows player/management to adjust pricing, production targets, or status."""
        conn = get_db_connection(self.db_path)
        with conn:
            cur = conn.cursor()
            if price is not None:
                cur.execute("UPDATE products SET selling_price = ? WHERE id = ?;", (price, product_id))
            if target is not None:
                cur.execute("UPDATE products SET daily_production_target = ? WHERE id = ?;", (target, product_id))
            if status is not None:
                cur.execute("UPDATE products SET status = ? WHERE id = ?;", (status, product_id))
            rowcount = cur.rowcount
        conn.close()
        return rowcount > 0

    def set_clock_state(self, is_paused: Optional[bool] = None, speed_seconds: Optional[float] = None) -> Dict[str, Any]:
        """Pauses, resumes, or changes speed of the clock."""
        conn = get_db_connection(self.db_path)
        with conn:
            if is_paused is not None:
                conn.execute("UPDATE game_clock SET is_paused = ? WHERE id = 1;", (1 if is_paused else 0,))
            if speed_seconds is not None:
                conn.execute("UPDATE game_clock SET tick_speed_seconds = ? WHERE id = 1;", (speed_seconds,))
            clock = conn.execute("SELECT * FROM game_clock WHERE id = 1;").fetchone()
        conn.close()
        return {
            "current_day": clock["current_day"],
            "is_paused": bool(clock["is_paused"]),
            "tick_speed_seconds": clock["tick_speed_seconds"]
        }
