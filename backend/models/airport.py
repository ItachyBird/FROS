# models/airport.py
import math
from typing import Dict, Any, Optional
from uuid import UUID, uuid4


class Airport:
    """Airport model with geographic coordinates."""

    def __init__(
        self,
        id: UUID = None,
        iata_code: str = "",
        name: str = "",
        city: str = "",
        country: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
    ):
        self.id = id or uuid4()
        self.iata_code = iata_code.upper()
        self.name = name
        self.city = city
        self.country = country
        self.latitude = latitude
        self.longitude = longitude

    def calculate_distance(self, other_airport) -> float:
        """Calculate great-circle distance between this airport and another in kilometers."""
        # Earth radius in kilometers
        R = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        lat2 = math.radians(other_airport.latitude)
        lon2 = math.radians(other_airport.longitude)

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    def calculate_bearing(self, other_airport) -> float:
        """Calculate initial bearing from this airport to another in degrees."""
        # Convert latitude and longitude from degrees to radians
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        lat2 = math.radians(other_airport.latitude)
        lon2 = math.radians(other_airport.longitude)

        # Calculate bearing
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(
            lat2
        ) * math.cos(dlon)
        bearing_rad = math.atan2(y, x)

        # Convert to degrees
        bearing = math.degrees(bearing_rad)
        # Normalize to 0-360
        bearing = (bearing + 360) % 360

        return bearing

    def to_dict(self) -> Dict[str, Any]:
        """Convert airport to dictionary representation."""
        return {
            "id": str(self.id),
            "iata_code": self.iata_code,
            "name": self.name,
            "city": self.city,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Airport":
        """Create an Airport object from dictionary data."""
        return cls(
            id=data.get("id"),
            iata_code=data.get("iata_code", ""),
            name=data.get("name", ""),
            city=data.get("city", ""),
            country=data.get("country", ""),
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
        )
