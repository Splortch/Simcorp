"""Database schema and SQLite connection management for SimCorp."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS company (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT NOT NULL DEFAULT 'Hardware & Electronics',
    reputation REAL NOT NULL DEFAULT 50.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS game_clock (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    current_day INTEGER NOT NULL DEFAULT 1,
    is_paused INTEGER NOT NULL DEFAULT 1,
    tick_speed_seconds REAL NOT NULL DEFAULT 3.0,
    last_tick_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ledger (
    id TEXT PRIMARY KEY,
    day INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category TEXT NOT NULL, -- REVENUE, COGS, WAGES, OPEX, MARKETING, RD, MISC
    amount REAL NOT NULL,   -- Positive for cash inflow, negative for cash outflow
    balance_after REAL NOT NULL,
    reference_id TEXT,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,   -- IN_DEVELOPMENT, ACTIVE, DISCONTINUED
    selling_price REAL NOT NULL,
    production_cost REAL NOT NULL,
    quality REAL NOT NULL DEFAULT 50.0,
    inventory_units INTEGER NOT NULL DEFAULT 0,
    daily_production_target INTEGER NOT NULL DEFAULT 10,
    unmet_demand_last_day INTEGER NOT NULL DEFAULT 0,
    units_sold_last_day INTEGER NOT NULL DEFAULT 0,
    total_units_sold INTEGER NOT NULL DEFAULT 0,
    total_revenue REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS market_segments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_demand INTEGER NOT NULL,
    price_sensitivity REAL NOT NULL, -- higher = more sensitive
    quality_importance REAL NOT NULL,
    marketing_responsiveness REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS market_events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    event_type TEXT NOT NULL,
    start_day INTEGER NOT NULL,
    duration_days INTEGER NOT NULL,
    end_day INTEGER NOT NULL,
    demand_multiplier REAL NOT NULL DEFAULT 1.0,
    cost_multiplier REAL NOT NULL DEFAULT 1.0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS daily_snapshots (
    day INTEGER PRIMARY KEY,
    cash_balance REAL NOT NULL,
    revenue REAL NOT NULL,
    cogs REAL NOT NULL,
    operating_expenses REAL NOT NULL,
    net_profit REAL NOT NULL,
    total_units_sold INTEGER NOT NULL,
    unmet_demand INTEGER NOT NULL,
    reputation REAL NOT NULL,
    inventory_value REAL NOT NULL,
    total_valuation REAL NOT NULL,
    wages_paid REAL NOT NULL DEFAULT 0.0,
    marketing_spend REAL NOT NULL DEFAULT 0.0,
    rd_spend REAL NOT NULL DEFAULT 0.0,
    headcount INTEGER NOT NULL DEFAULT 0,
    distress_stage TEXT NOT NULL DEFAULT 'HEALTHY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT NOT NULL,
    daily_wage REAL NOT NULL DEFAULT 20.0,
    productivity REAL NOT NULL DEFAULT 1.0,
    morale REAL NOT NULL DEFAULT 75.0,
    hired_day INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS rd_projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target_product_id TEXT,
    daily_budget REAL NOT NULL DEFAULT 50.0,
    progress REAL NOT NULL DEFAULT 0.0,
    target_quality_gain REAL NOT NULL DEFAULT 10.0,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    started_day INTEGER NOT NULL,
    completed_day INTEGER
);

CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target_product_id TEXT,
    channel TEXT NOT NULL DEFAULT 'DIGITAL',
    daily_budget REAL NOT NULL DEFAULT 30.0,
    effectiveness_multiplier REAL NOT NULL DEFAULT 1.0,
    demand_boost_pct REAL NOT NULL DEFAULT 0.0,
    started_day INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS loans (
    id TEXT PRIMARY KEY,
    principal REAL NOT NULL,
    outstanding_balance REAL NOT NULL,
    daily_interest_rate REAL NOT NULL DEFAULT 0.002,
    daily_repayment REAL NOT NULL DEFAULT 0.0,
    taken_day INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS game_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mode TEXT NOT NULL DEFAULT 'sandbox',
    difficulty TEXT NOT NULL DEFAULT 'normal',
    campaign_goal TEXT NOT NULL DEFAULT 'VALUATION_TARGET',
    campaign_target_value REAL NOT NULL DEFAULT 50000.0,
    campaign_deadline_days INTEGER NOT NULL DEFAULT 180,
    game_state TEXT NOT NULL DEFAULT 'RUNNING',
    win_loss_reason TEXT,
    starting_cash_multiplier REAL NOT NULL DEFAULT 1.0,
    demand_multiplier REAL NOT NULL DEFAULT 1.0,
    cost_multiplier REAL NOT NULL DEFAULT 1.0,
    event_frequency_multiplier REAL NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_decisions (
    id TEXT PRIMARY KEY,
    day INTEGER NOT NULL,
    manager_role TEXT NOT NULL,
    action_type TEXT NOT NULL,
    parameters_json TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL, -- PENDING, APPROVED, REJECTED, EXECUTED, FAILED
    result_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    enabled INTEGER NOT NULL DEFAULT 1,
    provider TEXT NOT NULL DEFAULT 'lm_studio',
    base_url TEXT NOT NULL DEFAULT 'http://localhost:1234/v1',
    model_id TEXT NOT NULL DEFAULT 'google/gemma-4-e4b',
    autonomy_mode TEXT NOT NULL DEFAULT 'autonomous', -- autonomous, oversight, player_approval
    review_frequency_days INTEGER NOT NULL DEFAULT 2,
    timeout_seconds REAL NOT NULL DEFAULT 75.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day INTEGER NOT NULL,
    category TEXT NOT NULL, -- SYSTEM, FINANCE, OPERATIONS, MARKETING, RESEARCH, AI
    severity TEXT NOT NULL DEFAULT 'INFO', -- INFO, WARNING, SUCCESS, DANGER
    message TEXT NOT NULL,
    details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    department TEXT NOT NULL, -- EXECUTIVE, FINANCE, OPERATIONS, MARKETING, RESEARCH
    level INTEGER NOT NULL DEFAULT 1, -- 0: CEO, 1: Manager, 2: Specialist
    supervisor_id TEXT,
    specialization TEXT NOT NULL,
    allowed_tasks_json TEXT NOT NULL DEFAULT '[]',
    permissions_json TEXT NOT NULL DEFAULT '{}',
    current_status TEXT NOT NULL DEFAULT 'IDLE', -- IDLE, ANALYZING, WORKING, AWAITING_REVIEW, AWAITING_APPROVAL, BLOCKED, OFFLINE
    current_objective TEXT NOT NULL DEFAULT '',
    performance_score REAL NOT NULL DEFAULT 100.0,
    tasks_completed INTEGER NOT NULL DEFAULT 0,
    tasks_failed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    department TEXT NOT NULL,
    task_type TEXT NOT NULL,
    assigned_agent_id TEXT NOT NULL,
    supervisor_id TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, URGENT
    status TEXT NOT NULL DEFAULT 'ASSIGNED', -- ASSIGNED, IN_PROGRESS, AWAITING_REVIEW, REVISION_REQUESTED, AWAITING_APPROVAL, COMPLETED, FAILED, BLOCKED, CANCELLED
    created_day INTEGER NOT NULL,
    deadline_day INTEGER NOT NULL,
    deliverable_json TEXT,
    recommendation_action_json TEXT,
    review_status TEXT NOT NULL DEFAULT 'PENDING',
    review_feedback TEXT,
    revision_count INTEGER NOT NULL DEFAULT 0,
    blocked_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_task_reviews (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    reviewer_agent_id TEXT NOT NULL,
    decision TEXT NOT NULL, -- APPROVED, REVISION_REQUESTED, ESCALATED, REJECTED
    feedback TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 100.0,
    day INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

MIGRATION_STMTS = [
    "ALTER TABLE daily_snapshots ADD COLUMN wages_paid REAL NOT NULL DEFAULT 0.0",
    "ALTER TABLE daily_snapshots ADD COLUMN marketing_spend REAL NOT NULL DEFAULT 0.0",
    "ALTER TABLE daily_snapshots ADD COLUMN rd_spend REAL NOT NULL DEFAULT 0.0",
    "ALTER TABLE daily_snapshots ADD COLUMN headcount INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE daily_snapshots ADD COLUMN distress_stage TEXT NOT NULL DEFAULT 'HEALTHY'",
]

def get_db_connection(db_path: Path | str = "simcorp.db") -> sqlite3.Connection:
    """Creates a connection with row factory enabled and foreign keys enforced."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_database(db_path: Path | str = "simcorp.db") -> None:
    """Executes schema initialization and safe migrations for existing databases."""
    conn = get_db_connection(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)
        for stmt in MIGRATION_STMTS:
            try:
                conn.execute(stmt)
            except Exception:
                pass  # Column already exists -- safe to ignore
    conn.close()
