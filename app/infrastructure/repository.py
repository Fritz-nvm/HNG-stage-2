from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm.session import Session

# Import Models from the same layer
from .models import Country, Status


class CountryRepository:
    """
    Handles all direct database interactions.
    This fulfills the Repository pattern interface for the Application layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_status(self) -> Status:
        """Retrieves or initializes the global status record."""
        status = self.db.query(Status).first()
        if not status:
            # Initialize status if it doesn't exist
            status = Status()
            self.db.add(status)
            self.db.commit()
            self.db.refresh(status)
        return status

    def upsert_countries(
        self, country_data_list: List[Dict[str, Any]], refresh_time: datetime
    ) -> int:
        """
        Performs Update-or-Insert (Upsert) logic based on country 'name'.
        Returns the count of successfully processed records.
        """
        processed_count = 0
        for data in country_data_list:
            # Case-insensitive matching for the update logic
            existing_country = (
                self.db.query(Country).filter(Country.name.ilike(data["name"])).first()
            )

            data["last_refreshed_at"] = refresh_time

            if existing_country:
                # Update existing record
                for key, value in data.items():
                    setattr(existing_country, key, value)
                self.db.commit()
            else:
                # Insert new record
                new_country = Country(**data)
                self.db.add(new_country)
                self.db.commit()

            processed_count += 1

        return processed_count

    def update_global_status(self, total_count: int, refresh_time: datetime):
        """Updates the global status tracking record."""
        status = self.get_status()
        status.total_countries = total_count
        status.last_refreshed_at = refresh_time
        self.db.commit()

    def get_all(
        self,
        region: Optional[str] = None,
        currency: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> List[Country]:
        """Retrieves all countries, supporting filtering and sorting."""
        query = self.db.query(Country)

        if region:
            # Case-insensitive region filter
            query = query.filter(Country.region.ilike(region))

        if currency:
            # Case-insensitive currency code filter
            query = query.filter(Country.currency_code.ilike(currency))

        # Sort logic
        if sort:
            sort_field = sort.split("_")[0]
            sort_direction = sort.split("_")[-1]

            if sort_field == "gdp":
                sort_col = Country.estimated_gdp
            elif sort_field == "population":
                sort_col = Country.population
            elif sort_field == "name":
                sort_col = Country.name
            else:
                # Default to name ascending if sort parameter is invalid
                sort_col = Country.name

            if sort_direction == "desc":
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())

        return query.all()

    def get_by_name(self, name: str) -> Optional[Country]:
        """Retrieves a single country by name."""
        return self.db.query(Country).filter(Country.name.ilike(name)).first()

    def delete_by_name(self, name: str) -> bool:
        """Deletes a single country by name."""
        country = self.get_by_name(name)
        if country:
            self.db.delete(country)
            self.db.commit()
            return True
        return False

    def get_top_gdp(self, limit: int = 5) -> List[Country]:
        """Gets the top N countries by estimated GDP for image generation."""
        return (
            self.db.query(Country)
            .filter(Country.estimated_gdp != None)
            .order_by(Country.estimated_gdp.desc())
            .limit(limit)
            .all()
        )
