from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from .database import Base  # Import Base from our new database setup file

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
    last_refreshed_at = Column(DateTime, default=None)
