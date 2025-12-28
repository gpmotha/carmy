"""Database setup and session management."""

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def get_database_path() -> Path:
    """Get the default database path."""
    return Path.cwd() / "carmy.db"


def get_engine(database_url: str | None = None):
    """Create and return a SQLAlchemy engine.

    Args:
        database_url: Database URL. Defaults to sqlite:///carmy.db
    """
    if database_url is None:
        database_url = f"sqlite:///{get_database_path()}"
    return create_engine(database_url, echo=False)


def get_session(database_url: str | None = None) -> Generator[Session, None, None]:
    """Get a database session.

    Args:
        database_url: Database URL. Defaults to sqlite:///carmy.db

    Yields:
        SQLAlchemy session
    """
    engine = get_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db(database_url: str | None = None) -> None:
    """Initialize the database by creating all tables.

    Args:
        database_url: Database URL. Defaults to sqlite:///carmy.db
    """
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
