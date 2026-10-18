"""SimCorp Balancing Laboratory -- batch runner for simulation experiments.

Run from backend directory with:
    python -m simcorp.lab.runner --help
    python -m simcorp.lab.runner --days 60 --difficulty normal --runs 3
"""
from __future__ import annotations
import argparse
import sys
import tempfile
import os
from pathlib import Path

# Add backend to path if needed
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from simcorp.engine.simulation import SimulationEngine


def run_experiment(days: int = 60, difficulty: str = "normal", mode: str = "sandbox", runs: int = 3) -> dict:
    """Run a batch of standalone simulations in isolated temporary databases for balance testing."""
    results = []

    for run_idx in range(runs):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_db = tmp.name

        try:
            engine = SimulationEngine(db_path=tmp_db, seed=42 + run_idx * 17)
            engine.create_new_game(
                company_name=f"TestCorp_{run_idx+1}",
                starting_cash=10000.0,
                mode=mode,
                difficulty=difficulty,
            )

            for _ in range(days):
                engine.advance_day()

            state = engine.get_full_state()
            cash = state.get("cash_balance", 0.0)
            valuation = state.get("company_valuation", 0.0)
            day = state.get("current_day", days)
            reputation = state.get("company", {}).get("reputation", 50.0)
            products = state.get("products", [])
            employees = state.get("employees", [])

            results.append({
                "run": run_idx + 1,
                "ending_cash": cash,
                "valuation": valuation,
                "day": day,
                "bankrupt": cash <= 0,
                "products_count": len(products),
                "employees_count": len(employees),
                "reputation": reputation,
            })
        finally:
            if os.path.exists(tmp_db):
                try:
                    os.remove(tmp_db)
                except OSError:
                    pass

    avg_cash = sum(r["ending_cash"] for r in results) / len(results)
    avg_valuation = sum(r["valuation"] for r in results) / len(results)
    bankruptcies = sum(1 for r in results if r["bankrupt"])

    summary = {
        "difficulty": difficulty,
        "mode": mode,
        "runs": runs,
        "days": days,
        "avg_ending_cash": avg_cash,
        "avg_valuation": avg_valuation,
        "bankruptcy_rate": bankruptcies / runs,
        "details": results,
    }
    return summary


def main():
    parser = argparse.ArgumentParser(description="SimCorp Balancing Lab")
    parser.add_argument("--days", type=int, default=60, help="Days to simulate per run")
    parser.add_argument("--difficulty", type=str, default="normal", choices=["easy", "normal", "hard", "brutal"], help="Difficulty level")
    parser.add_argument("--mode", type=str, default="sandbox", choices=["sandbox", "campaign"], help="Game mode")
    parser.add_argument("--runs", type=int, default=3, help="Number of simulation runs")

    args = parser.parse_args()
    print(f"=== Starting SimCorp Balancing Experiment ({args.runs} runs, {args.days} days, {args.difficulty} difficulty) ===")
    summary = run_experiment(days=args.days, difficulty=args.difficulty, mode=args.mode, runs=args.runs)

    print("\n--- Summary Results ---")
    print(f"Mode: {summary['mode']} | Difficulty: {summary['difficulty']}")
    print(f"Bankruptcy Rate: {summary['bankruptcy_rate'] * 100:.1f}%")
    print(f"Average Ending Cash: ${summary['avg_ending_cash']:,.2f}")
    print(f"Average Valuation: ${summary['avg_valuation']:,.2f}")
    print("\nIndividual Runs:")
    for r in summary["details"]:
        status = "BANKRUPT" if r["bankrupt"] else "SURVIVED"
        print(f"  Run {r['run']}: {status} | Cash: ${r['ending_cash']:,.2f} | Valuation: ${r['valuation']:,.2f} | Rep: {r['reputation']:.1f}")


if __name__ == "__main__":
    main()
