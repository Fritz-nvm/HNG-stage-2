from app.config import SessionLocal
from typing import Generator
from app.application.services import (
    FetchCountriesService,
    RefreshCountriesService,
    GetStatusService,
    DeleteCountryService,
    GetCountryByNameService,
    GetCountriesService,
)
from app.infrastructure.repositories import (
    RestCountriesAdapter,
    SQLCountryRepository,
    OpenERAPIAdapter,
    PillowImageAdapter,
)
from app.domain.repositories import (
    AbstractCountryPersistence,
    AbstractCountryDataSource,
    AbstractCurrencyService,
    AbstractImageGenerator,
)
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query, status


# This is the standard FastAPI pattern for getting a DB session
def get_db() -> Generator:
    """Provides a fresh database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- DI for Persistence (Renamed to match definition) ---
def get_country_persistence_repo(
    db: Session = Depends(get_db),
):  # Assuming get_db is defined elsewhere
    return SQLCountryRepository(db_session=db)


# Currency Service Adapter
def get_currency_service() -> AbstractCurrencyService:
    return OpenERAPIAdapter()  # <-- The new adapter


# --- DI for GET /countries ---
def get_countries_service(
    repo: AbstractCountryPersistence = Depends(get_country_persistence_repo),
) -> GetCountriesService:
    return GetCountriesService(repo=repo)


# --- DI for GET /countries/:name ---
def get_country_by_name_service(
    repo: AbstractCountryPersistence = Depends(get_country_persistence_repo),
) -> GetCountryByNameService:
    return GetCountryByNameService(repo=repo)


# --- DI for DELETE /countries/:name ---
def get_delete_country_service(
    repo: AbstractCountryPersistence = Depends(get_country_persistence_repo),
) -> DeleteCountryService:
    return DeleteCountryService(repo=repo)


def get_country_data_source() -> AbstractCountryDataSource:
    """
    Dependency function that creates and returns the concrete Adapter
    for fetching raw country data.

    This function is the 'bridge' that connects the abstract Port (what the Use Case needs)
    with the concrete Adapter (the external HTTP detail).
    """
    return RestCountriesAdapter()


def get_status_service(
    persistence_repo: AbstractCountryPersistence = Depends(
        get_country_persistence_repo
    ),
) -> GetStatusService:
    """Provides the GetStatusService instance."""
    return GetStatusService(persistence_repo=persistence_repo)


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


# --- DI for Image Generation ---
def get_image_generator() -> AbstractImageGenerator:
    """Provides the concrete Pillow implementation."""
    return PillowImageAdapter()


# --- Dependency Injection Configuration for Refresh Service ---
def get_refresh_countries_service(
    fetch_service: FetchCountriesService = Depends(get_fetch_countries_service),
    persistence_repo: AbstractCountryPersistence = Depends(
        get_country_persistence_repo  # ✅ Use the consistent dependency name
    ),
    # 💥 CRITICAL ADDITION 💥
    image_generator: AbstractImageGenerator = Depends(get_image_generator),
) -> RefreshCountriesService:
    """
    Provides the RefreshCountriesService instance with all required dependencies.
    """
    # 💥 CRITICAL FIX: PASS ALL REQUIRED ARGUMENTS 💥
    return RefreshCountriesService(
        fetch_service=fetch_service,
        persistence_repo=persistence_repo,
        image_generator=image_generator,  # <-- Must pass the new dependency
    )


def get_refresh_service(
    fetch_service: FetchCountriesService = Depends(
        get_fetch_countries_service
    ),  # Assuming this dependency exists
    persistence_repo: AbstractCountryPersistence = Depends(
        get_country_persistence_repo
    ),  # Assuming this dependency exists
    # 💥 CRITICAL FIX: Add the missing image generator dependency
    image_generator: AbstractImageGenerator = Depends(get_image_generator),
):
    # 💥 CRITICAL FIX: Pass all three required arguments to the constructor
    return RefreshCountriesService(
        fetch_service, persistence_repo, image_generator  # 👈 Now included
    )
