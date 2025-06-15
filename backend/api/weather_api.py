# services/weather_service.py
import httpx
import logging
import os
import json
import time
from typing import Dict, Any, Tuple, Optional
import redis
from models.weather_data import WeatherData

logger = logging.getLogger(__name__)


class WeatherAPI:
    """Interface for OpenMeteo API with caching."""

    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"

        # Setup Redis connection if available
        redis_url = os.getenv("REDIS_URL")
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                logger.info("Connected to Redis for weather caching")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {str(e)}")

        self.cache_ttl = int(os.getenv("WEATHER_CACHE_TTL", 3600))  # Default 1 hour
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    async def fetch_weather(self, latitude: float, longitude: float) -> WeatherData:
        """Fetch weather data for a specific location."""
        # Round coordinates to reduce cache fragmentation
        lat_rounded = round(latitude, 2)
        lon_rounded = round(longitude, 2)

        # Check cache first
        cached_data = self._get_from_cache(lat_rounded, lon_rounded)
        if cached_data:
            logger.debug(
                f"Using cached weather data for ({lat_rounded}, {lon_rounded})"
            )
            return WeatherData.parse_obj(cached_data)

        # If not in cache, fetch from API
        logger.info(f"Fetching weather data for ({lat_rounded}, {lon_rounded})")

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    params = {
                        "latitude": lat_rounded,
                        "longitude": lon_rounded,
                        "hourly": "temperature_2m,precipitation,cloud_cover,visibility,wind_speed_10m,wind_direction_10m,pressure_msl,relative_humidity_2m",
                    }

                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                    weather_data = response.json()

                    # Create WeatherData object
                    weather = WeatherData.from_api(
                        weather_data, lat_rounded, lon_rounded
                    )

                    # Cache the results
                    self._save_to_cache(lat_rounded, lon_rounded, weather.dict())

                    return weather

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Weather API attempt {attempt+1} failed: {str(e)}. Retrying..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(
                        f"Failed to fetch weather after {self.max_retries} attempts: {str(e)}"
                    )
                    # Generate dummy data as fallback
                    logger.warning(
                        f"Generating dummy weather data for ({lat_rounded}, {lon_rounded})"
                    )
                    dummy_weather = WeatherData.generate_dummy(lat_rounded, lon_rounded)
                    return dummy_weather

    def _get_cache_key(self, lat: float, lon: float) -> str:
        """Generate cache key for coordinates."""
        return f"weather:{lat}:{lon}"

    def _get_from_cache(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get weather data from cache if available."""
        if not self.redis_client:
            return None

        cache_key = self._get_cache_key(lat, lon)
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {str(e)}")

        return None

    def _save_to_cache(self, lat: float, lon: float, data: Dict[str, Any]) -> bool:
        """Save weather data to cache."""
        if not self.redis_client:
            return False

        cache_key = self._get_cache_key(lat, lon)
        try:
            self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.warning(f"Error saving to cache: {str(e)}")
            return False
