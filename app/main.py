from fastapi import FastAPI
from app.presentation.api.router import router as country_router
from app.config import init_db  # <-- Import the function

# 1. Initialize the database and create tables
init_db()  # <-- Call this function immediately

app = FastAPI(title="Country Data API")

app.include_router(country_router)

# To run: uvicorn src.presentation.api.main:app --reload
