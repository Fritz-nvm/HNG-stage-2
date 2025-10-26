import requests
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

# --- Configuration (Loaded from .env or default) ---
# Environment variables for external URLs are used here
COUNTRIES_API_URL = os.getenv("COUNTRIES_API_URL")
EXCHANGE_API_URL = os.getenv("EXCHANGE_API_URL")

# Hardcoded image path as requested, no longer reading from .env
IMAGE_CACHE_PATH = "./cache/summary.png"


# --- Client Implementations ---


class RestCountriesClient:
    """Handles fetching country data."""

    def fetch_countries(self) -> List[Dict[str, Any]]:
        """Makes the HTTP request to get all country data."""
        # Check for None just in case environment loading fails
        if not COUNTRIES_API_URL:
            raise requests.RequestException("COUNTRIES_API_URL is not set.")

        response = requests.get(COUNTRIES_API_URL, timeout=10)
        response.raise_for_status()
        return response.json()


class ExchangeRateClient:
    """Handles fetching exchange rate data."""

    def fetch_rates(self) -> Dict[str, float]:
        """Makes the HTTP request to get exchange rates against USD."""
        if not EXCHANGE_API_URL:
            raise requests.RequestException("EXCHANGE_API_URL is not set.")

        response = requests.get(EXCHANGE_API_URL, timeout=10)
        response.raise_for_status()
        rates_data = response.json()
        return rates_data.get("rates", {})


class ImageGenerator:
    """Handles generating and saving the summary image."""

    def __init__(self):
        # The path is hardcoded here instead of coming from .env
        self.image_path = IMAGE_CACHE_PATH
        self._ensure_cache_directory()

    def _ensure_cache_directory(self):
        """Ensures the directory for the cached image exists."""
        cache_dir = os.path.dirname(self.image_path)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def generate_summary(
        self, total_countries: int, top_gdp_countries: List[Dict[str, Any]]
    ):
        """Generates and saves the summary image to disk."""
        try:
            # Create a simple image summary
            img = Image.new("RGB", (800, 400), color="#2c3e50")
            d = ImageDraw.Draw(img)

            # Simplified font loading for robustness
            try:
                font_title = ImageFont.truetype("arial.ttf", 36)
                font_body = ImageFont.truetype("arial.ttf", 20)
            except IOError:
                font_title = ImageFont.load_default()
                font_body = ImageFont.load_default()

            # Drawing text onto the image
            d.text((50, 40), "Country Cache Summary", fill="#ecf0f1", font=font_title)
            d.text(
                (50, 100),
                f"Total Countries Cached: {total_countries}",
                fill="#3498db",
                font=font_body,
            )

            d.text((50, 180), "Top 5 Estimated GDP:", fill="#e67e22", font=font_body)
            y_offset = 210
            for i, country in enumerate(top_gdp_countries):
                gdp_display = (
                    f"{country['estimated_gdp']:.2e}"
                    if country.get("estimated_gdp")
                    else "N/A"
                )
                text = f"{i+1}. {country['name']} (GDP: ${gdp_display})"
                d.text((70, y_offset), text, fill="#ecf0f1", font=font_body)
                y_offset += 30

            img.save(self.image_path)
        except Exception as e:
            # Catch file/image processing errors
            print(f"Warning: Failed to generate summary image: {e}")

    def get_image_path(self) -> str:
        """Returns the expected path of the summary image."""
        return self.image_path

    def image_exists(self) -> bool:
        """Checks if the summary image file exists."""
        return os.path.exists(self.image_path)
