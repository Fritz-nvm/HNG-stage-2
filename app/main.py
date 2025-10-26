import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# --- Load Environment Variables ---
# This must be done before components access os.getenv()
load_dotenv()

# Import components from Infrastructure and Application layers
from infrastructure.database import SessionLocal, create_db_and_tables
from infrastructure.repository import CountryRepository
from infrastructure.clients import (
    RestCountriesClient,
    ExchangeRateClient,
    ImageGenerator,
)
from application.services import CountryService

# Import Router from Presentation layer
from api.router import router


# --- FastAPI App Initialization ---
app = FastAPI(
    title="Country Currency & Exchange API",
    description="A RESTful service for cached country and exchange rate data.",
    version="1.0.0",
)


# --- Database Dependency (Infrastructure) ---
def get_db():
    """Dependency function that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Service Dependency Injection (Application) ---
def get_country_service(db: Session = Depends(get_db)) -> CountryService:
    """Dependency that creates and returns the CountryService instance."""
    # 1. Instantiate Infrastructure components (they read config from env)
    repository = CountryRepository(db=db)
    countries_client = RestCountriesClient()
    exchange_client = ExchangeRateClient()
    image_generator = ImageGenerator()

    # 2. Instantiate Application component (Service) with all dependencies injected
    service = CountryService(
        repository=repository,
        countries_client=countries_client,
        exchange_client=exchange_client,
        image_generator=image_generator,
    )
    return service


# Inject the service dependency override into the router
router.dependency_overrides[router.dependencies[0]] = get_country_service


# --- Startup Hook ---
@app.on_event("startup")
def on_startup():
    """Executed when the FastAPI application starts."""
    # 1. Initialize the database schema
    print("Creating database and tables...")
    create_db_and_tables()
    print("Database ready.")


# --- Include Router ---
app.include_router(router)

# To run this locally using the configured port:
# API_PORT is loaded from .env
# uvicorn app.main:app --host 0.0.0.0 --port
# (You'll need to use os.getenv('API_PORT') to dynamically set the port when executing uvicorn.)
