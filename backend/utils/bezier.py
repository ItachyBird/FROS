import numpy as np
from typing import List, Tuple


def bezier_curve_point(
    control_points: List[Tuple[float, float]], t: float
) -> Tuple[float, float]:
    """
    Calculate a point on a Bezier curve defined by control points at parameter t.

    Args:
        control_points: List of (latitude, longitude) tuples defining the control points
        t: Parameter value between 0 and 1

    Returns:
        Tuple of (latitude, longitude) at position t along the curve
    """
    n = len(control_points) - 1
    point = [0.0, 0.0]

    for i, (lat, lon) in enumerate(control_points):
        # Calculate binomial coefficient
        coef = np.math.comb(n, i)
        # Calculate Bernstein polynomial
        factor = coef * (t**i) * ((1 - t) ** (n - i))
        # Add weighted contribution to point
        point[0] += lat * factor
        point[1] += lon * factor

    return tuple(point)
