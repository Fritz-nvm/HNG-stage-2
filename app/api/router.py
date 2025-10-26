from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional, Dict, Any

# Import Service and Exceptions from Application Layer
from application.services import (
    CountryService,
    ServiceUnavailableError,
    CountryNotFoundError,
)

# Import Pydantic models from the new schemas file
from .schemas import CountryResponse, StatusResponse


# --- Router Setup and Dependency ---

router = APIRouter()


# This dependency is injected at the endpoint level in main.py
def get_country_service(service: CountryService = Depends()) -> CountryService:
    return service


# --- Endpoints ---


@router.post(
    "/countries/refresh",
    response_model=StatusResponse,
    summary="Refresh Country Data Cache",
)
async def refresh_cache(service: CountryService = Depends(get_country_service)):
    """Fetches country and exchange data, processes it, and caches it in the database."""
    try:
        # Service call handles all logic, error handling is done here
        status_data = service.refresh_cache()
        return status_data
    except ServiceUnavailableError as e:
        # Maps application exception to 503 HTTP response
        return JSONResponse(
            status_code=503,
            content={
                "error": "External data source unavailable",
                "details": f"Could not fetch data from {e.source}",
            },
        )
    except Exception:
        # General catch-all for unexpected errors
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@router.get(
    "/countries",
    response_model=List[CountryResponse],
    summary="Get All Cached Countries",
)
async def get_all_countries(
    region: Optional[str] = Query(None, description="Filter by region (e.g., Africa)"),
    currency: Optional[str] = Query(
        None, description="Filter by currency code (e.g., NGN)"
    ),
    sort: Optional[str] = Query(
        None,
        regex="^(gdp|population|name)_(asc|desc)$",
        description="Sort by field: gdp_desc, name_asc, etc.",
    ),
    service: CountryService = Depends(get_country_service),
):
    """
    Retrieves all countries from the cache. Supports filtering by region/currency
    and sorting by estimated_gdp, population, or name.
    """
    # Note: Input validation for sort parameter is handled by the regex in Query
    countries = service.get_all_countries(region, currency, sort)
    return countries


@router.get(
    "/countries/{name}", response_model=CountryResponse, summary="Get Country by Name"
)
async def get_country_by_name(
    name: str, service: CountryService = Depends(get_country_service)
):
    """Retrieves a single country record by its name (case-insensitive)."""
    try:
        country_data = service.get_country_by_name(name)
        # Manually convert datetime object in data to string for Pydantic model
        country_data["last_refreshed_at"] = (
            country_data["last_refreshed_at"].isoformat("T", "seconds") + "Z"
        )
        return country_data
    except CountryNotFoundError:
        # Maps application exception to 404 HTTP response
        return JSONResponse(status_code=404, content={"error": "Country not found"})


@router.delete("/countries/{name}", status_code=204, summary="Delete Country by Name")
async def delete_country_by_name(
    name: str, service: CountryService = Depends(get_country_service)
):
    """Deletes a single country record by its name (case-insensitive)."""
    try:
        service.delete_country_by_name(name)
        return {"message": "Successfully deleted"}
    except CountryNotFoundError:
        # Maps application exception to 404 HTTP response
        return JSONResponse(status_code=404, content={"error": "Country not found"})


@router.get("/status", response_model=StatusResponse, summary="Get API Cache Status")
async def get_status(service: CountryService = Depends(get_country_service)):
    """Returns the total number of cached countries and the last refresh time."""
    return service.get_status()


@router.get("/countries/image", summary="Serve Summary Image")
async def get_summary_image(service: CountryService = Depends(get_country_service)):
    """Serves the generated cache summary image (PNG)."""
    image_path = service.get_summary_image_path()

    if image_path:
        # FileResponse handles setting Content-Type (image/png)
        return FileResponse(image_path, media_type="image/png")
    else:
        # Handle case where the image file does not exist
        return JSONResponse(
            status_code=404, content={"error": "Summary image not found"}
        )
