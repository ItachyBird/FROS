# services/weather_service.py
import logging
import random
import asyncio
import httpx
import json
import os
from typing import Dict, Any
from models.route import Route

logger = logging.getLogger(__name__)


class WeatherService:
    """Service to retrieve weather data for flight routes."""

    def __init__(self):
        self.cache_dir = "cache/weather"
        self.ensure_cache_dir()
        self.api_url = "https://api.open-meteo.com/v1/forecast"

    def ensure_cache_dir(self):
        """Ensure weather cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    async def get_weather_for_route(self, route: Route) -> Dict[str, Dict[str, Any]]:
        """
        Get weather data for all points along a route using parallel requests.

        Args:
            route: A Route object with waypoints

        Returns:
            Dictionary mapping node keys to weather data dictionaries
        """
        logger.info(f"Fetching weather data for route {route.name}")

        # Collect all points (origin, waypoints, destination)
        all_points = []
        if route.origin:
            all_points.append(("origin", route.origin.latitude, route.origin.longitude))

        for i, waypoint in enumerate(route.waypoints):
            all_points.append((f"waypoint_{i}", waypoint.latitude, waypoint.longitude))

        if route.destination:
            all_points.append(
                ("destination", route.destination.latitude, route.destination.longitude)
            )

        # Create tasks for fetching weather data (either from cache or API)
        async def get_point_weather(point_key, lat, lon):
            # Check cache first
            cache_key = f"{lat:.4f}_{lon:.4f}"
            cache_file = os.path.join(self.cache_dir, f"weather_{cache_key}.json")

            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r") as f:
                        weather_data = json.load(f)
                        logger.debug(
                            f"Found cached weather for {point_key} at {lat:.4f}, {lon:.4f}"
                        )
                        return point_key, weather_data
                except Exception as e:
                    logger.warning(f"Failed to read cached weather: {str(e)}")

            # Fetch from API if not cached
            weather = await self._fetch_weather_data(lat, lon)

            # Save to cache
            try:
                with open(cache_file, "w") as f:
                    json.dump(weather, f)
            except Exception as e:
                logger.warning(f"Failed to cache weather data: {str(e)}")

            return point_key, weather

        # Create and execute all tasks in parallel
        tasks = [
            get_point_weather(point_key, lat, lon) for point_key, lat, lon in all_points
        ]
        results = await asyncio.gather(*tasks)

        # Convert results to dictionary
        weather_data = {point_key: data for point_key, data in results}

        return weather_data

    async def _fetch_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch weather data from OpenMeteo API with specific parameters for aviation.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Weather data dictionary
        """
        # logger.info(f"Fetching weather for coordinate: lat={lat:.4f}, lon={lon:.4f}")

        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "precipitation",
                    "rain",
                    "showers",
                    "snowfall",
                    "cloud_cover",
                    "cloud_cover_high",
                    "weather_code",
                    "visibility",
                    "wind_speed_10m",
                    "wind_direction_10m",
                ],
                "hourly": [
                    # Cruising altitude wind data (jet stream info)
                    "windspeed_200hPa",
                    "winddirection_200hPa",
                    "windspeed_250hPa",
                    "winddirection_250hPa",
                    "windspeed_300hPa",
                    "winddirection_300hPa",
                    # Icing and turbulence data
                    "temperature_500hPa",
                    "relativehumidity_500hPa",
                    "temperature_700hPa",
                    "relativehumidity_700hPa",
                    "vertical_velocity_250hPa",
                    "vertical_velocity_500hPa",
                    # Convective activity and clouds
                    "cape",
                    "cloud_cover_low",
                    "cloud_cover_mid",
                    "cloud_cover_high",
                    "geopotential_height_250hPa",
                ],
                "timezone": "auto",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()

                # Extract current weather
                current_weather = {
                    "temperature_2m": round(data["current"]["temperature_2m"], 1),
                    "precipitation": round(data["current"]["precipitation"], 1),
                    "rain": round(data["current"]["rain"], 1),
                    "showers": round(data["current"]["showers"], 1),
                    "snowfall": round(data["current"]["snowfall"], 1),
                    "cloud_cover": int(data["current"]["cloud_cover"]),
                    "cloud_cover_high": int(data["current"]["cloud_cover_high"]),
                    "weather_code": int(data["current"]["weather_code"]),
                    "visibility": round(data["current"]["visibility"], 1),
                    "wind_speed_10m": round(data["current"]["wind_speed_10m"], 1),
                    "wind_direction_10m": int(data["current"]["wind_direction_10m"]),
                    "elevation": round(data.get("elevation", 0), 1),
                }

                # Extract hourly data (use the first hour)
                hourly_weather = {
                    # Jet stream data
                    "jet_stream_speed_250hPa": round(
                        data["hourly"]["windspeed_250hPa"][0], 1
                    ),
                    "jet_stream_direction_250hPa": int(
                        data["hourly"]["winddirection_250hPa"][0]
                    ),
                    # Vertical velocity (indicates turbulence)
                    "vertical_velocity_250hPa": round(
                        data["hourly"]["vertical_velocity_250hPa"][0], 1
                    ),
                    # Temperature and humidity at different pressure levels
                    "temperature_500hPa": round(
                        data["hourly"]["temperature_500hPa"][0], 1
                    ),
                    "relative_humidity_500hPa": int(
                        data["hourly"]["relativehumidity_500hPa"][0]
                    ),
                    "temperature_700hPa": round(
                        data["hourly"]["temperature_700hPa"][0], 1
                    ),
                    "relative_humidity_700hPa": int(
                        data["hourly"]["relativehumidity_700hPa"][0]
                    ),
                    # Convective activity
                    "cape": round(data["hourly"]["cape"][0], 1),
                    # Cloud layers
                    "cloud_cover_low": int(data["hourly"]["cloud_cover_low"][0]),
                    "cloud_cover_mid": int(data["hourly"]["cloud_cover_mid"][0]),
                    "cloud_cover_high": int(data["hourly"]["cloud_cover_high"][0]),
                    # Other metrics
                    "geopotential_height_250hPa": round(
                        data["hourly"]["geopotential_height_250hPa"][0], 1
                    ),
                }

                # Combine all weather data
                return {**current_weather, **hourly_weather}

        except Exception as e:
            logger.error(
                f"Error fetching weather for lat={lat:.4f}, lon={lon:.4f}: {e}"
            )
            # Return fallback weather data
            return self._generate_mock_weather(lat, lon)

    def _generate_mock_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Generate mock weather data for testing or API fallback."""
        # Generate data that varies somewhat based on latitude/longitude for realism
        temp_base = 20 - (abs(lat) / 90) * 30  # Colder at higher latitudes

        return {
            "temperature_2m": round(temp_base + random.uniform(-5, 5), 1),
            "precipitation": round(random.uniform(0, 20), 1),
            "rain": round(random.uniform(0, 10), 1),
            "showers": round(random.uniform(0, 10), 1),
            "snowfall": round(random.uniform(0, 5), 1),
            "cloud_cover": random.randint(0, 100),
            "cloud_cover_high": random.randint(0, 100),
            "weather_code": random.randint(0, 100),
            "visibility": round(random.uniform(1000, 10000), 1),
            "wind_speed_10m": round(random.uniform(0, 50), 1),
            "wind_direction_10m": random.randint(0, 360),
            "elevation": round(random.uniform(0, 3000), 1),
            "jet_stream_speed_250hPa": round(random.uniform(50, 150), 1),
            "jet_stream_direction_250hPa": random.randint(0, 360),
            "vertical_velocity_250hPa": round(random.uniform(-2, 2), 1),
            "temperature_500hPa": round(random.uniform(-50, 0), 1),
            "relative_humidity_500hPa": random.randint(0, 100),
            "temperature_700hPa": round(random.uniform(-20, 10), 1),
            "relative_humidity_700hPa": random.randint(0, 100),
            "cape": round(random.uniform(0, 2000), 1),
            "cloud_cover_low": random.randint(0, 100),
            "cloud_cover_mid": random.randint(0, 100),
            "cloud_cover_high": random.randint(0, 100),
            "geopotential_height_250hPa": round(random.uniform(9000, 12000), 1),
        }

    async def get_current_conditions(self, airport_code: str) -> Dict[str, Any]:
        """Get current weather conditions at an airport."""
        # In a real implementation, you would look up the airport coordinates
        # For now, generate mock data
        return self._generate_mock_weather(0, 0)
