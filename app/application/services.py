import random
import uuid
from typing import List, Optional
from app.domain.entities import Country
from app.domain.repositories import (
    AbstractCountryDataSource,
    AbstractCountryPersistence,
    AbstractCurrencyService,
)
from app.domain.exceptions import DomainError


class FetchCountriesService:
    def __init__(
        self,
        data_source: AbstractCountryDataSource,
        currency_service: AbstractCurrencyService,
    ):
        self.data_source = data_source
        self.currency_service = currency_service

    def execute(self) -> List[Country]:
        raw_data = self.data_source.fetch_all_countries_raw()
        countries: List[Country] = []
        cached_rates = {}

        for item in raw_data:
            # --- 1. DATA EXTRACTION & VALIDATION ---
            name = item.get("name")
            population = item.get(
                "population"
            )  # CRITICAL: Ensure population is extracted
            currencies = item.get("currencies")

            # Basic Validation: Skip record if essential data is missing
            if not name or population is None or population < 0:
                print(f"WARN: Skipping record due to invalid name/population: {name}")
                continue

            # Initialize optional/dynamic fields to None for the current loop iteration
            currency_code: Optional[str] = None
            exchange_rate: Optional[float] = None
            estimated_gdp: Optional[float] = None

            # --- 2. CURRENCY EXTRACTION AND EMPTY ARRAY HANDLING ---

            # Rule: If multiple currencies, store the first one.
            if currencies and len(currencies) > 0 and currencies[0].get("code"):
                currency_code = currencies[0].get("code")
            else:
                # Rule: If currencies array is empty or codes are missing:
                currency_code = None
                exchange_rate = None  # Explicitly set to null (None)
                estimated_gdp = 0.0  # Set estimated_gdp to 0 as required
                # Logic skips to step 4 (Create Entity)

            # --- 3. EXCHANGE RATE LOOKUP & FAILURE HANDLING ---

            # Only proceed if a currency code was successfully extracted
            if currency_code:

                try:
                    # Get rate from cache or call external service
                    if currency_code not in cached_rates:
                        rate = self.currency_service.get_exchange_rate(currency_code)
                        cached_rates[currency_code] = rate
                    else:
                        rate = cached_rates[currency_code]

                    # SUCCESS: Assign rate and compute GDP
                    exchange_rate = rate
                    gdp_factor = random.uniform(1000, 2000)
                    estimated_gdp = (population * gdp_factor) / exchange_rate

                except DomainError as e:
                    # Rule: If currency_code is not found in the exchange rates API:
                    # exchange_rate and estimated_gdp remain None (as initialized)
                    print(
                        f"WARN: Failed to get rate for {currency_code}. Storing nulls. Error: {e}"
                    )
                    pass  # Continue to step 4 with null values

            # --- 4. CREATE THE CORE ENTITY ---
            # This step always runs, fulfilling the "Still store the country record" rule.
            countries.append(
                Country(
                    name=name,
                    population=population,
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,
                    estimated_gdp=estimated_gdp,
                    capital=item.get("capital"),
                    region=item.get("region"),
                    flag_url=item.get("flag"),
                )
            )

        return countries


class GetCountriesService:
    def __init__(self, repo: AbstractCountryPersistence):
        self.repo = repo

    def execute(self, filters: dict, sort: Optional[str]) -> List[Country]:
        """Fetches all countries applying optional filters and sorting."""
        return self.repo.get_countries(filters=filters, sort_by=sort)


class GetCountryByNameService:
    def __init__(self, repo: AbstractCountryPersistence):
        self.repo = repo

    def execute(self, name: str) -> Optional[Country]:
        """Fetches a single country by name."""
        return self.repo.get_country_by_name(name)


class DeleteCountryService:
    def __init__(self, repo: AbstractCountryPersistence):
        self.repo = repo

    def execute(self, name: str) -> bool:
        """Deletes a country record by name."""
        return self.repo.delete_country_by_name(name)


class RefreshCountriesService:
    def __init__(
        self,
        fetch_service: FetchCountriesService,  # Inject the fetching logic
        persistence_repo: AbstractCountryPersistence,
    ):  # Inject the saving logic
        self.fetch_service = fetch_service
        self.persistence_repo = persistence_repo

    def execute(self) -> int:
        """
        Fetches data, saves it to the database, and returns the count.
        """
        # 1. FETCH data using the data source Port/Adapter
        countries = self.fetch_service.execute()

        # 2. PERSIST data using the persistence Port/Adapter
        self.persistence_repo.save_countries(countries)

        return len(countries)


class GetStatusService:
    def __init__(self, persistence_repo: AbstractCountryPersistence):
        """Injects the dependency (Persistence Port)."""
        self.persistence_repo = persistence_repo

    def execute(self) -> dict:
        """Retrieves and formats the API status data."""
        total_countries, last_refreshed_at = self.persistence_repo.get_status()

        # Format the result to match the required output keys
        return {
            "total_countries": total_countries,
            "last_refreshed_at": last_refreshed_at,
        }
