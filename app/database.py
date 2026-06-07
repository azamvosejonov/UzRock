from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/uzrock_db"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,          # auto-reconnect on stale connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
