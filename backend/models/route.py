import math
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from models.airport import Airport
from models.waypoint import Waypoint, WaypointStatus
from models.aircraft import Aircraft

logger = logging.getLogger(__name__)


class Route:
    """A flight route consisting of origin, destination, and waypoints."""

    def __init__(
        self,
        id: UUID = None,
        name: str = "",
        origin: Airport = None,
        destination: Airport = None,
        waypoints: List[Waypoint] = None,
        path_type: str = "direct",
        optimization_method: str = "",
        distance: float = 0,
        fitness_score: float = 0,
        created_at: datetime = None,
        fuel_consumption: float = 0,  # Added
        estimated_time: float = 0,    # Added
    ):
        self.id = id or uuid4()
        self.name = name
        self.origin = origin
        self.destination = destination
        self.waypoints = waypoints or []
        self.path_type = path_type
        self.optimization_method = optimization_method
        self.distance = distance
        self.fitness_score = fitness_score
        self.created_at = created_at or datetime.utcnow()
        self.weather_data = {}  # Will be populated by weather service
        self.fuel_consumption = fuel_consumption  # In kg
        self.estimated_time = estimated_time      # In hours

        # Per-segment distances and times
        self.leg_distances = []
        self.leg_times = []

    def get_current_waypoint(self, current_time: datetime = None) -> Optional[Waypoint]:
        """Return the current active waypoint based on time elapsed."""
        if not current_time:
            current_time = datetime.utcnow()

        active_waypoints = [
            wp for wp in self.waypoints if wp.status == WaypointStatus.ACTIVE
        ]
        return active_waypoints[0] if active_waypoints else None

    def calculate_estimated_time(self, aircraft) -> float:
        """Calculate estimated flight time in hours based on aircraft specifications and route distance."""
        if (
            not aircraft
            or not hasattr(aircraft, "cruise_speed_kmh")
            or not self.distance
        ):
            return None

        # Basic time calculation based on distance and cruise speed
        base_time_hours = self.distance / aircraft.cruise_speed_kmh

        # Add time for takeoff and landing (typically ~30 minutes total)
        total_time_hours = base_time_hours + 0.5

        # If we have weather data, account for headwinds/tailwinds
        if hasattr(self, "weather_data") and self.weather_data:
            # Calculate average wind effect
            wind_effect = 0
            num_points = 0

            for wp_key, weather in self.weather_data.items():
                # Extract wind data - assuming we have wind_speed and wind_direction
                if "wind_speed" in weather and "wind_direction" in weather:
                    wind_speed = weather.get("wind_speed", 0)  # m/s
                    wind_direction = weather.get("wind_direction", 0)  # degrees

                    # Simplified calculation - positive means tailwind (helps), negative means headwind (slows)
                    if 0 <= abs(wind_direction - self.average_bearing) <= 90:
                        wind_effect += wind_speed * 3.6  # convert to km/h
                    else:
                        wind_effect -= wind_speed * 3.6  # convert to km/h

                    num_points += 1

            # Apply wind effect to time calculation
            if num_points > 0:
                avg_wind_effect = wind_effect / num_points
                effective_speed = aircraft.cruise_speed_kmh + avg_wind_effect
                if effective_speed > 0:  # Prevent division by zero
                    wind_adjusted_time = self.distance / effective_speed
                    total_time_hours = (
                        wind_adjusted_time + 0.5
                    )  # Still add takeoff/landing time

        self.estimated_time = total_time_hours
        return total_time_hours

    def calculate_leg_times(self, aircraft) -> List[float]:
        """
        Calculate the estimated flight time for each segment/leg in hours.
        Stores and returns the times as a list, matching leg_distances.
        """
        if not aircraft or not hasattr(aircraft, "cruise_speed_kmh"):
            self.leg_times = []
            return []

        leg_times = []
        leg_distances = []

        # Prepare segments
        points = []
        if self.origin and self.waypoints:
            points.append((self.origin, self.waypoints[0]))
        for i in range(len(self.waypoints) - 1):
            points.append((self.waypoints[i], self.waypoints[i + 1]))
        if self.destination and self.waypoints:
            points.append((self.waypoints[-1], self.destination))

        n_legs = len(points)
        for idx, (start, end) in enumerate(points):
            distance = start.calculate_distance(end)
            leg_distances.append(distance)

            base_time = 0
            if aircraft.cruise_speed_kmh > 0:
                base_time = distance / aircraft.cruise_speed_kmh

            # Optionally, add weather effect here per segment if you want (see below)
            # For now: ignore segment wind/extra time

            leg_times.append(base_time)

        # Add fixed time for takeoff/landing to first/last leg (distributed)
        total_fixed = 0.5  # 30 minutes for takeoff+landing
        if leg_times:
            leg_times[0] += total_fixed / 2
            leg_times[-1] += total_fixed / 2

        self.leg_distances = leg_distances
        self.leg_times = leg_times
        return leg_times

    def get_leg_times(self, aircraft) -> List[float]:
        """Get or (re)calculate list of estimated times per leg."""
        if not hasattr(self, "leg_times") or not self.leg_times:
            self.calculate_leg_times(aircraft)
        return self.leg_times

    def calculate_fuel_consumption(self, aircraft, weather_data):
        """Calculate estimated fuel consumption based on route and weather."""
        # Base consumption from distance
        distance_km = self.distance
        flight_hours = distance_km / aircraft.cruise_speed_kmh
        base_fuel_kg = flight_hours * aircraft.fuel_consumption_rate_kg_hr

        # Adjustment factors - start with 100% (no adjustment)
        wind_factor = 1.0
        altitude_factor = 1.0
        temperature_factor = 1.0

        # Calculate headwind/tailwind component for each segment
        for i, waypoint in enumerate(self.waypoints[:-1]):
            if i >= len(self.waypoints) - 1:
                continue

            # Get next waypoint
            next_waypoint = self.waypoints[i + 1]

            # Calculate bearing between waypoints
            from math import radians, sin, cos, atan2, degrees

            bearing = waypoint.calculate_bearing(next_waypoint)

            # Get wind data
            waypoint_key = f"waypoint_{i}"
            if waypoint_key in weather_data:
                wind_speed = weather_data[waypoint_key].get("wind_speed_10m", 0)
                wind_direction = weather_data[waypoint_key].get("wind_direction_10m", 0)

                # Calculate headwind/tailwind component
                # Positive is headwind, negative is tailwind
                wind_angle = abs((wind_direction - bearing + 180) % 360 - 180)
                if wind_angle <= 90:
                    # Headwind component
                    headwind = wind_speed * cos(radians(wind_angle))
                    # Increase fuel by 2% per m/s headwind, but apply per segment
                    segment_wind_factor = 1.0 + (0.02 * headwind)
                else:
                    # Tailwind component
                    tailwind = wind_speed * cos(radians(wind_angle - 180))
                    # Decrease fuel by 1.5% per m/s tailwind, but ensure we don't go below 50% of normal consumption
                    segment_wind_factor = max(0.5, 1.0 - (0.015 * tailwind))
                
                # Apply this segment's wind factor (weight by segment proportion)
                segment_proportion = 1.0 / (len(self.waypoints) - 1)  # Equal weight to each segment
                wind_factor = wind_factor * (1.0 - segment_proportion) + segment_wind_factor * segment_proportion

        # Apply minimum limit to wind factor to prevent negative fuel consumption
        wind_factor = max(0.3, wind_factor)  # Never go below 30% of base consumption

        # Apply all factors
        total_fuel_kg = base_fuel_kg * wind_factor * altitude_factor * temperature_factor
        total_fuel_kg /= 2
        self.fuel_consumption = total_fuel_kg
        return total_fuel_kg

    def calculate_total_distance(self) -> float:
        """Calculate the total distance of the route in kilometers and update leg_distances array."""
        leg_distances = []

        # Add distance from origin to first waypoint
        if self.origin and self.waypoints:
            leg_distances.append(self.origin.calculate_distance(self.waypoints[0]))

        # Add distances between waypoints
        for i in range(len(self.waypoints) - 1):
            leg_distances.append(self.waypoints[i].calculate_distance(self.waypoints[i + 1]))

        # Add distance from last waypoint to destination
        if self.destination and self.waypoints:
            leg_distances.append(self.waypoints[-1].calculate_distance(self.destination))

        total = sum(leg_distances)
        self.leg_distances = leg_distances  # Store the array of segment distances
        self.distance = total
        return total

    def get_leg_distances(self) -> List[float]:
        """Return a list of distances for each leg of the route."""
        # If not calculated yet, calculate
        if not hasattr(self, "leg_distances") or not self.leg_distances:
            self.calculate_total_distance()
        return self.leg_distances

    def calculate_time_after_ppo(self, ppo_index: int, alt_waypoints: List[Waypoint], new_destination: Airport, aircraft) -> float:
        """
        Calculate total estimated time after a PPO event, using same logic as calculate_distance_after_ppo.
        Returns the new estimated time in hours, with takeoff/landing time split across first/last segment.
        """
        if not aircraft or not hasattr(aircraft, "cruise_speed_kmh"):
            return 0.0

        # Build segment list just like in distance
        segments = []
        # origin to first waypoint
        if self.origin and self.waypoints:
            segments.append((self.origin, self.waypoints[0]))
        # current waypoints up to ppo_index
        for i in range(ppo_index):
            segments.append((self.waypoints[i], self.waypoints[i + 1]))
        # reroute: waypoints after PPO
        if alt_waypoints:
            segments.append((self.waypoints[ppo_index], alt_waypoints[0]))
            for i in range(len(alt_waypoints) - 1):
                segments.append((alt_waypoints[i], alt_waypoints[i + 1]))
            segments.append((alt_waypoints[-1], new_destination))
        else:
            segments.append((self.waypoints[ppo_index], new_destination))

        leg_times = []
        for start, end in segments:
            distance = start.calculate_distance(end)
            time = distance / aircraft.cruise_speed_kmh if aircraft.cruise_speed_kmh > 0 else 0
            leg_times.append(time)

        # Add fixed time for takeoff/landing split between first/last
        total_fixed = 0.5
        if leg_times:
            leg_times[0] += total_fixed / 2
            leg_times[-1] += total_fixed / 2

        return sum(leg_times)

    def calculate_distance_after_ppo(self, ppo_index: int, alt_waypoints: List[Waypoint], new_destination: Airport) -> float:
        """
        Calculate total distance after a PPO event.
        ppo_index: index in self.waypoints where PPO is applied (e.g., 6 for w7).
        alt_waypoints: list of alternate waypoints after reroute.
        new_destination: the destination after reroute (can be same as before).
        Returns distance (float). Does NOT update self.distance.
        """
        total = 0.0
        # Distance from origin to ppo_index waypoint
        if self.origin and self.waypoints:
            total += self.origin.calculate_distance(self.waypoints[0])
        for i in range(ppo_index):
            total += self.waypoints[i].calculate_distance(self.waypoints[i + 1])
        # From reroute point to alt waypoints
        if alt_waypoints:
            total += self.waypoints[ppo_index].calculate_distance(alt_waypoints[0])
            for i in range(len(alt_waypoints) - 1):
                total += alt_waypoints[i].calculate_distance(alt_waypoints[i + 1])
            total += alt_waypoints[-1].calculate_distance(new_destination)
        else:
            total += self.waypoints[ppo_index].calculate_distance(new_destination)
        return total

    def calculate_fitness_score(
        self,
        aircraft: Optional[Aircraft] = None,
        weather_weight: float = 0.6,
        distance_weight: float = 0.4,
    ) -> float:
        """
        Calculate the fitness score of the route based on weather and distance.

        Lower scores are better.
        """
        if self.distance <= 0:
            self.calculate_total_distance()

        if not self.weather_data:
            logger.warning(f"No weather data available for route {self.id}")
            # Default to distance-only fitness if no weather data
            self.fitness_score = self.distance / 1000  # Normalize distance
            return self.fitness_score

        # Get all waypoints including origin and destination
        all_points = [self.origin] + self.waypoints + [self.destination]
        weather_nodes = list(self.weather_data.values())

        # If incomplete weather data, default to distance-only fitness
        if len(weather_nodes) < 2:
            logger.warning(f"Incomplete weather data for route {self.id}")
            self.fitness_score = self.distance / 1000
            return self.fitness_score

        # Step 1: Estimate flight heading (simplified)
        if self.origin and self.destination:
            delta_lat = self.destination.latitude - self.origin.latitude
            delta_lon = self.destination.longitude - self.origin.longitude
            flight_heading_deg = math.degrees(math.atan2(delta_lon, delta_lat)) % 360
        else:
            flight_heading_deg = 0

        # Step 2: Ground Speed and Flight Time Calculation
        airspeed_km_h = 900  # Typical jet airspeed
        avg_ground_speed = 0

        for node in weather_nodes:
            jet_stream_speed = node.get("jet_stream_speed_250hPa", 0)
            jet_stream_direction = node.get("jet_stream_direction_250hPa", 0)
            angle_diff = math.radians(abs(flight_heading_deg - jet_stream_direction))
            jet_stream_component = jet_stream_speed * math.cos(angle_diff)
            ground_speed = airspeed_km_h + jet_stream_component
            avg_ground_speed += max(
                ground_speed, airspeed_km_h * 0.5
            )  # Prevent unrealistically slow speeds

        avg_ground_speed /= len(weather_nodes) if weather_nodes else 1
        flight_time_hours = (
            self.distance / avg_ground_speed if avg_ground_speed > 0 else float("inf")
        )

        # Step 3: Fuel Consumption Calculation (use provided aircraft or defaults)
        if aircraft:
            fuel_consumption_rate = aircraft.fuel_consumption_rate_kg_hr
            fuel_capacity_kg = (
                aircraft.fuel_capacity_liters * 0.8
            )  # 0.8 kg/L for jet fuel
        else:
            # Default values
            fuel_consumption_rate = 3000  # kg/hr
            fuel_capacity_kg = 70000

        fuel_consumption_kg = fuel_consumption_rate * flight_time_hours

        # Step 4: Fuel Sufficiency Check
        fuel_penalty = 0
        if fuel_consumption_kg > fuel_capacity_kg:
            fuel_penalty = (
                (fuel_consumption_kg - fuel_capacity_kg) / fuel_capacity_kg * 10
            )

        # Step 5: Safety Assessments
        # Turbulence risk
        turbulence_risk = 0
        for node in weather_nodes:
            vertical_velocity = node.get("vertical_velocity_250hPa", 0)
            if abs(vertical_velocity) > 0.5:
                turbulence_risk += 1
        turbulence_penalty = (
            (turbulence_risk / len(weather_nodes)) * 2 if weather_nodes else 0
        )

        # Thunderstorm risk
        thunderstorm_risk = 0
        for node in weather_nodes:
            cape = node.get("cape", 0)
            cloud_cover_high = node.get("cloud_cover_high", 0)
            if cape > 1000 or cloud_cover_high > 80:
                thunderstorm_risk += 1
        thunderstorm_penalty = (
            (thunderstorm_risk / len(weather_nodes)) * 3 if weather_nodes else 0
        )

        # Visibility and cloud cover
        source_weather = weather_nodes[0] if weather_nodes else {}
        dest_weather = weather_nodes[-1] if weather_nodes else {}

        visibility_source = source_weather.get("visibility", 10000)
        visibility_dest = dest_weather.get("visibility", 10000)
        cloud_cover_source = source_weather.get("cloud_cover", 0)
        cloud_cover_dest = dest_weather.get("cloud_cover", 0)

        visibility_penalty = 0
        if visibility_source < 5000 or visibility_dest < 5000:
            visibility_penalty = 1.0

        cloud_cover_penalty = 0
        if cloud_cover_source > 80 or cloud_cover_dest > 80:
            cloud_cover_penalty = 0.5

        # Runway condition assessment
        runway_risk = 0
        for weather in [source_weather, dest_weather]:
            precipitation = weather.get("precipitation", 0)
            rain = weather.get("rain", 0)
            showers = weather.get("showers", 0)
            snowfall = weather.get("snowfall", 0)
            if precipitation > 10 or rain > 5 or showers > 5 or snowfall > 1:
                runway_risk += 1
        runway_penalty = runway_risk * 0.75

        # Crosswind component
        crosswind_penalty = 0
        for weather in [source_weather, dest_weather]:
            wind_speed_10m = weather.get("wind_speed_10m", 0)
            wind_direction_10m = weather.get("wind_direction_10m", 0)
            angle_diff = math.radians(abs(flight_heading_deg - wind_direction_10m))
            crosswind_component = wind_speed_10m * math.sin(angle_diff)
            if crosswind_component > 20:
                crosswind_penalty += 0.5

        # Weather hazard flag
        weather_hazard_penalty = 0
        for weather in [source_weather, dest_weather]:
            weather_code = weather.get("weather_code", 0)
            if weather_code > 50:
                weather_hazard_penalty += 0.3

        # Step 6: Route Safety Score
        safety_score = (
            turbulence_penalty
            + thunderstorm_penalty
            + visibility_penalty
            + cloud_cover_penalty
            + runway_penalty
            + crosswind_penalty
            + weather_hazard_penalty
        )

        # Step 7: Combine into Fitness Score
        normalized_fuel = fuel_consumption_kg / 10000  # Normalize
        normalized_distance = self.distance / 5000  # Normalize assuming max 5000km

        # Final fitness score (lower is better)
        fitness_score = (
            weather_weight * safety_score
            + distance_weight * normalized_fuel
            + fuel_penalty
        )

        # Extra penalties for very long routes
        if self.distance > 5000:
            fitness_score += (self.distance - 5000) / 1000

        self.fitness_score = fitness_score
        return fitness_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert route to dictionary for API responses."""
        waypoints_dict = [wp.to_dict() for wp in self.waypoints]

        return {
            "id": str(self.id),
            "name": self.name,
            "origin": self.origin.to_dict() if self.origin else None,
            "destination": self.destination.to_dict() if self.destination else None,
            "waypoints": waypoints_dict,
            "path_type": self.path_type,
            "optimization_method": self.optimization_method,
            "distance_km": self.distance,
            "leg_distances": self.leg_distances,
            "leg_times": self.leg_times,
            "fitness_score": self.fitness_score,
            "created_at": self.created_at.isoformat(),
            "reroute_history": getattr(self, "reroute_history", []),
            "fuel_consumption": round(self.fuel_consumption, 2) if self.fuel_consumption else 0,
            "estimated_time": {
                "hours": int(self.estimated_time),
                "minutes": int((self.estimated_time % 1) * 60) if self.estimated_time else 0
            } if self.estimated_time else None
        }

    @property
    def average_bearing(self):
        """Calculate the average bearing of the route."""
        if len(self.waypoints) < 2:
            return 0

        # Calculate bearings between consecutive waypoints
        bearings = []
        for i in range(len(self.waypoints) - 1):
            wp1 = self.waypoints[i]
            wp2 = self.waypoints[i + 1]
            bearing = math.atan2(
                math.sin(math.radians(wp2.longitude - wp1.longitude))
                * math.cos(math.radians(wp2.latitude)),
                math.cos(math.radians(wp1.latitude))
                * math.sin(math.radians(wp2.latitude))
                - math.sin(math.radians(wp1.latitude))
                * math.cos(math.radians(wp2.latitude))
                * math.cos(math.radians(wp2.longitude - wp1.longitude)),
            )
            bearing = math.degrees(bearing)
            bearing = (bearing + 360) % 360  # Normalize to 0-360
            bearings.append(bearing)

        # Return average bearing
        return sum(bearings) / len(bearings)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Route":
        """Create a Route from dictionary data."""
        origin = Airport.from_dict(data["origin"]) if data.get("origin") else None
        destination = (
            Airport.from_dict(data["destination"]) if data.get("destination") else None
        )

        waypoints = []
        for wp_data in data.get("waypoints", []):
            waypoints.append(Waypoint.from_dict(wp_data))

        route = cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            name=data.get("name", ""),
            origin=origin,
            destination=destination,
            waypoints=waypoints,
            path_type=data.get("path_type", "direct"),
            optimization_method=data.get("optimization_method", ""),
            distance=data.get("distance_km", 0),
            fitness_score=data.get("fitness_score", 0),
            fuel_consumption=data.get("fuel_consumption", 0),
        )

        # Calculate initial leg distances (and optionally leg times if aircraft provided)
        route.calculate_total_distance()

        if "estimated_time" in data:
            estimated_time_data = data["estimated_time"]
            if isinstance(estimated_time_data, dict) and "hours" in estimated_time_data:
                # If it's in the format {"hours": x, "minutes": y}
                hours = estimated_time_data.get("hours", 0)
                minutes = estimated_time_data.get("minutes", 0)
                route.estimated_time = hours + (minutes / 60)
            else:
                # Otherwise, use it directly
                route.estimated_time = float(estimated_time_data) if estimated_time_data else 0

        if "created_at" in data:
            try:
                route.created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                route.created_at = datetime.utcnow()

        if "reroute_history" in data:
            route.reroute_history = data["reroute_history"]

        return route