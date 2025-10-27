from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CountryModel(Base):
    """SQLAlchemy ORM Model (Adapter Model)."""

    __tablename__ = "countries"

    # Matches the core Country Entity fields
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    capital = Column(String, nullable=True)
    region = Column(String, nullable=True)
    population = Column(Integer, nullable=False)
    currency_code = Column(String, nullable=False)
    exchange_rate = Column(Float, nullable=False)
    estimated_gdp = Column(Float, nullable=False)
    flag_url = Column(String, nullable=True)
    last_refreshed_at = Column(DateTime, nullable=False)
