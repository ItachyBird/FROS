import math
from typing import Tuple


def calculate_distance(
    point1: Tuple[float, float], point2: Tuple[float, float]
) -> float:
    """
    Calculate the great-circle distance between two points in kilometers.

    Args:
        point1: Tuple of (latitude, longitude) for first point
        point2: Tuple of (latitude, longitude) for second point

    Returns:
        Distance in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Earth radius in kilometers
    r = 6371.0

    return r * c


def calculate_bearing(
    point1: Tuple[float, float], point2: Tuple[float, float]
) -> float:
    """
    Calculate the bearing (direction) from point1 to point2 in degrees.

    Args:
        point1: Tuple of (latitude, longitude) for first point
        point2: Tuple of (latitude, longitude) for second point

    Returns:
        Bearing in degrees (0-360, where 0 is North)
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])

    # Calculate bearing
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        dlon
    )
    bearing = math.degrees(math.atan2(y, x))

    # Convert to 0-360 range
    bearing = (bearing + 360) % 360

    return bearing


def get_midpoint(
    point1: Tuple[float, float], point2: Tuple[float, float]
) -> Tuple[float, float]:
    """
    Calculate the midpoint between two geographic points.

    Args:
        point1: Tuple of (latitude, longitude) for first point
        point2: Tuple of (latitude, longitude) for second point

    Returns:
        Tuple of (latitude, longitude) for the midpoint
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])

    # Calculate the midpoint
    bx = math.cos(lat2) * math.cos(lon2 - lon1)
    by = math.cos(lat2) * math.sin(lon2 - lon1)

    lat3 = math.atan2(
        math.sin(lat1) + math.sin(lat2), math.sqrt((math.cos(lat1) + bx) ** 2 + by**2)
    )
    lon3 = lon1 + math.atan2(by, math.cos(lat1) + bx)

    # Convert back to degrees
    lat3 = math.degrees(lat3)
    lon3 = math.degrees(lon3)

    return (lat3, lon3)
