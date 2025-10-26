import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Configuration (Loaded from .env) ---
# Retrieve the database connection URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DB_URL", "sqlite:///./default.db")

# Database setup
# connect_args={"check_same_thread": False} is required for SQLite only
# For MySQL, this should be omitted.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Helper function to create the tables upon startup
def create_db_and_tables():
    """Creates the database and all tables defined in Base."""
    Base.metadata.create_all(bind=engine)
