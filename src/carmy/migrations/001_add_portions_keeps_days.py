"""Add default_portions and keeps_days columns to meals table.

Migration: 001
Date: 2024-12-27
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def upgrade(engine: Engine) -> None:
    """Add default_portions and keeps_days columns."""
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(meals)"))
        columns = {row[1] for row in result.fetchall()}

        if "default_portions" not in columns:
            conn.execute(
                text("ALTER TABLE meals ADD COLUMN default_portions INTEGER DEFAULT 1")
            )

        if "keeps_days" not in columns:
            conn.execute(
                text("ALTER TABLE meals ADD COLUMN keeps_days INTEGER DEFAULT 1")
            )

        conn.commit()


def downgrade(engine: Engine) -> None:
    """Remove default_portions and keeps_days columns.

    Note: SQLite doesn't support DROP COLUMN before version 3.35.0.
    For older versions, this would require recreating the table.
    """
    with engine.connect() as conn:
        # SQLite 3.35+ supports DROP COLUMN
        try:
            conn.execute(text("ALTER TABLE meals DROP COLUMN default_portions"))
            conn.execute(text("ALTER TABLE meals DROP COLUMN keeps_days"))
            conn.commit()
        except Exception:
            # Older SQLite versions - would need table recreation
            pass
