from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Country:
    """Core Business Object: A Country."""

    name: str
    population: int
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    estimated_gdp: Optional[float] = None

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    last_refreshed_at: datetime = field(default_factory=datetime.utcnow)

    # Optional fields
    capital: Optional[str] = None
    region: Optional[str] = None
    flag_url: Optional[str] = None
