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
    currency_code: str
    exchange_rate: float
    estimated_gdp: float
    flag_url: Optional[str]
    last_refreshed_at: datetime

    # Allows Pydantic to read ORM-like objects (Entities)
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
