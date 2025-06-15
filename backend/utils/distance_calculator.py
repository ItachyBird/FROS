import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_distance(
    distance_km: float,
    min_distance: Optional[float] = None,
    max_distance: Optional[float] = None,
) -> float:
    """
    Normalize a distance value to a 0-1 range.

    Args:
        distance_km: Distance in kilometers to normalize
        min_distance: Minimum distance for normalization (default from env var or 100)
        max_distance: Maximum distance for normalization (default from env var or 5000)

    Returns:
        Normalized distance value between 0-1
    """
    # Read min/max from environment if not provided
    if min_distance is None:
        min_distance = float(os.getenv("MIN_FLIGHT_DISTANCE_KM", 100))

    if max_distance is None:
        max_distance = float(os.getenv("MAX_FLIGHT_DISTANCE_KM", 5000))

    # Ensure distance is within bounds
    bounded_distance = max(min_distance, min(distance_km, max_distance))

    # Normalize to 0-1 range
    normalized = (bounded_distance - min_distance) / (max_distance - min_distance)

    logger.debug(f"Normalized distance {distance_km:.2f} km to {normalized:.4f}")

    return normalized
