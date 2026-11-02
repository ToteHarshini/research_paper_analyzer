import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load .env.local if present, then fallback to .env
load_dotenv(".env.local")
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
else:
    engine = None
    SessionLocal = None


class Base(DeclarativeBase):
    pass


def configure_database(url: str):
    """
    Configure or reconfigure the database engine and session factory.
    Enables testing with SQLite in-memory or alternative URLs.
    """
    global engine, SessionLocal, DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    DATABASE_URL = url
    engine = create_engine(url, pool_pre_ping=True, echo=False)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    return engine


def get_db():
    """FastAPI dependency for yielding request-scoped database sessions."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not found in environment (.env or .env.local)")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for obtaining a database session outside of web requests."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not found in environment (.env or .env.local)")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    if engine is None:
        print("Database connection failed: DATABASE_URL not set in environment.")
        return False
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT current_database(), current_user")
            )
            database, user = result.fetchone()

            print("Neon connection successful!")
            print(f"Database: {database}")
            print(f"User: {user}")
            return True

    except Exception as error:
        print("Database connection failed!")
        print(f"Error: {error}")
        return False


if __name__ == "__main__":
    test_connection()
