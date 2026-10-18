"""Hierarchy, roles, permissions, and seeding for SimCorp AI workforce."""
from __future__ import annotations
import json
from typing import Dict, Any, List

DEFAULT_AGENTS = [
    # Level 0: Executive
    {
        "id": "agent_ceo",
        "name": "Nexus-Prime",
        "title": "Chief Executive Officer",
        "department": "EXECUTIVE",
        "level": 0,
        "supervisor_id": None,
        "specialization": "Strategic Leadership, Cross-department Conflict Resolution, Capital Allocation",
        "allowed_tasks": ["STRATEGIC_REVIEW", "APPROVE_EXECUTIVE_ACTION", "GOAL_ALIGNMENT"],
        "permissions": {
            "can_approve_executive": True,
            "can_resolve_conflicts": True,
            "can_set_objectives": True,
            "can_assign_tasks": True,
        },
        "current_status": "IDLE",
        "current_objective": "Maintain solvency and maximize company valuation while ensuring balanced operations.",
    },
    # Level 1: Department Managers
    {
        "id": "agent_cfo",
        "name": "Aurelius Vance",
        "title": "Finance Manager",
        "department": "FINANCE",
        "level": 1,
        "supervisor_id": "agent_ceo",
        "specialization": "Liquidity Management, Debt Structuring, Profitability & Margin Optimization",
        "allowed_tasks": ["FINANCIAL_AUDIT", "CASHFLOW_FORECAST", "DEBT_ANALYSIS", "BUDGET_APPROVAL"],
        "permissions": {
            "can_recommend_loans": True,
            "can_set_budgets": True,
            "can_assign_tasks": True,
            "can_review_subordinates": True,
        },
        "current_status": "IDLE",
        "current_objective": "Ensure cash reserves remain above safety thresholds and eliminate operational burn.",
    },
    {
        "id": "agent_coo",
        "name": "Valerie Stone",
        "title": "Operations Manager",
        "department": "OPERATIONS",
        "level": 1,
        "supervisor_id": "agent_ceo",
        "specialization": "Production Scheduling, Capacity Utilization, Supply Chain & Inventory Control",
        "allowed_tasks": ["PRODUCTION_PLANNING", "INVENTORY_AUDIT", "PRICING_ALIGNMENT"],
        "permissions": {
            "can_recommend_production": True,
            "can_recommend_pricing": True,
            "can_assign_tasks": True,
            "can_review_subordinates": True,
        },
        "current_status": "IDLE",
        "current_objective": "Eliminate stockouts and prevent unsold inventory accumulation.",
    },
    {
        "id": "agent_cmo",
        "name": "Marcus Kane",
        "title": "Marketing & Sales Manager",
        "department": "MARKETING",
        "level": 1,
        "supervisor_id": "agent_ceo",
        "specialization": "Brand Positioning, Customer Acquisition, Campaign ROI & Market Share Growth",
        "allowed_tasks": ["MARKET_EXPANSION_REVIEW", "CAMPAIGN_ALLOCATION", "PRICING_STRATEGY"],
        "permissions": {
            "can_recommend_campaigns": True,
            "can_recommend_pricing": True,
            "can_assign_tasks": True,
            "can_review_subordinates": True,
        },
        "current_status": "IDLE",
        "current_objective": "Expand customer demand sustainably within daily marketing budget constraints.",
    },
    {
        "id": "agent_cro",
        "name": "Dr. Aris Thorne",
        "title": "R&D Director",
        "department": "RESEARCH",
        "level": 1,
        "supervisor_id": "agent_ceo",
        "specialization": "Product Innovation, Quality Engineering, Technological Roadmapping",
        "allowed_tasks": ["RD_PORTFOLIO_REVIEW", "QUALITY_ASSESSMENT", "FEASIBILITY_STUDY"],
        "permissions": {
            "can_recommend_rd": True,
            "can_assign_tasks": True,
            "can_review_subordinates": True,
        },
        "current_status": "IDLE",
        "current_objective": "Elevate product quality metrics to command premium market pricing.",
    },
    # Level 2: Specialized Agents
    {
        "id": "agent_spec_cashflow",
        "name": "Elena Rostova",
        "title": "Cash Flow Analyst",
        "department": "FINANCE",
        "level": 2,
        "supervisor_id": "agent_cfo",
        "specialization": "Daily Burn Analysis, Working Capital Runway, Fixed Expense Tracking",
        "allowed_tasks": ["CASHFLOW_PROJECTION", "BURN_RATE_CHECK"],
        "permissions": {
            "can_read_financials": True,
            "can_generate_forecasts": True,
        },
        "current_status": "IDLE",
        "current_objective": "Calculate operational runway and flag insolvency risks early.",
    },
    {
        "id": "agent_spec_production",
        "name": "Kaelen Voss",
        "title": "Production Planner",
        "department": "OPERATIONS",
        "level": 2,
        "supervisor_id": "agent_coo",
        "specialization": "Demand Matching, Batch Sizing, Manufacturing Cost Optimization",
        "allowed_tasks": ["CALCULATE_OPTIMAL_TARGET", "INVENTORY_BALANCE"],
        "permissions": {
            "can_read_operations": True,
            "can_recommend_target": True,
        },
        "current_status": "IDLE",
        "current_objective": "Calibrate daily manufacturing targets against recent sales velocity.",
    },
    {
        "id": "agent_spec_pricing",
        "name": "Siddharth Nair",
        "title": "Pricing Analyst",
        "department": "MARKETING",
        "level": 2,
        "supervisor_id": "agent_cmo",
        "specialization": "Price Elasticity, Competitor Benchmarking, Contribution Margin Optimization",
        "allowed_tasks": ["PRICE_ELASTICITY_STUDY", "MARGIN_ANALYSIS"],
        "permissions": {
            "can_read_market": True,
            "can_recommend_price": True,
        },
        "current_status": "IDLE",
        "current_objective": "Identify revenue-maximizing price points for active catalog items.",
    },
    {
        "id": "agent_spec_rd",
        "name": "Lyra Sterling",
        "title": "Product Researcher",
        "department": "RESEARCH",
        "level": 2,
        "supervisor_id": "agent_cro",
        "specialization": "Quality Benchmark Testing, Component Longevity, Specification Upgrades",
        "allowed_tasks": ["QUALITY_GAP_ANALYSIS", "UPGRADE_SPECIFICATION"],
        "permissions": {
            "can_read_products": True,
            "can_recommend_spec": True,
        },
        "current_status": "IDLE",
        "current_objective": "Benchmark existing product quality and prioritize high-ROI upgrades.",
    },
]


def seed_ai_agents(conn) -> None:
    """Inserts initial agent hierarchy if table is empty."""
    existing = conn.execute("SELECT COUNT(*) AS cnt FROM ai_agents;").fetchone()
    if existing and existing["cnt"] > 0:
        return

    for a in DEFAULT_AGENTS:
        conn.execute(
            """INSERT INTO ai_agents (
                id, name, title, department, level, supervisor_id,
                specialization, allowed_tasks_json, permissions_json,
                current_status, current_objective, performance_score,
                tasks_completed, tasks_failed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 100.0, 0, 0);""",
            (
                a["id"],
                a["name"],
                a["title"],
                a["department"],
                a["level"],
                a["supervisor_id"],
                a["specialization"],
                json.dumps(a["allowed_tasks"]),
                json.dumps(a["permissions"]),
                a["current_status"],
                a["current_objective"],
            )
        )
