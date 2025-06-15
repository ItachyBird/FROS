# services/route_generator.py
import logging
import random
import os
import json
from typing import List, Dict, Any, Optional
from uuid import uuid4

from models.airport import Airport
from models.route import Route
from models.waypoint import Waypoint
from services.weather_service import WeatherService
from services.path_calculator import PathCalculator
from api.aircraft_api import AircraftAPI

logger = logging.getLogger(__name__)


class RouteGenerator:
    """Service to generate alternative flight routes."""

    def __init__(self, weather_service: WeatherService):
        self.weather_service = weather_service
        self.path_calculator = PathCalculator()
        self.aircraft_api = AircraftAPI()
        self.cache_dir = "cache/routes"
        self.ensure_cache_dir()

    def ensure_cache_dir(self):
        """Ensure route cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def filter_routes_for_optimization(self, routes):
        """Filter out direct paths and other unsuitable routes for optimization."""
        return [route for route in routes if route.path_type != "direct"]

    async def generate_alternative_routes(
        self,
        origin: Airport,
        destination: Airport,
        route_types: Optional[List[str]] = None,
        aircraft_model: Optional[str] = None,
        excluded_areas: Optional[List[Dict[str, Any]]] = None,
        use_cache: bool = True,
    ) -> List[Route]:
        """
        Generate multiple alternative routes between two airports.

        Args:
            origin: Origin airport
            destination: Destination airport
            route_types: List of route types to generate (default: all types)
            aircraft_model: Optional aircraft model to use
            excluded_areas: List of areas to avoid
            use_cache: Whether to use cached routes (default: True)

        Returns:
            List of Route objects
        """
        if not origin or not destination:
            logger.error("Origin and destination airports are required")
            return []

        # Default to all route types if none specified
        if not route_types:
            route_types = ["direct", "left", "right", "north", "south", "wide"]

        # Create a cache key based on origin, destination, and route types
        cache_key = f"{origin.iata_code}_{destination.iata_code}_{'-'.join(sorted(route_types))}"
        
        # Add aircraft model to cache key if specified
        if aircraft_model:
            cache_key += f"_{aircraft_model}"
            
        # Add excluded areas to cache key if specified
        if excluded_areas:
            # Create a simplified representation of excluded areas for the cache key
            excluded_str = "_excluded"
            for area in excluded_areas:
                if "center" in area and "radius_km" in area:
                    center = area["center"]
                    excluded_str += f"_{center['latitude']:.2f}_{center['longitude']:.2f}_{area['radius_km']}"
            cache_key += excluded_str

        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Try to load from cache if use_cache is True
        if use_cache and os.path.exists(cache_file):
            try:
                logger.info(f"Loading routes from cache for {origin.iata_code} to {destination.iata_code}")
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)
                
                # Convert JSON data back to Route objects
                routes = []
                for route_data in cached_data:
                    route = Route.from_dict(route_data)
                    routes.append(route)
                
                logger.info(f"Loaded {len(routes)} routes from cache")
                return routes
            except Exception as e:
                logger.warning(f"Error loading routes from cache: {str(e)}", exc_info=True)
                # Continue with generating new routes if cache loading fails
        
        logger.info(
            f"Generating {len(route_types)} alternative routes from {origin.iata_code} to {destination.iata_code}"
        )

        routes = []

        # Get aircraft data if specified
        aircraft = None
        if aircraft_model:
            aircraft_list = await self.aircraft_api.get_aircraft(aircraft_model)
            # Take the first aircraft in the list if available
            if aircraft_list and len(aircraft_list) > 0:
                aircraft = aircraft_list[0]

        # Generate each route type
        for route_type in route_types:
            route = await self._generate_route(
                origin, destination, route_type, aircraft, excluded_areas
            )
            if route:
                routes.append(route)
        
        # Cache the generated routes
        if routes:
            try:
                # Convert route objects to dictionaries
                routes_data = [route.to_dict() for route in routes]
                
                # Save to cache file
                with open(cache_file, "w") as f:
                    json.dump(routes_data, f, indent=2)
                    
                logger.info(f"Cached {len(routes)} routes to {cache_file}")
            except Exception as e:
                logger.warning(f"Error caching routes: {str(e)}", exc_info=True)

        return routes

    async def _generate_route(
        self,
        origin: Airport,
        destination: Airport,
        route_type: str,
        aircraft: Optional[Any] = None,
        excluded_areas: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Route]:
        """Generate a single route of the specified type."""
        # Create a basic route
        route = Route(
            id=uuid4(),
            name=f"{origin.iata_code}-{destination.iata_code} ({route_type})",
            origin=origin,
            destination=destination,
            path_type=route_type,
        )

        # Calculate waypoints based on route type
        waypoints = self._calculate_waypoints(
            origin, destination, route_type, excluded_areas
        )
        route.waypoints = waypoints

        # Calculate total distance
        route.calculate_total_distance()

        # Get weather data for the route
        weather_data = await self.weather_service.get_weather_for_route(route)
        route.weather_data = weather_data

        # Calculate fitness score
        # If aircraft is a list, use the first one
        if aircraft and isinstance(aircraft, list) and len(aircraft) > 0:
            route.calculate_fitness_score(aircraft[0])
        else:
            route.calculate_fitness_score(aircraft)

        logger.info(
            f"Generated route: {route.name} with {len(waypoints)} waypoints, "
            f"distance: {route.distance:.2f} km, fitness: {route.fitness_score:.2f}"
        )

        return route

    def clear_cache(self, origin_code: Optional[str] = None, destination_code: Optional[str] = None):
        """
        Clear route cache for specific origin/destination or all routes.
        
        Args:
            origin_code: Optional origin airport code to clear specific cache
            destination_code: Optional destination airport code to clear specific cache
        """
        try:
            # If both origin and destination specified, clear only that specific cache
            if origin_code and destination_code:
                pattern = f"{origin_code}_{destination_code}_"
                for filename in os.listdir(self.cache_dir):
                    if filename.startswith(pattern) and filename.endswith(".json"):
                        os.remove(os.path.join(self.cache_dir, filename))
                        logger.info(f"Cleared cache for {origin_code} to {destination_code}: {filename}")
            
            # If only origin specified, clear all caches from that origin
            elif origin_code:
                pattern = f"{origin_code}_"
                for filename in os.listdir(self.cache_dir):
                    if filename.startswith(pattern) and filename.endswith(".json"):
                        os.remove(os.path.join(self.cache_dir, filename))
                        logger.info(f"Cleared cache for routes from {origin_code}: {filename}")
            
            # If only destination specified, clear all caches to that destination
            elif destination_code:
                for filename in os.listdir(self.cache_dir):
                    if f"_{destination_code}_" in filename and filename.endswith(".json"):
                        os.remove(os.path.join(self.cache_dir, filename))
                        logger.info(f"Cleared cache for routes to {destination_code}: {filename}")
            
            # If neither specified, clear all caches
            else:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith(".json"):
                        os.remove(os.path.join(self.cache_dir, filename))
                logger.info("Cleared all route caches")
                
        except Exception as e:
            logger.error(f"Error clearing route cache: {str(e)}", exc_info=True)

    def _calculate_waypoints(
        self,
        origin: Airport,
        destination: Airport,
        route_type: str,
        excluded_areas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Waypoint]:
        """
        Calculate waypoints between origin and destination based on route type.
        Uses Bézier curves to create smooth, realistic flight paths.

        Args:
            origin: Origin airport
            destination: Destination airport
            route_type: Type of route to generate ("direct", "left", "right", "north", "south", "wide")
            excluded_areas: List of areas to avoid (each with center lat/lng and radius)

        Returns:
            List of Waypoint objects
        """
        
        # Calculate direct distance and bearing
        direct_distance = origin.calculate_distance(destination)
        bearing = origin.calculate_bearing(destination)

        # Set number of waypoints
        num_waypoints = 20
        waypoints = []
        
        # For direct route, create a straight line
        if route_type == "direct":
            # FIRST WAYPOINT: Always use exact origin coordinates
            waypoints.append(Waypoint(
                id=uuid4(),
                name=f"WP1_{route_type}",
                latitude=origin.latitude,
                longitude=origin.longitude,
                order=1,
            ))
            
            # Create waypoints along the straight line
            for i in range(1, num_waypoints - 1):
                progress = i / (num_waypoints - 1)
                # Calculate position along the straight line
                waypoint_coords = self.path_calculator.calculate_position(
                    origin.latitude,
                    origin.longitude,
                    destination.latitude,
                    destination.longitude,
                    progress,
                    0,  # No deflection for direct route
                )
                
                waypoints.append(Waypoint(
                    id=uuid4(),
                    name=f"WP{i+1}_{route_type}",
                    latitude=waypoint_coords[0],
                    longitude=waypoint_coords[1],
                    order=i + 1,
                ))
            
            # LAST WAYPOINT: Always use exact destination coordinates
            waypoints.append(Waypoint(
                id=uuid4(),
                name=f"WP{num_waypoints}_{route_type}",
                latitude=destination.latitude,
                longitude=destination.longitude,
                order=num_waypoints,
            ))
            
            return waypoints
        
        # For other route types, use quadratic Bézier curves
        # First, define the control points for the Bézier curve
        start_coords = (origin.latitude, origin.longitude)
        end_coords = (destination.latitude, destination.longitude)
        
        # Calculate middle control point based on route type
        mid_lat = (start_coords[0] + end_coords[0]) / 2
        mid_lon = (start_coords[1] + end_coords[1]) / 2
        lat_diff = end_coords[0] - start_coords[0]
        lon_diff = end_coords[1] - start_coords[1]
        
        # Offset magnitude should scale with distance to ensure consistent curve shapes
        offset_magnitude = min(0.2, direct_distance / 2000)
        
        # Adjust control point based on route type
        if route_type == "left":
            mid_lat += lon_diff * offset_magnitude
            mid_lon -= lat_diff * offset_magnitude
        elif route_type == "right":
            mid_lat -= lon_diff * offset_magnitude
            mid_lon += lat_diff * offset_magnitude
        elif route_type == "wide":
            # Make a wider curve by moving control point further along the perpendicular
            mid_lat += lon_diff * offset_magnitude * 1.5
            mid_lon -= lat_diff * offset_magnitude * 1.5
        elif route_type == "north":
            # Move control point northward
            north_offset = offset_magnitude * 2
            mid_lat += north_offset
        elif route_type == "south":
            # Move control point southward
            south_offset = offset_magnitude * 2
            mid_lat -= south_offset
        
        # Check if control point is in excluded area and adjust if needed
        if excluded_areas:
            attempts = 0
            while attempts < 5 and self._is_in_excluded_area(
                (mid_lat, mid_lon), excluded_areas
            ):
                # Try to move the control point away from excluded area
                # by increasing the offset
                offset_magnitude *= 1.5
                
                if route_type == "left":
                    mid_lat += lon_diff * offset_magnitude
                    mid_lon -= lat_diff * offset_magnitude
                elif route_type == "right":
                    mid_lat -= lon_diff * offset_magnitude
                    mid_lon += lat_diff * offset_magnitude
                elif route_type == "wide":
                    mid_lat += lon_diff * offset_magnitude * 1.5
                    mid_lon -= lat_diff * offset_magnitude * 1.5
                elif route_type == "north":
                    mid_lat += offset_magnitude * 2
                elif route_type == "south":
                    mid_lat -= offset_magnitude * 2
                    
                attempts += 1
        
        # Generate waypoints using quadratic Bézier curve formula
        # B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂, where t ∈ [0,1]
        
        # FIRST WAYPOINT: Always use exact origin coordinates
        waypoints.append(Waypoint(
            id=uuid4(),
            name=f"WP1_{route_type}",
            latitude=origin.latitude,
            longitude=origin.longitude,
            order=1,
        ))
        
        # Create intermediate waypoints using the Bézier curve
        for i in range(1, num_waypoints - 1):
            t = i / (num_waypoints - 1)  # Parameter t varies from 0 to 1
            
            # Quadratic Bézier curve formula
            lat = (1 - t)**2 * start_coords[0] + 2 * (1 - t) * t * mid_lat + t**2 * end_coords[0]
            lon = (1 - t)**2 * start_coords[1] + 2 * (1 - t) * t * mid_lon + t**2 * end_coords[1]
            
            # Create waypoint
            waypoint = Waypoint(
                id=uuid4(),
                name=f"WP{i+1}_{route_type}",
                latitude=lat,
                longitude=lon,
                order=i + 1,
            )
            waypoints.append(waypoint)
        
        # LAST WAYPOINT: Always use exact destination coordinates
        waypoints.append(Waypoint(
            id=uuid4(),
            name=f"WP{num_waypoints}_{route_type}",
            latitude=destination.latitude,
            longitude=destination.longitude,
            order=num_waypoints,
        ))
        
        return waypoints

    def _is_in_excluded_area(
        self, coords: tuple, excluded_areas: List[Dict[str, Any]]
    ) -> bool:
        """Check if coordinates are within any excluded area."""
        for area in excluded_areas:
            if "center" in area and "radius_km" in area:
                center = area["center"]
                radius = area["radius_km"]

                # Calculate distance from point to area center
                center_point = (center["latitude"], center["longitude"])
                distance = self.path_calculator.calculate_distance(
                    coords[0], coords[1], center_point[0], center_point[1]
                )

                # If distance is less than radius, point is in excluded area
                if distance <= radius:
                    return True

        return False