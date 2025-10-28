import requests
from typing import List, Dict, Any
from app.domain.repositories import (
    AbstractCountryPersistence,
    AbstractCountryDataSource,
    AbstractCurrencyService,
)
from app.domain.entities import Country
from app.domain.repositories import AbstractCountryPersistence
from app.infrastructure.models import CountryModel
from sqlalchemy.orm import Session
from app.domain.exceptions import DomainError  # <-- This line is needed!
import os
from dotenv import load_dotenv

load_dotenv()


class RestCountriesAdapter(AbstractCountryDataSource):
    """
    Adapter: Implements the Port using the actual REST Countries API.
    """

    def __init__(self):
        # The specific URL is an implementation detail!
        self.url = os.environ.get("COUNTRIES_API_URL")
        self.fields = "name,capital,region,population,flag,currencies"

    def fetch_all_countries_raw(self) -> List[Dict[str, Any]]:
        """
        Connects to the external API and returns the raw JSON data.
        """
        try:
            response = requests.get(self.url, params={"fields": self.fields})
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            # You should raise a DomainError here instead of printing
            print(f"Error fetching data from REST Countries: {e}")
            return []  # Return empty list on failure for simplicity here


class SQLCountryRepository(AbstractCountryPersistence):
    """Adapter that implements the persistence Port using SQLAlchemy."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_all_countries(self) -> List[Country]:
        """Retrieves all Models, converts them back to Entities."""
        models = self.db.query(CountryModel).all()

        countries: List[Country] = []
        for model in models:
            # 1. Get the dictionary representation of the Model
            model_data = model.__dict__

            # 2. **CRITICAL FIX:** Remove the SQLAlchemy internal metadata key
            #    The .pop() method safely removes the key if it exists.
            model_data.pop("_sa_instance_state", None)

            # 3. Create the Domain Entity using the cleaned data
            countries.append(Country(**model_data))

        return countries

    def save_countries(self, countries: List[Country]) -> None:
        """Converts Entities to Models and saves them to the DB."""
        # Clear existing data (optional, for refresh)
        self.db.query(CountryModel).delete()
        self.db.commit()

        # Convert each Domain Entity to a SQLAlchemy Model instance
        models_to_save = [CountryModel(**country.__dict__) for country in countries]

        self.db.bulk_save_objects(models_to_save)
        self.db.commit()


class OpenERAPIAdapter(AbstractCurrencyService):
    """
    Adapter: Implements the Port using the Open ER API.
    """

    def __init__(self):
        # Configuration detail
        self.url = os.environ.get("EXCHANGE_RATE_API_URL")

    def get_exchange_rate(self, target_code: str) -> float:
        """
        Fetches all rates and returns the specific target rate.
        Note: Caches could be added here for performance, but we skip that for now.
        """
        try:
            # We fetch all rates from the USD base endpoint once
            response = requests.get(self.url)
            response.raise_for_status()
            data = response.json()

            # Error checking on the API response itself
            if data.get("result") != "success":
                raise DomainError("External currency API reported failure.")

            # Look up the rate from the fetched dictionary
            rates = data.get("rates", {})

            # The rate from USD to USD is 1.0 (handled here for safety)
            if target_code == "USD":
                return 1.0

            rate = rates.get(target_code.upper())

            if rate is None:
                # If the currency code is invalid or missing in the response
                raise DomainError(
                    f"Exchange rate not found for currency code: {target_code}"
                )

            return float(rate)

        except requests.exceptions.RequestException as e:
            # Catch network errors and translate them to a Domain Error
            raise DomainError(f"External currency service unavailable or failed: {e}")
