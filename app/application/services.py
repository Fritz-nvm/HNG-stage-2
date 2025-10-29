import random
import uuid
import asyncio
from typing import List, Optional, Dict
from app.domain.entities import Country
from app.domain.repositories import (
    AbstractCountryDataSource,
    AbstractCountryPersistence,
    AbstractCurrencyService,
    AbstractImageGenerator,
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

    # 1. 💥 CRITICAL FIX: Make the method ASYNC 💥
    async def execute(self) -> List[Country]:
        # AWAIT the call to the now-async data source
        raw_data = await self.data_source.fetch_all_countries_raw()
        countries: List[Country] = []
        unique_currency_codes = set()

        # --- Pre-processing to collect ALL unique currency codes ---
        for item in raw_data:
            currencies = item.get("currencies")
            if currencies and len(currencies) > 0 and currencies[0].get("code"):
                unique_currency_codes.add(currencies[0].get("code"))

        # 2. 💥 CRITICAL FIX: Make ONE consolidated API call for ALL rates 💥
        # We assume the currency service now has a bulk async method

        # This is a hypothetical new async method on the service:
        cached_rates = await self._get_all_exchange_rates_async(unique_currency_codes)

        # If your currency service only supports one call per currency,
        # use asyncio.gather to make them concurrently (much slower than a consolidated call).

        # --- Process Data ---

        for item in raw_data:
            # --- 1. DATA EXTRACTION & VALIDATION (Unchanged) ---
            name = item.get("name")
            population = item.get("population")
            currencies = item.get("currencies")

            if not name or population is None or population < 0:
                print(f"WARN: Skipping record due to invalid name/population: {name}")
                continue

            currency_code: Optional[str] = None
            exchange_rate: Optional[float] = None
            estimated_gdp: Optional[float] = None

            # --- 2. CURRENCY EXTRACTION ---
            if currencies and len(currencies) > 0 and currencies[0].get("code"):
                currency_code = currencies[0].get("code")

            if not currency_code:
                estimated_gdp = 0.0  # Rule: Set to 0 if no currency

            # --- 3. EXCHANGE RATE LOOKUP & FAILURE HANDLING ---

            if currency_code:
                # 💥 CRITICAL FIX: Look up rate from the pre-fetched map 💥
                rate = cached_rates.get(currency_code)

                if rate is not None:
                    # SUCCESS: Assign rate and compute GDP
                    exchange_rate = rate
                    gdp_factor = random.uniform(1000, 2000)
                    estimated_gdp = (population * gdp_factor) / exchange_rate
                else:
                    # Rule: If rate failed to fetch during the bulk call, set to None
                    print(f"WARN: Rate missing for {currency_code}. Storing nulls.")
                    pass

            # --- 4. CREATE THE CORE ENTITY (Unchanged) ---
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

    # Helper method to call the exchange service
    async def _get_all_exchange_rates_async(
        self, codes: set
    ) -> Dict[str, Optional[float]]:
        # This is a mock implementation. You need to implement this logic
        # either by making ONE call to your exchange rate adapter,
        # or by using asyncio.gather to call self.currency_service.get_exchange_rate for each code concurrently.

        # ⚠️ ASSUME 1: Your exchange service adapter has an async bulk method:
        # return await self.currency_service.get_rates_for_codes(codes)

        # ⚠️ ASSUME 2: If you must call the endpoint individually (slower but concurrent):
        tasks = [self.currency_service.get_exchange_rate(code) for code in codes]
        # Wrap in dict comprehension for easy lookup later
        results = await asyncio.gather(*tasks, return_exceptions=True)

        rates = {}
        for code, result in zip(codes, results):
            if isinstance(result, DomainError) or isinstance(result, Exception):
                print(f"WARN: Async rate fetch failed for {code}: {result}")
                rates[code] = None
            else:
                rates[code] = result
        return rates


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
        image_generator: AbstractImageGenerator,
    ):  # Inject the saving logic
        self.fetch_service = fetch_service
        self.persistence_repo = persistence_repo
        self.image_generator = image_generator

    async def execute(self) -> int:
        # 2. 💥 CRITICAL FIX: AWAIT the asynchronous fetch service 💥
        countries = await self.fetch_service.execute()

        # Persistence is already FAST due to bulk operations (no await needed here)
        count = self.persistence_repo.save_countries(countries)

        # 2. Retrieve Status Data for Image Generation
        total, last_refresh_time = self.persistence_repo.get_status()

        all_countries = self.persistence_repo.get_countries(
            filters={}, sort_by="gdp_desc"
        )
        top_gdp = [
            {"name": c.name, "estimated_gdp": c.estimated_gdp}
            for c in all_countries[:5]
            if c is not None
        ]

        # 3. Generate and Save Image
        if last_refresh_time:
            # Image generation is usually CPU-bound and fast, no need for await unless designed async
            self.image_generator.generate_summary_image(
                total_countries=total,
                top_gdp_countries=top_gdp,
                last_refreshed_at=last_refresh_time,
            )

        return count


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
