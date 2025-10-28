from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.domain.entities import Country


class AbstractCountryPersistence(ABC):
    """
    Port: Defines the contract for persistence (saving/loading Countries).
    """

    @abstractmethod
    def save_countries(self, countries: List[Country]) -> None:
        """Saves a list of Country entities to the persistence layer."""
        raise NotImplementedError

    @abstractmethod
    def get_all_countries(self) -> List[Country]:
        """Retrieves all Country entities."""
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
