"""FastAPI dependencies for Carmy API."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from carmy.models.database import get_engine, init_db


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency.

    Yields a SQLAlchemy session and ensures it's closed after use.
    """
    init_db()
    engine = get_engine()
    with Session(engine) as session:
        yield session
