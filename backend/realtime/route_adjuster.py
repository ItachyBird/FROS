import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import asyncio

from models.route import Route
from models.waypoint import Waypoint, WaypointStatus
from services.route_generator import RouteGenerator
from services.weather_service import WeatherService
from services.optimization.optimizer_factory import OptimizerFactory

logger = logging.getLogger(__name__)


class RouteAdjuster:
    """Service for real-time route adjustments."""

    def __init__(self):
        # These will be initialized on first use
        self._route_generator = None
        self._optimizer_factory = None
        self._weather_service = None

        # In-memory route storage (would be a database in production)
        self.active_routes = {}

    @property
    def route_generator(self):
        if self._route_generator is None:
            self._weather_service = WeatherService()
            self._route_generator = RouteGenerator(self._weather_service)
        return self._route_generator

    @property
    def optimizer_factory(self):
        if self._optimizer_factory is None:
            self._weather_service = WeatherService()
            self._optimizer_factory = OptimizerFactory(self._weather_service)
        return self._optimizer_factory

    @property
    def weather_service(self):
        if self._weather_service is None:
            self._weather_service = WeatherService()
        return self._weather_service

    async def handle_blocked_waypoint(
        self, route_id: str, waypoint_id: str
    ) -> Optional[Route]:
        """
        Handle a blocked waypoint by bypassing only that waypoint,
        keeping the subsequent waypoints in the route.
        """
        logger.info(f"Handling blocked waypoint {waypoint_id} on route {route_id}")

        # Get the route
        route = self.active_routes.get(route_id)
        if not route:
            logger.warning(f"Route {route_id} not found")
            return None

        # Find index of the blocked waypoint
        blocked_idx = None
        for idx, waypoint in enumerate(route.waypoints):
            if str(waypoint.id) == waypoint_id:
                blocked_idx = idx
                waypoint.mark_as_blocked()
                break

        if blocked_idx is None:
            logger.warning(f"Waypoint {waypoint_id} not found in route {route_id}")
            return None

        # Set the current position (either previous waypoint or route origin)
        if blocked_idx > 0:
            current_position = route.waypoints[blocked_idx - 1]
            current_position.mark_as_active()
            current_lat, current_lon = current_position.latitude, current_position.longitude
            # Next valid waypoint to join after blocked
            next_waypoint = (
                route.waypoints[blocked_idx + 1]
                if blocked_idx + 1 < len(route.waypoints)
                else route.destination
            )
        else:
            # Blocked waypoint is first
            current_position = None
            current_lat, current_lon = route.origin.latitude, route.origin.longitude
            next_waypoint = (
                route.waypoints[1]
                if len(route.waypoints) > 1
                else route.destination
            )

        # Exclude blocked waypoint area
        excluded_area = {
            "center": (
                route.waypoints[blocked_idx].latitude,
                route.waypoints[blocked_idx].longitude
            ),
            "radius": 0.2,  # ~20km exclusion radius
        }

        # Create a temporary origin at current position
        from models.airport import Airport
        temp_origin = Airport(
            iata_code=f"TMP{str(uuid4())[:4]}",
            name="Current Position",
            city="",
            country="",
            latitude=current_lat,
            longitude=current_lon,
        )

        # Generate new segment from current position to the next usable waypoint
        new_segment_routes = await self.route_generator.generate_alternative_routes(
            origin=temp_origin,
            destination=next_waypoint,
            aircraft_model=None,
            excluded_areas=[excluded_area],
        )

        # Use same optimization as original
        optimizer = self.optimizer_factory.get_optimizer(route.optimization_method)
        new_segment = optimizer.optimize(new_segment_routes)
        if not new_segment or not new_segment.waypoints:
            logger.error(f"Failed to generate new segment to bypass blocked waypoint")
            return None

        # Build new waypoints list:
        #  - up to current position (inclusive)
        #  - new segment (excluding first, which is temp_origin, and last, which is next_waypoint)
        #  - rest of the original waypoints (from next_waypoint onward)
        new_waypoints = []
        if blocked_idx > 0:
            new_waypoints.extend(route.waypoints[:blocked_idx])  # Up to before blocked
        # Append new segment waypoints (skip first, which is temp_origin, and last, which is next_waypoint)
        if len(new_segment.waypoints) > 2:
            new_waypoints.extend(new_segment.waypoints[1:-1])
        # Append remaining waypoints (from next_waypoint onward)
        if blocked_idx + 1 < len(route.waypoints):
            new_waypoints.extend(route.waypoints[blocked_idx + 1 :])

        # Update the route's waypoints
        route.waypoints = new_waypoints
        self.active_routes[route_id] = route

        return route

    def register_route(self, route: Route) -> None:
        """Register a new active route."""
        self.active_routes[str(route.id)] = route
        logger.info(f"Registered route {route.id}: {route.name}")