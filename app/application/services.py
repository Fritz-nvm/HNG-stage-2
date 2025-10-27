import random
import uuid
from typing import List
from app.domain.entities import Country
from app.domain.repositories import AbstractCountryDataSource
from app.domain.repositories import AbstractCountryPersistence


class FetchCountriesService:
    def __init__(self, data_source: AbstractCountryDataSource):
        """Injects the dependency (the Port/Adapter)."""
        self.data_source = data_source

    def execute(self, exchange_rate: float = 1.0) -> List[Country]:
        """
        Business Logic: Fetches raw data, computes GDP, and creates Entities.
        """
        raw_data = self.data_source.fetch_all_countries_raw()
        countries: List[Country] = []

        for item in raw_data:
            # --- Data Requirements & Validation ---
            name = item.get("name")
            population = item.get("population")
            currencies = item.get("currencies")

            # Basic Validation/Filtering (Business Rule)
            if not name or population is None or not currencies:
                continue

            # Since the API only returns one currency, we'll take the first one
            currency_code = (
                currencies[0].get("code") if currencies[0].get("code") else "N/A"
            )

            # --- Business Computation ---
            # computed from population × random(1000–2000) ÷ exchange_rate
            gdp_factor = random.uniform(1000, 2000)
            estimated_gdp = (population * gdp_factor) / exchange_rate

            # --- Create the Core Entity ---
            countries.append(
                Country(
                    id=str(uuid.uuid4()),
                    name=name,
                    population=population,
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,  # Using a fixed rate for now
                    estimated_gdp=estimated_gdp,
                    capital=item.get("capital"),
                    region=item.get("region"),
                    flag_url=item.get("flag"),
                )
            )

        return countries


class RefreshCountriesService:
    def __init__(
        self,
        fetch_service: FetchCountriesService,  # Inject the fetching logic
        persistence_repo: AbstractCountryPersistence,
    ):  # Inject the saving logic
        self.fetch_service = fetch_service
        self.persistence_repo = persistence_repo

    def execute(self, exchange_rate: float) -> int:
        """
        Fetches data, saves it to the database, and returns the count.
        """
        # 1. FETCH data using the data source Port/Adapter
        countries = self.fetch_service.execute(exchange_rate=exchange_rate)

        # 2. PERSIST data using the persistence Port/Adapter
        self.persistence_repo.save_countries(countries)

        return len(countries)
