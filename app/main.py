import random
from datetime import datetime
from typing import List, Optional, Dict, Any

# SQLAlchemy imports for database ORM
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    BigInteger,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm.session import Session

# --- Configuration (Mocking .env load) ---
# In a real app, this would be loaded from .env
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"  # Persistent SQLite for demo
# For MySQL, it would be: "mysql+pymysql://user:password@host/dbname"

# Database setup
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models (Entities) ---


class Country(Base):
    """Database model for country data cache."""

    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    capital = Column(String, nullable=True)
    region = Column(String, nullable=True)
    population = Column(BigInteger, nullable=False)
    currency_code = Column(String, nullable=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(String, nullable=True)
    last_refreshed_at = Column(DateTime, nullable=False)


class Status(Base):
    """Database model for global API status tracking."""

    __tablename__ = "status"

    id = Column(Integer, primary_key=True)
    total_countries = Column(Integer, default=0)
    last_refreshed_at = Column(DateTime, default=datetime.min)
