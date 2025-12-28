"""Add portions_remaining, chain_id, cooked_on_date to plan_meals table.

Migration: 002
Date: 2024-12-27
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def upgrade(engine: Engine) -> None:
    """Add chain tracking columns to plan_meals."""
    with engine.connect() as conn:
        # Check existing columns
        result = conn.execute(text("PRAGMA table_info(plan_meals)"))
        columns = {row[1] for row in result.fetchall()}

        if "portions_remaining" not in columns:
            conn.execute(
                text("ALTER TABLE plan_meals ADD COLUMN portions_remaining INTEGER")
            )

        if "chain_id" not in columns:
            conn.execute(
                text("ALTER TABLE plan_meals ADD COLUMN chain_id VARCHAR(36)")
            )

        if "cooked_on_date" not in columns:
            conn.execute(
                text("ALTER TABLE plan_meals ADD COLUMN cooked_on_date DATE")
            )

        conn.commit()


def downgrade(engine: Engine) -> None:
    """Remove chain tracking columns."""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE plan_meals DROP COLUMN portions_remaining"))
            conn.execute(text("ALTER TABLE plan_meals DROP COLUMN chain_id"))
            conn.execute(text("ALTER TABLE plan_meals DROP COLUMN cooked_on_date"))
            conn.commit()
        except Exception:
            pass
