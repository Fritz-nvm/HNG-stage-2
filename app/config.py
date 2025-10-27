from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.models import Base
import dotenv

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
