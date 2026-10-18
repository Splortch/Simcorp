"""Simulation engine executing deterministic business days and transactions."""
from __future__ import annotations
import math
import random
import uuid
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from simcorp.engine.db import get_db_connection, initialize_database

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
        initial_daily_target: int = 15
    ) -> None:
        """Initializes a brand new company and base ledger with 10,000 starting credits."""
        conn = get_db_connection(self.db_path)
        with conn:
            # Clear existing data for fresh game
            conn.execute("DELETE FROM ledger;")
            conn.execute("DELETE FROM products;")
            conn.execute("DELETE FROM market_segments;")
            conn.execute("DELETE FROM market_events;")
            conn.execute("DELETE FROM daily_snapshots;")
            conn.execute("DELETE FROM ai_decisions;")
            conn.execute("DELETE FROM activity_log;")
            conn.execute("DELETE FROM company;")
            conn.execute("DELETE FROM game_clock;")

            company_id = "comp_001"
            conn.execute(
                "INSERT INTO company (id, name, industry, reputation) VALUES (?, ?, ?, ?);",
                (company_id, company_name, "Hardware & Electronics", 50.0)
            )

            conn.execute(
                "INSERT INTO game_clock (id, current_day, is_paused, tick_speed_seconds) VALUES (1, 1, 1, 3.0);"
            )

            # Record initial starting capital in ledger
            tx_id = f"tx_init_{uuid.uuid4().hex[:8]}"
            conn.execute(
                """INSERT INTO ledger (id, day, category, amount, balance_after, reference_id, description)
                   VALUES (?, 1, 'EQUITY_INJECTION', ?, ?, NULL, 'Initial Seed Capital');""",
                (tx_id, starting_cash, starting_cash)
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

            # Log startup event
            conn.execute(
                """INSERT INTO activity_log (day, category, severity, message, details_json)
                   VALUES (1, 'SYSTEM', 'SUCCESS', ?, NULL);""",
                (f"Company '{company_name}' incorporated with {starting_cash:.2f} credits in starting capital.",)
            )

            # Record initial day 1 baseline snapshot
            conn.execute(
                """INSERT INTO daily_snapshots (
                    day, cash_balance, revenue, cogs, operating_expenses, net_profit,
                    total_units_sold, unmet_demand, reputation, inventory_value, total_valuation
                ) VALUES (1, ?, 0.0, 0.0, 0.0, 0.0, 0, 0, 50.0, ?, ?);""",
                (starting_cash, 20 * initial_product_cost, starting_cash + (20 * initial_product_cost))
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

    def advance_day(self) -> Dict[str, Any]:
        """
        Executes a single simulation day in strict, deterministic order:
        1. Check clock and increment day.
        2. Production: Enforce cash constraint and produce inventory up to target.
        3. Market demand & Sales: Convert demand limited by actual inventory.
        4. Deliveries & Revenue: Record revenue from completed sales in ledger.
        5. Expenses: Pay fixed OPEX and wages.
        6. Inventory & Snapshot: Calculate inventory valuation, write snapshot.
        7. Insolvency check and log alerts.
        """
        conn = get_db_connection(self.db_path)
        with conn:
            clock_row = conn.execute("SELECT current_day FROM game_clock WHERE id = 1;").fetchone()
            if not clock_row:
                # If no game exists, initialize default
                self.create_new_game()
                current_day = 1
            else:
                current_day = clock_row["current_day"] + 1
                conn.execute(
                    "UPDATE game_clock SET current_day = ?, last_tick_at = CURRENT_TIMESTAMP WHERE id = 1;",
                    (current_day,)
                )

            comp_row = conn.execute("SELECT reputation, name FROM company WHERE id = 'comp_001';").fetchone()
            reputation = comp_row["reputation"] if comp_row else 50.0

            # 1. Production Phase
            active_products = conn.execute(
                "SELECT * FROM products WHERE status = 'ACTIVE';"
            ).fetchall()

            total_cogs_today = 0.0
            for prod in active_products:
                prod_id = prod["id"]
                target = prod["daily_production_target"]
                unit_cost = prod["production_cost"]
                current_cash = self.get_current_cash(conn)

                # Cannot produce without cash
                max_affordable = max(0, int(current_cash // unit_cost)) if unit_cost > 0 else target
                actual_production = min(target, max_affordable)
                prod_expense = actual_production * unit_cost

                if prod_expense > 0:
                    self.record_transaction(
                        conn=conn,
                        day=current_day,
                        category="COGS",
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
                conn.execute(
                    "UPDATE products SET inventory_units = ? WHERE id = ?;",
                    (new_inv, prod_id)
                )

            # 2. Demand & Sales Phase
            total_revenue_today = 0.0
            total_units_sold_today = 0
            total_unmet_demand_today = 0

            # Re-read products with updated inventory
            products_for_sales = conn.execute(
                "SELECT * FROM products WHERE status = 'ACTIVE';"
            ).fetchall()

            for prod in products_for_sales:
                prod_id = prod["id"]
                price = prod["selling_price"]
                cost = prod["production_cost"]
                quality = prod["quality"]
                inv = prod["inventory_units"]

                calculated_demand = self.calculate_product_demand(
                    price=price,
                    cost=cost,
                    quality=quality,
                    reputation=reputation
                )

                actual_sales = min(calculated_demand, inv)
                unmet = max(0, calculated_demand - actual_sales)
                revenue = round(actual_sales * price, 2)

                if actual_sales > 0:
                    self.record_transaction(
                        conn=conn,
                        day=current_day,
                        category="REVENUE",
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

            # 3. Fixed Operating Expenses (Facilities, minimal administrative software)
            fixed_opex = 50.0
            self.record_transaction(
                conn=conn,
                day=current_day,
                category="OPEX",
                amount=-fixed_opex,
                description="Daily facility rent, utilities, and administrative overhead"
            )

            # 4. Reputation dynamics
            rep_delta = 0.0
            if total_unmet_demand_today > 10:
                rep_delta -= 0.5
            elif total_units_sold_today > 10 and total_unmet_demand_today == 0:
                rep_delta += 0.3
            new_reputation = max(10.0, min(100.0, reputation + rep_delta))
            conn.execute("UPDATE company SET reputation = ? WHERE id = 'comp_001';", (new_reputation,))

            # 5. Financial Snapshot & Balance
            ending_cash = self.get_current_cash(conn)
            total_opex = fixed_opex
            net_profit = total_revenue_today - (total_cogs_today + total_opex)

            # Inventory asset valuation
            inv_rows = conn.execute("SELECT inventory_units, production_cost FROM products;").fetchall()
            inventory_val = sum(r["inventory_units"] * r["production_cost"] for r in inv_rows)
            company_valuation = max(0.0, ending_cash + inventory_val + (new_reputation * 100))

            conn.execute(
                """INSERT INTO daily_snapshots (
                    day, cash_balance, revenue, cogs, operating_expenses, net_profit,
                    total_units_sold, unmet_demand, reputation, inventory_value, total_valuation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (
                    current_day, ending_cash, total_revenue_today, total_cogs_today,
                    total_opex, net_profit, total_units_sold_today,
                    total_unmet_demand_today, new_reputation, inventory_val, company_valuation
                )
            )

            # 6. Solvency warnings
            if ending_cash < 500.0 and ending_cash > 0:
                conn.execute(
                    """INSERT INTO activity_log (day, category, severity, message)
                       VALUES (?, 'FINANCE', 'DANGER', ?);""",
                    (current_day, f"CRITICAL: Liquidity warning! Cash reserves down to {ending_cash:.2f} credits.")
                )
            elif ending_cash <= 0:
                conn.execute(
                    """INSERT INTO activity_log (day, category, severity, message)
                       VALUES (?, 'FINANCE', 'DANGER', ?);""",
                    (current_day, "INSOLVENCY ALERT: Company cash balance is negative or zero! Trading at severe financial risk.")
                )

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
            "reputation": new_reputation
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
