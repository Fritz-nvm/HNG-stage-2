from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# --- Response DTO (Pydantic Model) ---
class CountryResponse(BaseModel):
    id: str
    name: str
    capital: Optional[str]
    region: Optional[str]
    population: int
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    estimated_gdp: Optional[float] = None
    flag_url: Optional[str]
    last_refreshed_at: datetime

    # Allows Pydantic to read ORM-like objects (Entities)
    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class StatusResponse(BaseModel):
    total_countries: int
    # Optional because the table might be empty, resulting in a NULL timestamp
    last_refreshed_at: Optional[datetime] = None
