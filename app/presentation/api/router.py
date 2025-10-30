from fastapi import APIRouter, Depends, HTTPException, Query, status

from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
from fastapi import status
import os

# Imports from core layers
from app.application.services import (
    RefreshCountriesService,
    GetStatusService,
    DeleteCountryService,
    GetCountryByNameService,
    GetCountriesService,
)

from app.presentation.api.dto import CountryResponse, StatusResponse
from app.domain.repositories import (
    AbstractImageGenerator,
)
from app.infrastructure.DI import (
    get_countries_service,
    get_country_by_name_service,
    get_delete_country_service,
    get_refresh_countries_service,
    get_status_service,
    get_image_generator,
)

router = APIRouter()


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
