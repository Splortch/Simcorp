"""Regression tests for SQLite schema migration error handling."""
from pathlib import Path

import pytest

from simcorp.engine import db


def test_unexpected_migration_error_is_raised(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        db,
        "MIGRATION_STMTS",
        ["ALTER TABLE table_that_does_not_exist ADD COLUMN unexpected TEXT"],
    )

    with pytest.raises(db.sqlite3.OperationalError, match="no such table"):
        db.initialize_database(tmp_path / "broken.db")
