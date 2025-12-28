"""Add v2 planning tables for month-centric orchestration.

Migration: 004
Date: 2024-12-28

Creates new tables:
- month_plans
- special_dates
- week_skeletons
- cooking_events
- meal_slots
- cooking_rhythm
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def upgrade(engine: Engine) -> None:
    """Create v2 planning tables."""
    with engine.connect() as conn:
        # Create month_plans table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS month_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                theme TEXT,
                season TEXT NOT NULL,
                settings TEXT DEFAULT '{}',
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, month)
            )
        """))

        # Create index for month_plans
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_month_plans_year_month
            ON month_plans(year, month)
        """))

        # Create special_dates table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS special_dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_plan_id INTEGER NOT NULL,
                date DATE NOT NULL,
                event_type TEXT NOT NULL,
                name TEXT,
                affects_cooking INTEGER DEFAULT 1,
                notes TEXT,
                FOREIGN KEY (month_plan_id) REFERENCES month_plans(id) ON DELETE CASCADE
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_special_dates_date
            ON special_dates(date)
        """))

        # Create week_skeletons table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS week_skeletons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month_plan_id INTEGER,
                year INTEGER NOT NULL,
                week_number INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT DEFAULT 'skeleton',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, week_number),
                FOREIGN KEY (month_plan_id) REFERENCES month_plans(id) ON DELETE SET NULL
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_week_skeletons_year_week
            ON week_skeletons(year, week_number)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_week_skeletons_dates
            ON week_skeletons(start_date, end_date)
        """))

        # Create cooking_events table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cooking_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_skeleton_id INTEGER NOT NULL,
                meal_id INTEGER NOT NULL,
                cook_date DATE NOT NULL,
                cook_time TEXT,
                serves_days INTEGER DEFAULT 1,
                portions INTEGER DEFAULT 4,
                effort_level TEXT DEFAULT 'medium',
                event_type TEXT DEFAULT 'regular',
                was_made INTEGER,
                rating INTEGER,
                notes TEXT,
                FOREIGN KEY (week_skeleton_id) REFERENCES week_skeletons(id) ON DELETE CASCADE,
                FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cooking_events_date
            ON cooking_events(cook_date)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cooking_events_week
            ON cooking_events(week_skeleton_id)
        """))

        # Create meal_slots table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meal_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_skeleton_id INTEGER NOT NULL,
                date DATE NOT NULL,
                meal_time TEXT NOT NULL,
                meal_id INTEGER,
                source TEXT DEFAULT 'fresh',
                cooking_event_id INTEGER,
                leftover_day INTEGER,
                status TEXT DEFAULT 'planned',
                notes TEXT,
                UNIQUE(date, meal_time),
                FOREIGN KEY (week_skeleton_id) REFERENCES week_skeletons(id) ON DELETE CASCADE,
                FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE SET NULL,
                FOREIGN KEY (cooking_event_id) REFERENCES cooking_events(id) ON DELETE SET NULL
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_meal_slots_date
            ON meal_slots(date)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_meal_slots_date_time
            ON meal_slots(date, meal_time)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_meal_slots_week
            ON meal_slots(week_skeleton_id)
        """))

        # Create cooking_rhythm table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cooking_rhythm (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week INTEGER NOT NULL,
                cook_probability REAL DEFAULT 0.5,
                typical_effort TEXT,
                typical_types TEXT DEFAULT '[]',
                confidence REAL DEFAULT 0.5,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cooking_rhythm_day
            ON cooking_rhythm(day_of_week)
        """))

        conn.commit()


def downgrade(engine: Engine) -> None:
    """Drop v2 planning tables."""
    with engine.connect() as conn:
        # Drop tables in reverse order of dependencies
        conn.execute(text("DROP TABLE IF EXISTS cooking_rhythm"))
        conn.execute(text("DROP TABLE IF EXISTS meal_slots"))
        conn.execute(text("DROP TABLE IF EXISTS cooking_events"))
        conn.execute(text("DROP TABLE IF EXISTS week_skeletons"))
        conn.execute(text("DROP TABLE IF EXISTS special_dates"))
        conn.execute(text("DROP TABLE IF EXISTS month_plans"))
        conn.commit()
