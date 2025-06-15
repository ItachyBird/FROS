import logging
from typing import List, Optional
from uuid import uuid4
from geopy.distance import geodesic
import math
import copy

from models.route import Route
from models.aircraft import Aircraft
from models.waypoint import Waypoint, WaypointStatus
from services.weather_service import WeatherService

logger = logging.getLogger(__name__)

class PPORerouter:
    """PPO-based rerouting logic for flight paths."""

    def __init__(
        self, weather_service: WeatherService = None, aircraft: Aircraft = None
    ):
        self.used_route_types = []
        self.weather_service = weather_service
        self.aircraft = aircraft
        self.consider_fuel = True

    # Add method to evaluate alternatives based on fuel and weather
    async def evaluate_alternatives(
        self, current_route, blocked_waypoint, current_position, alternative_routes
    ):
        """Evaluate alternative routes based on multiple factors including weather and fuel."""
        scores = []

        for alt_route in alternative_routes:
            # Skip routes with previously used path types
            if (
                alt_route.path_type in self.used_route_types
                or alt_route.path_type == "direct"
            ):
                continue

            # Find closest waypoint in this alternative route
            nearest_wp = None
            nearest_index = -1
            min_distance = float("inf")

            for i, wp in enumerate(alt_route.waypoints):
                distance = current_position.calculate_distance(wp)
                if distance < min_distance:
                    min_distance = distance
                    nearest_wp = wp
                    nearest_index = i

            if not nearest_wp:
                continue

            # Create a potential rerouted path
            rerouted = self._create_rerouted_path(
                current_route=current_route,
                blocked_waypoint=blocked_waypoint,
                current_position=current_position,
                alternative_route=alt_route,
                target_waypoint=nearest_wp,
                target_index=nearest_index,
            )

            # Get weather data if needed and not already present
            if self.consider_fuel and self.weather_service and self.aircraft:
                if not hasattr(rerouted, "weather_data") or not rerouted.weather_data:
                    rerouted.weather_data = (
                        await self.weather_service.get_weather_for_route(rerouted)
                    )

                # Calculate fuel consumption with weather factors
                fuel_kg = rerouted.calculate_fuel_consumption(
                    self.aircraft, rerouted.weather_data
                )
            else:
                fuel_kg = 0

            # Base score is fitness score
            base_score = rerouted.fitness_score

            # Weather risk factors (optional enhancement)
            weather_risk = 0
            if self.consider_fuel and rerouted.weather_data:
                for wp_key, weather in rerouted.weather_data.items():
                    # Check for severe turbulence (using vertical velocity as proxy)
                    v_velocity = abs(weather.get("vertical_velocity_250hPa", 0))
                    if v_velocity > 0.5:  # m/s vertical velocity
                        weather_risk += v_velocity * 2

                    # Check for poor visibility
                    visibility = weather.get("visibility", 10000)
                    if visibility < 5000:  # meters
                        weather_risk += (5000 - visibility) / 1000

                    # Check for high cloud cover
                    cloud_cover = weather.get("cloud_cover", 0)
                    if cloud_cover > 80:  # percent
                        weather_risk += (cloud_cover - 80) / 5

            # Combined score (lower is better)
            # Weight fuel consumption and weather risk appropriately
            fuel_factor = 0.2 if self.consider_fuel else 0
            weather_factor = 0.1 if self.consider_fuel else 0

            total_score = (
                base_score + (fuel_kg * fuel_factor) + (weather_risk * weather_factor)
            )

            scores.append(
                {
                    "route": alt_route,
                    "target_waypoint": nearest_wp,
                    "target_index": nearest_index,
                    "distance": min_distance,
                    "score": total_score,
                    "fuel_kg": fuel_kg,
                    "weather_risk": weather_risk,
                    "rerouted_path": rerouted,
                }
            )

        # Sort by score (lower is better)
        scores.sort(key=lambda x: x["score"])

        return scores

    async def reroute(
        self,
        blocked_waypoint: Waypoint,
        current_route: Route,
        alternative_routes: List[Route],
        current_position: Optional[Waypoint] = None,
    ) -> Optional[Route]:
        """
        Reroute a flight path when a waypoint is blocked, considering fuel and weather.

        Args:
            blocked_waypoint: The waypoint that needs to be avoided
            current_route: The currently active route
            alternative_routes: Other possible routes to consider for rerouting
            current_position: Current aircraft position (defaults to waypoint before blocked)

        Returns:
            A new Route object with the rerouted path, or None if rerouting failed
        """
        if not blocked_waypoint or not current_route or not alternative_routes:
            logger.warning("Missing required parameters for rerouting")
            return None

        logger.info(
            f"PPO Rerouting from {current_route.name} around blocked waypoint {blocked_waypoint.name}"
        )

        # Reset used route types if this is a new rerouting session
        if (
            not hasattr(current_route, "reroute_history")
            or not current_route.reroute_history
        ):
            self.used_route_types = [current_route.path_type]
        else:
            # Extract used route types from reroute history
            self.used_route_types = [
                route_type for _, route_type in current_route.reroute_history
            ]

        # If no current_position is provided, use the waypoint before the blocked one
        if not current_position:
            try:
                blocked_index = current_route.waypoints.index(blocked_waypoint)
                if blocked_index > 0:
                    current_position = current_route.waypoints[blocked_index - 1]
                    current_position.status = WaypointStatus.ACTIVE
                else:
                    # If blocked waypoint is the first one, current position is the origin
                    logger.warning(
                        "Cannot reroute from origin - first waypoint is blocked"
                    )
                    return None
            except ValueError:
                logger.error(f"Blocked waypoint not found in current route")
                return None

        # Evaluate alternative routes considering weather and fuel
        if self.consider_fuel and self.weather_service and self.aircraft:
            alternatives = await self.evaluate_alternatives(
                current_route, blocked_waypoint, current_position, alternative_routes
            )

            # No valid alternatives found
            if not alternatives:
                logger.warning("No valid alternative routes found for rerouting")
                return None

            # Take the best alternative (lowest score)
            best_reroute = alternatives[0]

            logger.info(
                f"Selected reroute: {best_reroute['route'].path_type} with score {best_reroute['score']:.2f}, "
                f"fuel: {best_reroute['fuel_kg']:.2f}kg, weather risk: {best_reroute['weather_risk']:.2f}"
            )

            # Add route type to used routes
            self.used_route_types.append(best_reroute["route"].path_type)

            return best_reroute["rerouted_path"]

        else:
            # Use original non-fuel-aware rerouting logic
            # Find the closest waypoint in alternative routes, excluding used route types
            reroute_targets = []

            for alt_route in alternative_routes:
                # Skip routes with previously used path types
                if (
                    alt_route.path_type in self.used_route_types
                    or alt_route.path_type == "direct"
                ):
                    continue

                # Find closest waypoint in this alternative route
                nearest_wp = None
                nearest_index = -1
                min_distance = float("inf")

                for i, wp in enumerate(alt_route.waypoints):
                    distance = current_position.calculate_distance(wp)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_wp = wp
                        nearest_index = i

                if nearest_wp:
                    reroute_targets.append(
                        {
                            "route": alt_route,
                            "target_waypoint": nearest_wp,
                            "target_index": nearest_index,
                            "distance": min_distance,
                        }
                    )

            # No valid reroute targets found
            if not reroute_targets:
                logger.warning("No valid alternative routes found for rerouting")
                return None

            # Sort targets by distance (closest first)
            reroute_targets.sort(key=lambda x: x["distance"])
            best_reroute = reroute_targets[0]

            logger.info(
                f"Selected reroute target: {best_reroute['target_waypoint'].name} on route {best_reroute['route'].name} (distance: {best_reroute['distance']:.2f} km)"
            )

            # Create a new rerouted path
            rerouted_route = self._create_rerouted_path(
                current_route=current_route,
                blocked_waypoint=blocked_waypoint,
                current_position=current_position,
                alternative_route=best_reroute["route"],
                target_waypoint=best_reroute["target_waypoint"],
                target_index=best_reroute["target_index"],
            )

            # Add route type to used routes
            self.used_route_types.append(best_reroute["route"].path_type)

            # At the end, before returning the route
            if rerouted_route and not rerouted_route.estimated_time:
                # Calculate estimated time with default values if necessary
                if self.aircraft:
                    rerouted_route.estimated_time = (
                        rerouted_route.calculate_estimated_time(self.aircraft)
                    )
                else:
                    # Use a default speed if no aircraft is available
                    default_speed = 900  # km/h
                    flight_hours = rerouted_route.distance / default_speed
                    rerouted_route.estimated_time = (
                        flight_hours + 0.5
                    )  # Add takeoff/landing time

            return rerouted_route

    def _create_rerouted_path(
        self,
        current_route: Route,
        blocked_waypoint: Waypoint,
        current_position: Waypoint,
        alternative_route: Route,
        target_waypoint: Waypoint,
        target_index: int,
    ) -> Route:
        """Create a new route by combining the current route up to current_position with
        the alternative route from target_waypoint+2 to destination."""

        # Find index in current route for current position and blocked waypoint
        current_pos_index = -1
        blocked_index = -1

        for i, wp in enumerate(current_route.waypoints):
            if wp.id == current_position.id:
                current_pos_index = i
            if wp.id == blocked_waypoint.id:
                blocked_index = i

        if current_pos_index == -1:
            # Current position not found in waypoints by ID, try to find by closest coordinates
            min_distance = float("inf")
            for i, wp in enumerate(current_route.waypoints):
                distance = geodesic(
                    (current_position.latitude, current_position.longitude),
                    (wp.latitude, wp.longitude),
                ).kilometers
                if distance < min_distance:
                    min_distance = distance
                    current_pos_index = i

        logger.info(
            f"Current position index: {current_pos_index}, Blocked index: {blocked_index}"
        )

        # Determine if we're before or after the blocked waypoint
        if blocked_index != -1 and current_pos_index < blocked_index:
            # We're before the blocked waypoint, we need to reroute around it

            # Get waypoints from current route up to current position
            waypoints_initial = current_route.waypoints[: current_pos_index + 1]

            # For the alternative route, join at target_index + 2 (with boundary check)
            alt_waypoints = alternative_route.waypoints
            join_index = target_index + 2
            if join_index >= len(alt_waypoints):
                join_index = len(alt_waypoints) - 1  # Ensure we don't go out of bounds

            waypoints_alt = alt_waypoints[join_index:]

            destination_waypoint = current_route.waypoints[-1]

            # Check if the last waypoint from the alternative route matches the destination
            if waypoints_alt and waypoints_alt[-1].name != destination_waypoint.name:
                logger.info(
                    "Adding destination waypoint to ensure route ends at destination airport"
                )
        else:
            # We're already past the blocked waypoint or it's not in our route
            waypoints_initial = current_route.waypoints[: current_pos_index + 1]
            remaining_waypoints = current_route.waypoints[current_pos_index + 1 :]
            logger.warning(
                f"Current position ({current_pos_index}) is already past or equal to blocked waypoint ({blocked_index}). "
                f"Continuing on current route but noting the blockage."
            )
            waypoints_alt = remaining_waypoints

        # Update the order of all waypoints
        combined_waypoints = []
        for i, wp in enumerate(waypoints_initial):
            wp_copy = copy.deepcopy(wp)
            wp_copy.order = i + 1
            # Keep the original name for these waypoints
            combined_waypoints.append(wp_copy)

        next_order = len(combined_waypoints) + 1
        for i, wp in enumerate(waypoints_alt):
            wp_copy = copy.deepcopy(wp)
            wp_copy.id = uuid4()  # Generate new ID to prevent duplicates

            # Rename waypoints to reflect their new position in sequence
            original_name_parts = wp.name.split("_")
            route_type = (
                original_name_parts[-1] if len(original_name_parts) > 1 else "alt"
            )

            wp_copy.name = f"WP{next_order + i}_{route_type}"
            wp_copy.order = next_order + i
            combined_waypoints.append(wp_copy)

        # Always ensure the final waypoint is the destination
        destination_waypoint = copy.deepcopy(current_route.waypoints[-1])

        is_destination_included = False
        if (
            combined_waypoints
            and combined_waypoints[-1].latitude == destination_waypoint.latitude
            and combined_waypoints[-1].longitude == destination_waypoint.longitude
        ):
            is_destination_included = True

        if not is_destination_included:
            destination_waypoint.id = uuid4()  # Generate new ID to prevent duplicates
            destination_waypoint.order = len(combined_waypoints) + 1
            if combined_waypoints:
                last_wp_name_parts = combined_waypoints[-1].name.split("_")
                route_type = (
                    last_wp_name_parts[-1] if len(last_wp_name_parts) > 1 else "alt"
                )
                destination_waypoint.name = (
                    f"WP{destination_waypoint.order}_{route_type}"
                )
            else:
                destination_waypoint.name = f"WP{destination_waypoint.order}_dest"

            combined_waypoints.append(destination_waypoint)
            logger.info(
                "Added destination waypoint to ensure route ends at destination airport"
            )

        logger.info(
            f"Combined route: {len(waypoints_initial)} initial + {len(waypoints_alt)} alternative = {len(combined_waypoints)} total waypoints"
        )

        # Create reroute record
        reroute_record = (blocked_waypoint.name, alternative_route.path_type)

        rerouted_route = Route(
            id=uuid4(),
            name=f"Rerouted_{current_route.name}",
            origin=current_route.origin,
            destination=current_route.destination,
            waypoints=combined_waypoints,
            path_type=f"rerouted_{alternative_route.path_type}",
            optimization_method="ppo",
            distance=0,  # Will be calculated
            fitness_score=0,  # Will be calculated
        )

        if hasattr(current_route, "reroute_history") and current_route.reroute_history:
            rerouted_route.reroute_history = current_route.reroute_history + [
                reroute_record
            ]
        else:
            rerouted_route.reroute_history = [reroute_record]

        if hasattr(current_route, "weather_data") and current_route.weather_data:
            rerouted_route.weather_data = current_route.weather_data
        elif (
            hasattr(alternative_route, "weather_data")
            and alternative_route.weather_data
        ):
            rerouted_route.weather_data = alternative_route.weather_data

        rerouted_route.calculate_total_distance()
        rerouted_route.calculate_fitness_score()

        if hasattr(current_route, "estimated_time") and current_route.estimated_time:
            rerouted_route.estimated_time = current_route.estimated_time

        if (
            self.aircraft
            and hasattr(rerouted_route, "weather_data")
            and rerouted_route.weather_data
        ):
            fuel_kg = rerouted_route.calculate_fuel_consumption(
                self.aircraft, rerouted_route.weather_data
            )
            rerouted_route.fuel_consumption = fuel_kg
            logger.info(f"Calculated fuel consumption: {fuel_kg:.2f} kg")

            flight_time = rerouted_route.calculate_estimated_time(self.aircraft)
            rerouted_route.estimated_time = flight_time

        elif not rerouted_route.estimated_time:
            default_speed = 900  # km/h, typical jet cruise speed
            flight_hours = rerouted_route.distance / default_speed
            rerouted_route.estimated_time = flight_hours + 0.5

        logger.info(
            f"Created rerouted path with {len(rerouted_route.waypoints)} waypoints"
        )
        return rerouted_route
    
    
