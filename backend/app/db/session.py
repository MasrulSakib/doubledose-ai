
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=2,
    pool_recycle=300,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session to a request and then close it."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def test_database_connection() -> str:
    """Verify that the database is reachable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return "Database connection successful"
