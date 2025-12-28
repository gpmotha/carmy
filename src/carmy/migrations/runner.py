"""Migration runner for Carmy database."""

import importlib
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from carmy.models.database import get_engine


MIGRATIONS_DIR = Path(__file__).parent


def get_applied_migrations(engine: Engine) -> set[str]:
    """Get set of already applied migration names."""
    with engine.connect() as conn:
        # Create migrations table if it doesn't exist
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS _migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.commit()

        result = conn.execute(text("SELECT name FROM _migrations"))
        return {row[0] for row in result.fetchall()}


def record_migration(engine: Engine, name: str) -> None:
    """Record a migration as applied."""
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO _migrations (name) VALUES (:name)"), {"name": name})
        conn.commit()


def run_migrations(database_url: str | None = None) -> list[str]:
    """Run all pending migrations.

    Returns:
        List of applied migration names.
    """
    engine = get_engine(database_url)
    applied = get_applied_migrations(engine)
    newly_applied = []

    # Find all migration files
    migration_files = sorted(MIGRATIONS_DIR.glob("[0-9]*.py"))

    for migration_file in migration_files:
        migration_name = migration_file.stem

        if migration_name in applied:
            continue

        # Import and run the migration
        module_name = f"carmy.migrations.{migration_name}"
        module = importlib.import_module(module_name)

        if hasattr(module, "upgrade"):
            module.upgrade(engine)
            record_migration(engine, migration_name)
            newly_applied.append(migration_name)

    return newly_applied
