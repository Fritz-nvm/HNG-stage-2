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
from app.domain.exceptions import DomainError
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy import func

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

    # --- NEW METHOD: GET ALL COUNTRIES (with filters/sorting) ---
    def get_countries(self, filters: dict, sort_by: Optional[str]) -> List[Country]:
        query = self.db.query(CountryModel)

        # 1. Apply Filters
        if "region" in filters:
            query = query.filter(CountryModel.region == filters["region"])
        if "currency" in filters:
            query = query.filter(CountryModel.currency_code == filters["currency"])

        # 2. Apply Sorting
        if sort_by == "gdp_desc":
            # Use desc() for descending order; nullsfirst ensures null GDP values are last
            query = query.order_by(CountryModel.estimated_gdp.desc().nullsfirst())
        elif sort_by == "pop_desc":
            query = query.order_by(CountryModel.population.desc())
        # Add other sorting options as needed

        # 3. Execute and Convert
        models = query.all()
        return [self._to_entity(model) for model in models]

    # --- NEW METHOD: GET ONE COUNTRY BY NAME ---
    def get_country_by_name(self, name: str) -> Optional[Country]:
        model = self.db.query(CountryModel).filter(CountryModel.name == name).first()
        if model:
            return self._to_entity(model)
        return None

    # --- NEW METHOD: DELETE COUNTRY BY NAME ---
    def delete_country_by_name(self, name: str) -> bool:
        # Use a filter and the delete method
        delete_count = (
            self.db.query(CountryModel)
            .filter(CountryModel.name == name)
            .delete(
                synchronize_session="fetch"  # Ensures session state is updated immediately
            )
        )

        # ⚠️ CRITICAL: Must commit the change for DELETE operations
        self.db.commit()

        # Returns True if one or more rows were deleted
        return delete_count > 0

    def save_countries(self, countries: List[Country]) -> None:
        """Converts Entities to Models and saves them to the DB."""
        # Clear existing data (optional, for refresh)
        self.db.query(CountryModel).delete()
        self.db.commit()

        # Convert each Domain Entity to a SQLAlchemy Model instance
        models_to_save = [CountryModel(**country.__dict__) for country in countries]

        self.db.bulk_save_objects(models_to_save)
        self.db.commit()

    def get_status(self) -> Tuple[int, Optional[datetime]]:
        """
        Uses the injected session (self.db) to get the total count and max timestamp.
        """
        # CRITICAL FIX: Use the injected session instance (self.db) directly
        result = self.db.query(
            func.count(CountryModel.id).label("count"),
            func.max(CountryModel.last_refreshed_at).label("last_refreshed"),
        ).one()

        total_countries = result.count
        last_refreshed_at = result.last_refreshed

        return total_countries, last_refreshed_at

    def _to_entity(self, model: CountryModel) -> Country:
        """Converts an SQLAlchemy CountryModel instance to a Domain Country Entity."""
        if model is None:
            return None  # Should not happen here, but good practice

        return Country(
            # Core Fields
            id=model.id,
            name=model.name,
            population=model.population,
            # Optional Fields (must match Entity definition)
            currency_code=model.currency_code,
            exchange_rate=model.exchange_rate,
            estimated_gdp=model.estimated_gdp,
            # Other Fields
            capital=model.capital,
            region=model.region,
            flag_url=model.flag_url,
            last_refreshed_at=model.last_refreshed_at,
        )


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
