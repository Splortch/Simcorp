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

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day INTEGER NOT NULL,
    category TEXT NOT NULL, -- SYSTEM, FINANCE, OPERATIONS, MARKETING, RESEARCH, AI
    severity TEXT NOT NULL DEFAULT 'INFO', -- INFO, WARNING, SUCCESS, DANGER
    message TEXT NOT NULL,
    details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def get_db_connection(db_path: Path | str = "simcorp.db") -> sqlite3.Connection:
    """Creates a connection with row factory enabled and foreign keys enforced."""
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_database(db_path: Path | str = "simcorp.db") -> None:
    """Executes schema initialization."""
    conn = get_db_connection(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)
    conn.close()
