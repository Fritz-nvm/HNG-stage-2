from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.domain.entities import Country
from datetime import datetime
from typing import Optional, Tuple


class AbstractCountryPersistence(ABC):
    """
    Port: Defines the contract for persistence (saving/loading Countries).
    """

    @abstractmethod
    def save_countries(self, countries: List[Country]) -> None:
        """Saves a list of Country entities to the persistence layer."""
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> Tuple[int, Optional[datetime]]:
        """
        Retrieves the total number of countries and the latest
        last_refreshed_at timestamp.
        Returns: (total_count, last_refreshed_at)
        """
        raise NotImplementedError


class AbstractCountryDataSource(ABC):
    """
    Port: Contract for fetching raw country data from an external source.
    """

    @abstractmethod
    def fetch_all_countries_raw(self) -> List[Dict[str, Any]]:
        """
        Fetches raw data structured as a list of dictionaries.
        """
        raise NotImplementedError


class AbstractCurrencyService(ABC):
    """
    Port: Contract for fetching currency exchange rates.
    """

    @abstractmethod
    def get_exchange_rate(self, target_code: str) -> float:
        """
        Retrieves the exchange rate from the base currency (USD)
        to the target currency code (e.g., EUR).
        """
        raise NotImplementedError


class AbstractImageGenerator(ABC):
    """Port for generating and saving the country summary image."""

    @abstractmethod
    def generate_summary_image(
        self,
        total_countries: int,
        top_gdp_countries: List[Dict],
        last_refreshed_at: datetime,
    ) -> str:
        """
        Generates the summary image and returns the file path.
        """
        raise NotImplementedError

    @abstractmethod
    def get_image_path(self) -> str:
        """Returns the expected path to the summary image."""
        raise NotImplementedError
