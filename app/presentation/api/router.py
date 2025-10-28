from fastapi import APIRouter, Depends
from typing import List
from fastapi import status

# Imports from core layers
from app.domain.entities import Country
from app.application.services import FetchCountriesService, RefreshCountriesService
from app.infrastructure.repositories import (
    RestCountriesAdapter,
    SQLCountryRepository,
    OpenERAPIAdapter,
)
from app.presentation.api.dto import CountryResponse
from app.infrastructure.DI import get_db
from app.domain.repositories import (
    AbstractCountryPersistence,
    AbstractCountryDataSource,
    AbstractCurrencyService,
)
from sqlalchemy.orm import Session


router = APIRouter()


# Currency Service Adapter
def get_currency_service() -> AbstractCurrencyService:
    return OpenERAPIAdapter()  # <-- The new adapter


def get_country_data_source() -> AbstractCountryDataSource:
    """
    Dependency function that creates and returns the concrete Adapter
    for fetching raw country data.

    This function is the 'bridge' that connects the abstract Port (what the Use Case needs)
    with the concrete Adapter (the external HTTP detail).
    """
    return RestCountriesAdapter()


# --- Dependency Injection Configuration ---
# In a real app, this would be cleaner (as taught in Lesson 4)
def get_fetch_countries_service(
    data_source: AbstractCountryDataSource = Depends(get_country_data_source),
    currency_service: AbstractCurrencyService = Depends(
        get_currency_service
    ),  # <-- NEW INJECTION
) -> FetchCountriesService:
    return FetchCountriesService(
        data_source=data_source,
        currency_service=currency_service,  # <-- Passed to the Use Case
    )


# --- DI for Persistence ---
def get_country_persistence_repo(db: Session = Depends(get_db)):
    return SQLCountryRepository(db_session=db)


def get_refresh_service(
    fetch_service: FetchCountriesService = Depends(get_fetch_countries_service),
    persistence_repo: AbstractCountryPersistence = Depends(
        get_country_persistence_repo
    ),
) -> RefreshCountriesService:
    return RefreshCountriesService(fetch_service, persistence_repo)


# --- FastAPI Endpoint ---
@router.get("/countries", response_model=List[CountryResponse])
def get_all_countries_data(
    # Now depends on the Persistence Repository
    persistence_repo: AbstractCountryPersistence = Depends(
        get_country_persistence_repo
    ),
):
    # 1. Call the Persistence Port to get stored data
    countries_entities: List[Country] = persistence_repo.get_all_countries()

    # 2. Return the list of Entities
    return countries_entities


@router.post("/countries/refresh", status_code=status.HTTP_200_OK)
def refresh_country_data(
    service: RefreshCountriesService = Depends(get_refresh_service),
):
    count = service.execute()
    return {"message": f"Successfully refreshed and saved {count} countries."}
