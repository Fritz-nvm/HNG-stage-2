from app.config import SessionLocal
from typing import Generator


# This is the standard FastAPI pattern for getting a DB session
def get_db() -> Generator:
    """Provides a fresh database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
