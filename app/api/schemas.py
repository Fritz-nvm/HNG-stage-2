from pydantic import BaseModel
from typing import Optional, Dict, Any


class CountryBase(BaseModel):
    """Base structure for country data."""

    name: str
    population: int
    currency_code: Optional[str] = None


class CountryResponse(CountryBase):
    """Full response model for a cached country record."""

    id: int
    capital: Optional[str]
    region: Optional[str]
    exchange_rate: Optional[float]
    estimated_gdp: Optional[float]
    flag_url: Optional[str]
    # last_refreshed_at will be a string in the API response (ISO format)
    last_refreshed_at: str

    class Config:
        """Pydantic configuration."""

        # Allows Pydantic to read SQLAlchemy ORM objects directly
        from_attributes = True


class StatusResponse(BaseModel):
    """Response model for the GET /status endpoint."""

    total_countries: int
    last_refreshed_at: str


class ErrorResponse(BaseModel):
    """Generic model for structured error responses (400, 404, 503)."""

    error: str
    details: Optional[Dict[str, str]] = None
