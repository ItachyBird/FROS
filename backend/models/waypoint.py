# models/waypoint.py
import math
from enum import Enum
from typing import Dict, Any
from uuid import UUID, uuid4


class WaypointStatus(Enum):
    """Status of a waypoint in a route."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Waypoint:
    """A waypoint on a flight route."""

    def __init__(
        self,
        id: UUID = None,
        name: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
        order: int = 0,
        status: WaypointStatus = WaypointStatus.PENDING,
    ):
        self.id = id or uuid4()
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.order = order
        self.status = status

    def calculate_distance(self, other) -> float:
        """Calculate great-circle distance between this waypoint and another point in kilometers."""
        # Earth radius in kilometers
        R = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        lat2 = math.radians(other.latitude)
        lon2 = math.radians(other.longitude)

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert waypoint to dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "order": self.order,
            "status": (
                self.status.value
                if isinstance(self.status, WaypointStatus)
                else self.status
            ),
        }
    
    def calculate_bearing(self, other) -> float:
        """Calculate the bearing (direction) from this waypoint to another in degrees (0-360)."""
        # Convert latitude and longitude from degrees to radians
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        lat2 = math.radians(other.latitude)
        lon2 = math.radians(other.longitude)

        # Formula for initial bearing
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        initial_bearing = math.atan2(y, x)

        # Convert from radians to degrees
        initial_bearing = math.degrees(initial_bearing)
        
        # Normalize to 0-360 degrees
        bearing = (initial_bearing + 360) % 360

        return bearing


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Waypoint":
        """Create a Waypoint object from dictionary data."""
        status = data.get("status", "pending")
        if isinstance(status, str):
            try:
                status = WaypointStatus(status)
            except ValueError:
                status = WaypointStatus.PENDING

        return cls(
            id=UUID(data["id"]) if "id" in data else None,
            name=data.get("name", ""),
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
            order=data.get("order", 0),
            status=status,
        )
