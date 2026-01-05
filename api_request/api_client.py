"""
Weather API client with retry logic and error handling
"""
import time
import requests
from typing import Dict, Any, List

from config import Config
from exceptions import APIConnectionError, APIResponseError
from logger_config import setup_logger

logger = setup_logger(__name__)


class OpenMeteoAPIClient:
    """Client for fetching weather data from Open-Meteo API"""

    def __init__(self):
        Config.validate()
        self.base_url = Config.API_BASE_URL
        self.historical_url = Config.HISTORICAL_URL
        self.timeout = Config.API_TIMEOUT
        self.max_retries = Config.MAX_RETRIES
        self.retry_delay = Config.RETRY_DELAY
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_url(self, lat: float, lon: float, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build request params with coordinates"""
        base_params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "auto"
        }
        base_params.update(params)
        return base_params

    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with retry logic"""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                if data.get("error"):
                    raise APIResponseError(data.get("reason", "Unknown API error"))

                return data

            except (requests.RequestException, APIResponseError) as e:
                logger.error(f"API request failed (attempt {attempt}): {e}")
                if attempt == self.max_retries:
                    raise APIConnectionError("Max retries exceeded") from e
                time.sleep(self.retry_delay)

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def fetch_current_weather(self, city_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch current weather for a city"""
        params = self._build_url(
            city_data["lat"],
            city_data["lon"],
            {
                "current_weather": True
            }
        )
        logger.info(f"Fetching current weather for {city_data['name']}")
        return self._make_request(self.base_url, params)

    def fetch_forecast(
        self,
        city_data: Dict[str, Any],
        days: int = 7
    ) -> Dict[str, Any]:
        """Fetch weather forecast"""
        params = self._build_url(
            city_data["lat"],
            city_data["lon"],
            {
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum"
                ],
                "forecast_days": days
            }
        )
        logger.info(f"Fetching {days}-day forecast for {city_data['name']}")
        return self._make_request(self.base_url, params)

    def fetch_historical_weather(
        self,
        city_data: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Fetch historical weather data"""
        params = self._build_url(
            city_data["lat"],
            city_data["lon"],
            {
                "start_date": start_date,
                "end_date": end_date,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum"
                ]
            }
        )
        logger.info(
            f"Fetching historical weather for {city_data['name']} "
            f"({start_date} → {end_date})"
        )
        return self._make_request(self.historical_url, params)

    def fetch_multiple_cities(
        self,
        cities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fetch current weather for multiple cities"""
        results = []

        for city in cities:
            try:
                data = self.fetch_current_weather(city)
                results.append({
                    "city": city["name"],
                    "data": data
                })
            except Exception as e:
                logger.error(f"Failed to fetch weather for {city['name']}: {e}")

        return results
