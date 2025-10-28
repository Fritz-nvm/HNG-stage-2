from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.models import Base
from typing import Generator
from sqlalchemy.orm import Session

# Use SQLite for simple setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./countries.db"

# engine = the connection point to the database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite/FastAPI
)

# SessionLocal = the actual database session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Function to create tables
def init_db():
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency function to manage the lifecycle of a database session.
    It creates a session, yields it to the caller, and ensures it's closed.
    """
    db = SessionLocal()  # Create a new session instance
    try:
        yield db  # Pass the session to the repository/service
    finally:
        db.close()  # Ensure the session is closed after use
