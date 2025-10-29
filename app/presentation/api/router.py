from fastapi import APIRouter, Depends, HTTPException, Query, status

from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
from fastapi import status
import os

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
    PillowImageAdapter,
)
from app.presentation.api.dto import CountryResponse, StatusResponse
from app.infrastructure.DI import get_db
from app.domain.repositories import (
    AbstractCountryPersistence,
    AbstractCountryDataSource,
    AbstractCurrencyService,
    AbstractImageGenerator,
)
from sqlalchemy.orm import Session
from app.config import get_db_session


router = APIRouter()


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
# 💥 CRITICAL FIX 1: Keep the router function ASYNC 💥
async def refresh_data(
    # 💥 CRITICAL FIX 2: Use the unified dependency provider name 💥
    service: RefreshCountriesService = Depends(get_refresh_countries_service),
):
    # 💥 CRITICAL FIX 3: AWAIT the asynchronous service method 💥
    count = await service.execute()
    return {"message": f"Successfully refreshed {count} countries."}


@router.get("/status", response_model=StatusResponse, status_code=status.HTTP_200_OK)
def get_api_status(service: GetStatusService = Depends(get_status_service)):
    """
    Retrieves the total number of countries and the last refresh timestamp.
    """
    # The service returns a dict, which FastAPI validates against StatusResponse
    return service.execute()


# --- GET /countries/image ---
@router.get("/countries/image")
def get_summary_image(generator: AbstractImageGenerator = Depends(get_image_generator)):
    image_path = generator.get_image_path()

    # Convert to absolute path to fix local development issues
    absolute_path = os.path.abspath(image_path)

    print(f"Looking for image at: {absolute_path}")  # Debug info
    print(f"File exists: {os.path.exists(absolute_path)}")  # Debug info

    if not os.path.exists(absolute_path):
        # Provide helpful debug information
        print(f"DEBUG: Current working directory: {os.getcwd()}")
        print(f"DEBUG: Relative path was: {image_path}")

        # Check if cache directory exists
        cache_dir = os.path.dirname(absolute_path)
        if os.path.exists(cache_dir):
            print(f"DEBUG: Cache directory exists. Contents: {os.listdir(cache_dir)}")
        else:
            print(f"DEBUG: Cache directory does not exist: {cache_dir}")

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Summary image not found. Run POST /countries/refresh first.",
                "debug_info": {
                    "requested_path": image_path,
                    "absolute_path": absolute_path,
                    "current_directory": os.getcwd(),
                    "cache_directory_exists": os.path.exists(cache_dir),
                },
            },
        )

    # Serve the file directly using FileResponse
    return FileResponse(
        path=absolute_path, media_type="image/png", filename="summary.png"
    )
