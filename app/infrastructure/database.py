from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Configuration (Mocking .env load) ---
# Use a persistent SQLite file for the demo, easily swap with MySQL config
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# Database setup
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Helper function to create the tables upon startup
def create_db_and_tables():
    """Creates the database and all tables defined in Base."""
    Base.metadata.create_all(bind=engine)
