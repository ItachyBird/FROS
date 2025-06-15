# services/path_calculator.py
import math
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class PathCalculator:
    """Service to calculate positions along flight paths."""

    def __init__(self):
        # Earth radius in km
        self.earth_radius = 6371.0

    def calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate great-circle distance between two points in kilometers."""
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = self.earth_radius * c

        return distance

    def calculate_bearing(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate initial bearing from point 1 to point 2 in degrees."""
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Calculate bearing
        dlon = lon2_rad - lon1_rad
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
            lat2_rad
        ) * math.cos(dlon)
        bearing_rad = math.atan2(y, x)

        # Convert to degrees
        bearing = math.degrees(bearing_rad)
        # Normalize to 0-360
        bearing = (bearing + 360) % 360

        return bearing

    def calculate_position(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        fraction: float,
        deflection_angle: float = 0,
    ) -> Tuple[float, float]:
        """
        Calculate a position along a great circle path with optional deflection.

        Args:
            start_lat: Starting latitude in degrees
            start_lon: Starting longitude in degrees
            end_lat: Ending latitude in degrees
            end_lon: Ending longitude in degrees
            fraction: Fraction of the path (0 to 1)
            deflection_angle: Angle to deflect from the direct path (degrees)

        Returns:
            Tuple of (latitude, longitude) in degrees
        """
        # Convert to radians
        start_lat_rad = math.radians(start_lat)
        start_lon_rad = math.radians(start_lon)
        end_lat_rad = math.radians(end_lat)
        end_lon_rad = math.radians(end_lon)

        # Calculate distance and bearing
        distance = self.calculate_distance(start_lat, start_lon, end_lat, end_lon)
        initial_bearing_rad = math.radians(
            self.calculate_bearing(start_lat, start_lon, end_lat, end_lon)
        )

        # Apply deflection to bearing
        bearing_rad = initial_bearing_rad + math.radians(deflection_angle)

        # Calculate intermediate distance
        dist_rad = (distance * fraction) / self.earth_radius

        # Calculate intermediate position
        lat_rad = math.asin(
            math.sin(start_lat_rad) * math.cos(dist_rad)
            + math.cos(start_lat_rad) * math.sin(dist_rad) * math.cos(bearing_rad)
        )

        lon_rad = start_lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(dist_rad) * math.cos(start_lat_rad),
            math.cos(dist_rad) - math.sin(start_lat_rad) * math.sin(lat_rad),
        )

        # Convert back to degrees
        lat = math.degrees(lat_rad)
        lon = math.degrees(lon_rad)

        return (lat, lon)
