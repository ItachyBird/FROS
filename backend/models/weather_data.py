from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class WeatherData(BaseModel):
    """Weather information model."""

    latitude: float
    longitude: float
    timestamp: datetime
    temperature: float  # Celsius
    precipitation: float  # mm
    cloud_cover: float  # %
    wind_speed: float  # km/h
    wind_direction: float  # degrees
    visibility: Optional[float] = None  # km
    pressure: Optional[float] = None  # hPa
    humidity: Optional[float] = None  # %
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self):
        return {
            "coordinates": [self.latitude, self.longitude],
            "timestamp": self.timestamp.isoformat(),
            "temperature": self.temperature,
            "precipitation": self.precipitation,
            "cloud_cover": self.cloud_cover,
            "wind": {"speed": self.wind_speed, "direction": self.wind_direction},
            "visibility": self.visibility,
            "pressure": self.pressure,
            "humidity": self.humidity,
        }

    @classmethod
    def from_api(cls, api_data, lat, lon):
        """Create a WeatherData object from OpenMeteo API response."""
        hourly = api_data.get("hourly", {})
        current_index = 0  # Use current hour data

        return cls(
            latitude=lat,
            longitude=lon,
            timestamp=datetime.fromisoformat(hourly.get("time", [])[current_index]),
            temperature=hourly.get("temperature_2m", [])[current_index],
            precipitation=hourly.get("precipitation", [])[current_index],
            cloud_cover=hourly.get("cloud_cover", [])[current_index],
            wind_speed=hourly.get("wind_speed_10m", [])[current_index],
            wind_direction=hourly.get("wind_direction_10m", [])[current_index],
            visibility=(
                hourly.get("visibility", [])[current_index]
                if "visibility" in hourly
                else None
            ),
            pressure=(
                hourly.get("pressure_msl", [])[current_index]
                if "pressure_msl" in hourly
                else None
            ),
            humidity=(
                hourly.get("relative_humidity_2m", [])[current_index]
                if "relative_humidity_2m" in hourly
                else None
            ),
            raw_data=api_data,
        )

    @classmethod
    def generate_dummy(cls, lat, lon):
        """Generate dummy weather data for testing."""
        import random

        return cls(
            latitude=lat,
            longitude=lon,
            timestamp=datetime.utcnow(),
            temperature=random.uniform(15, 35),  # 15-35 Celsius
            precipitation=random.uniform(0, 10),  # 0-10 mm
            cloud_cover=random.uniform(0, 100),  # 0-100%
            wind_speed=random.uniform(0, 30),  # 0-30 km/h
            wind_direction=random.uniform(0, 360),  # 0-360 degrees
            visibility=random.uniform(5, 20),  # 5-20 km
            pressure=random.uniform(980, 1020),  # 980-1020 hPa
            humidity=random.uniform(30, 90),  # 30-90%
        )
