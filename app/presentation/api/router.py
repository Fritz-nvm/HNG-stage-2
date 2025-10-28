from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from fastapi import status

# Imports from core layers
from app.domain.entities import Country
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
)
from app.presentation.api.dto import CountryResponse, StatusResponse
from app.infrastructure.DI import get_db
from app.domain.repositories import (
    AbstractCountryPersistence,
    AbstractCountryDataSource,
    AbstractCurrencyService,
)
from sqlalchemy.orm import Session
from app.config import get_db_session


router = APIRouter()


# --- Persistence Dependency ---
def get_country_persistence_repo(
    # The session is now injected by the new provider function
    db_session: Session = Depends(get_db_session),
) -> AbstractCountryPersistence:
    """Provides the concrete database repository."""
    return SQLCountryRepository(db_session=db_session)


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
def list_countries(
    region: Optional[str] = Query(None, description="Filter by region (e.g., Africa)"),
    currency: Optional[str] = Query(
        None, description="Filter by currency code (e.g., NGN)"
    ),
    sort: Optional[str] = Query(
        None, description="Sort order: 'gdp_desc' or 'pop_desc'"
    ),
    service: GetCountriesService = Depends(get_countries_service),
):
    # Construct filters dictionary only with non-None values
    filters = {}
    if region:
        filters["region"] = region
    if currency:
        filters["currency"] = currency

    return service.execute(filters=filters, sort=sort)


@router.get("/countries/{name}", response_model=CountryResponse)
def get_country_by_name(
    name: str,
    service: GetCountryByNameService = Depends(get_country_by_name_service),
):
    country = service.execute(name=name)
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Country '{name}' not found."
        )
    return country


# --- DELETE /countries/:name (Delete One) ---
@router.delete("/countries/{name}", status_code=status.HTTP_200_OK)
def delete_country_by_name(
    name: str,
    service: DeleteCountryService = Depends(get_delete_country_service),
):
    success = service.execute(name=name)
    if not success:
        # If the service returns False, the country was not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country '{name}' not found for deletion.",
        )

    return {"message": f"Successfully deleted country: {name}"}


@router.post("/countries/refresh", status_code=status.HTTP_200_OK)
def refresh_country_data(
    service: RefreshCountriesService = Depends(get_refresh_service),
):
    count = service.execute()
    return {"message": f"Successfully refreshed and saved {count} countries."}


@router.get("/status", response_model=StatusResponse, status_code=status.HTTP_200_OK)
def get_api_status(service: GetStatusService = Depends(get_status_service)):
    """
    Retrieves the total number of countries and the last refresh timestamp.
    """
    # The service returns a dict, which FastAPI validates against StatusResponse
    return service.execute()
