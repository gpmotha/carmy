"""Add v2 planning columns to meals table.

Migration: 003
Date: 2024-12-28

Adds columns for v2 month-centric planning:
- effort_level: none, quick, medium, big
- good_for_batch: boolean
- reheats_well: boolean
- kid_friendly: boolean
- typical_day: friday, saturday, tuesday, or NULL
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def upgrade(engine: Engine) -> None:
    """Add v2 planning columns to meals table."""
    with engine.connect() as conn:
        # Check existing columns
        result = conn.execute(text("PRAGMA table_info(meals)"))
        columns = {row[1] for row in result.fetchall()}

        # Add effort_level (default: medium)
        if "effort_level" not in columns:
            conn.execute(
                text("ALTER TABLE meals ADD COLUMN effort_level TEXT DEFAULT 'medium'")
            )

        # Add good_for_batch (default: false)
        if "good_for_batch" not in columns:
            conn.execute(
                text("ALTER TABLE meals ADD COLUMN good_for_batch INTEGER DEFAULT 0")
            )

        # Add reheats_well (default: true)
        if "reheats_well" not in columns:
            conn.execute(
                text("ALTER TABLE meals ADD COLUMN reheats_well INTEGER DEFAULT 1")
            )

        # Add kid_friendly (default: true)
        if "kid_friendly" not in columns:
            conn.execute(
                text("ALTER TABLE meals ADD COLUMN kid_friendly INTEGER DEFAULT 1")
            )

        # Add typical_day (nullable)
        if "typical_day" not in columns:
            conn.execute(
                text("ALTER TABLE meals ADD COLUMN typical_day TEXT DEFAULT NULL")
            )

        conn.commit()

        # Set sensible defaults based on meal characteristics
        _set_default_values(conn)


def _set_default_values(conn) -> None:
    """Set sensible default values based on meal characteristics."""

    # Effort level based on cook_time and meal_type
    # Big effort: cook_time > 60 or stews/goulash types
    conn.execute(text("""
        UPDATE meals SET effort_level = 'big'
        WHERE cook_time_minutes > 60
           OR LOWER(name) LIKE '%goulash%'
           OR LOWER(name) LIKE '%gulyás%'
           OR LOWER(name) LIKE '%stuffed%'
           OR LOWER(name) LIKE '%töltött%'
           OR LOWER(nev) LIKE '%töltött%'
    """))

    # Quick effort: cook_time < 30 and prep_time < 15
    conn.execute(text("""
        UPDATE meals SET effort_level = 'quick'
        WHERE (cook_time_minutes < 30 AND prep_time_minutes < 15)
           OR meal_type = 'salad'
           OR meal_type = 'breakfast'
           OR LOWER(name) LIKE '%sandwich%'
           OR LOWER(name) LIKE '%szendvics%'
    """))

    # No effort: specific types
    conn.execute(text("""
        UPDATE meals SET effort_level = 'none'
        WHERE LOWER(name) LIKE '%leftover%'
           OR LOWER(name) LIKE '%maradék%'
           OR LOWER(name) LIKE '%takeout%'
           OR LOWER(name) LIKE '%takeaway%'
    """))

    # Good for batch: high keeps_days meals and stews
    conn.execute(text("""
        UPDATE meals SET good_for_batch = 1
        WHERE keeps_days >= 3
           OR meal_type = 'soup'
           OR LOWER(name) LIKE '%stew%'
           OR LOWER(name) LIKE '%pörkölt%'
           OR LOWER(name) LIKE '%curry%'
           OR LOWER(name) LIKE '%goulash%'
    """))

    # Reheats well: most things do, but not salads or eggs
    conn.execute(text("""
        UPDATE meals SET reheats_well = 0
        WHERE meal_type = 'salad'
           OR LOWER(name) LIKE '%salad%'
           OR LOWER(name) LIKE '%saláta%'
           OR LOWER(name) LIKE '%egg%'
           OR LOWER(name) LIKE '%tojás%'
           OR LOWER(name) LIKE '%fried%egg%'
    """))

    # Kid friendly: assume most are, but mark spicy or complex as not
    conn.execute(text("""
        UPDATE meals SET kid_friendly = 0
        WHERE LOWER(name) LIKE '%spicy%'
           OR LOWER(name) LIKE '%csípős%'
           OR LOWER(name) LIKE '%hot%pepper%'
    """))

    # Typical day: saturday for big cooks
    conn.execute(text("""
        UPDATE meals SET typical_day = 'saturday'
        WHERE effort_level = 'big'
    """))

    # Typical day: friday for fun foods
    conn.execute(text("""
        UPDATE meals SET typical_day = 'friday'
        WHERE LOWER(name) LIKE '%pizza%'
           OR LOWER(name) LIKE '%burger%'
           OR LOWER(name) LIKE '%fish%friday%'
           OR LOWER(name) LIKE '%hal%'
    """))

    conn.commit()


def downgrade(engine: Engine) -> None:
    """Remove v2 planning columns.

    Note: SQLite doesn't support DROP COLUMN before version 3.35.0.
    """
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE meals DROP COLUMN effort_level"))
            conn.execute(text("ALTER TABLE meals DROP COLUMN good_for_batch"))
            conn.execute(text("ALTER TABLE meals DROP COLUMN reheats_well"))
            conn.execute(text("ALTER TABLE meals DROP COLUMN kid_friendly"))
            conn.execute(text("ALTER TABLE meals DROP COLUMN typical_day"))
            conn.commit()
        except Exception:
            pass
