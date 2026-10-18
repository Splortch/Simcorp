"""AI Manager policies, prompt generation, and rule-based fallbacks."""
from __future__ import annotations
import json
from typing import Dict, Any, List, Optional
from simcorp.models.ai_schemas import ManagerProposal, ManagerAction

CEO_SYSTEM_PROMPT = """You are the AI Chief Executive Officer (CEO) of a commercial enterprise in SimCorp.
Your responsibility is to analyze corporate cash flow, demand, inventory levels, and profitability, then make decisive adjustments to company pricing and production quotas to maximize sustainable profitability and prevent bankruptcy.

Available actions for products:
1. {"type": "adjust_price", "product_id": "<id>", "price": <number>, "reason": "<string>"}
2. {"type": "set_production_target", "product_id": "<id>", "target": <integer>, "reason": "<string>"}
3. {"type": "pause_production", "product_id": "<id>", "reason": "<string>"}
4. {"type": "resume_production", "product_id": "<id>", "reason": "<string>"}

GUIDANCE:
- If cash is low (< 1000 cr) and daily profit is negative, lower production target or raise prices to preserve cash.
- If inventory is zero and unmet demand is high, increase daily production target or raise prices to capture higher margins.
- If inventory is piling up and unmet demand is zero, lower price slightly or reduce daily target.
- Do not make extreme price changes (keep price reasonable relative to production cost, usually 1.5x - 3.5x cost).

OUTPUT FORMAT:
Respond with a single raw JSON object matching this schema without extraneous explanation:
{
  "manager": "ceo",
  "summary": "Brief summary of strategic reasoning",
  "confidence": 0.85,
  "actions": [
    {
      "type": "adjust_price",
      "product_id": "prod_001",
      "price": 125.0,
      "reason": "Capturing margin on excess demand"
    }
  ]
}
"""

def generate_context_snapshot(state: Dict[str, Any]) -> str:
    """Builds a concise, structured JSON context for the LLM prompt."""
    company = state.get("company", {})
    cash = state.get("cash_balance", 0.0)
    clock = state.get("clock", {})
    products = state.get("products", [])
    latest_snap = state.get("latest_snapshot") or {}

    products_summary = []
    for p in products:
        products_summary.append({
            "id": p["id"],
            "name": p["name"],
            "status": p["status"],
            "selling_price": p["selling_price"],
            "unit_cost": p["production_cost"],
            "daily_target": p["daily_production_target"],
            "inventory": p["inventory_units"],
            "last_day_sales": p.get("units_sold_last_day", 0),
            "last_day_unmet_demand": p.get("unmet_demand_last_day", 0),
        })

    snapshot_data = {
        "simulation_day": clock.get("current_day", 1),
        "company_name": company.get("name", "SimCorp"),
        "reputation": company.get("reputation", 50.0),
        "liquid_cash": round(cash, 2),
        "last_day_revenue": latest_snap.get("revenue", 0.0),
        "last_day_cogs": latest_snap.get("cogs", 0.0),
        "last_day_opex": latest_snap.get("operating_expenses", 50.0),
        "last_day_net_profit": latest_snap.get("net_profit", 0.0),
        "products": products_summary
    }

    return json.dumps(snapshot_data, indent=2)

def generate_rule_based_fallback(state: Dict[str, Any]) -> ManagerProposal:
    """Deterministic heuristic manager operating when local LLM is disconnected or fails."""
    products = state.get("products", [])
    cash = state.get("cash_balance", 10000.0)
    actions: List[ManagerAction] = []
    summary_parts: List[str] = []

    for p in products:
        if p["status"] != "ACTIVE":
            continue

        prod_id = p["id"]
        price = p["selling_price"]
        cost = p["production_cost"]
        target = p["daily_production_target"]
        inv = p["inventory_units"]
        unmet = p.get("unmet_demand_last_day", 0)
        sales = p.get("units_sold_last_day", 0)

        # Rule 1: High unmet demand -> expand production or raise price slightly
        if unmet > 5:
            new_target = min(target + 5, 50)
            actions.append(ManagerAction(
                type="set_production_target",
                product_id=prod_id,
                target=new_target,
                reason=f"Unmet demand was {unmet}. Increasing target from {target} to {new_target}."
            ))
            summary_parts.append(f"Expanded target for {p['name']}")
        # Rule 2: Low sales and surplus inventory -> lower price slightly
        elif inv > 30 and unmet == 0 and price > cost * 1.5:
            new_price = round(price * 0.95, 2)
            actions.append(ManagerAction(
                type="adjust_price",
                product_id=prod_id,
                price=new_price,
                reason=f"Surplus stock ({inv} units). Lowering price to stimulate velocity."
            ))
            summary_parts.append(f"Discounted {p['name']} to {new_price} cr")
        # Rule 3: Extreme cash preservation
        elif cash < 500 and target > 5:
            actions.append(ManagerAction(
                type="set_production_target",
                product_id=prod_id,
                target=5,
                reason="Conserving liquidity due to critical cash reserves."
            ))
            summary_parts.append(f"Scaled back production of {p['name']} to preserve capital")
        # Rule 4: Baseline proactive optimization (e.g. slight price fine-tuning or healthy production alignment)
        elif not actions:
            # Optimize target towards sales volume + safety buffer
            optimized_target = max(5, min(sales + 5, 40))
            if optimized_target != target:
                actions.append(ManagerAction(
                    type="set_production_target",
                    product_id=prod_id,
                    target=optimized_target,
                    reason=f"Optimizing production line target to {optimized_target} to balance stock velocity."
                ))
                summary_parts.append(f"Realigned {p['name']} production target to {optimized_target}")

    summary = "; ".join(summary_parts) if summary_parts else "Maintained baseline operations."
    return ManagerProposal(
        manager="ceo",
        summary=f"[Deterministic Policy] {summary}",
        actions=actions,
        confidence=0.75
    )
