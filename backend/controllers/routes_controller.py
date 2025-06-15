import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.route import Route

from services.route_generator import RouteGenerator
from services.optimization.optimizer_factory import OptimizerFactory
from services.weather_service import WeatherService
from api.airport_api import AirportAPI
from api.aircraft_api import AircraftAPI

logger = logging.getLogger(__name__)
router = APIRouter()

class AircraftModel(BaseModel):
    model: str
    mtow_kg: float
    max_range_km: float
    fuel_consumption_rate_kg_hr: float

# Models for request/response
class RouteRequest(BaseModel):
    origin: str
    destination: str
    aircraft_model: Optional[str] = None
    route_types: Optional[List[str]] = None
    optimization_method: Optional[str] = None
    excluded_areas: Optional[List[Dict[str, Any]]] = None
    use_cache: bool = True

class BlockWaypointRequest(BaseModel):
    route_id: str
    waypoint_id: str

# Add these request models
class RouteOptimizationRequest(BaseModel):
    routes: List[Dict[str, Any]]
    method: str = "aco"  # "aco", "genetic", or "ppo"
    iterations: int = 50

class RerouteRequest(BaseModel):
    current_route: Dict[str, Any]
    blocked_waypoint: Dict[str, Any]
    current_position: Dict[str, Any]
    alternative_routes: Optional[List[Dict[str, Any]]] = None
    aircraft_model: Optional[str] = None

# Create shared services
airport_api = AirportAPI()
aircraft_api = AircraftAPI()
weather_service = WeatherService()
optimizer_factory = OptimizerFactory(weather_service)
route_generator = RouteGenerator(weather_service)

@router.post("/generate", response_model=Dict[str, Any])
async def generate_routes(route_request: RouteRequest):
    """Generate and optimize routes between two airports."""
    try:
        logger.info(
            f"Generating routes from {route_request.origin} to {route_request.destination}"
        )
        # Get airport data
        airports = airport_api.fetch_airports()
        airport_dict = {airport.iata_code: airport for airport in airports}

        # Validate airports
        if route_request.origin not in airport_dict:
            raise HTTPException(
                status_code=404,
                detail=f"Origin airport {route_request.origin} not found",
            )
        if route_request.destination not in airport_dict:
            raise HTTPException(
                status_code=404,
                detail=f"Destination airport {route_request.destination} not found",
            )

        origin = airport_dict[route_request.origin]
        destination = airport_dict[route_request.destination]

        # Get aircraft if specified
        aircraft = None
        if route_request.aircraft_model:
            aircraft = await aircraft_api.get_aircraft(route_request.aircraft_model)
            if not aircraft:
                raise HTTPException(
                    status_code=404,
                    detail=f"Aircraft model {route_request.aircraft_model} not found",
                )
            else:
                aircraft = aircraft[0]  # Return only the first aircraft found

        # Generate alternative routes
        routes = await route_generator.generate_alternative_routes(
            origin=origin,
            destination=destination,
            route_types=route_request.route_types,
            aircraft_model=route_request.aircraft_model,
            excluded_areas=route_request.excluded_areas,
            use_cache=route_request.use_cache,
        )

        routes_for_optimization = route_generator.filter_routes_for_optimization(routes)

        # Optimize routes
        optimizer = optimizer_factory.get_optimizer(route_request.optimization_method)
        optimized_route = optimizer.optimize(routes_for_optimization)

        # Calculate estimated fuel consumption and time if aircraft was specified
        if aircraft and optimized_route:
            optimized_route.fuel_consumption = (
                optimized_route.calculate_fuel_consumption(
                    aircraft, optimized_route.weather_data
                )
            )
            optimized_route.estimated_time = optimized_route.calculate_estimated_time(
                aircraft
            )
            optimized_route.calculate_leg_times(aircraft)  # <-- Calculate per-segment times

        # Update all routes with estimated time and per-segment times
        if aircraft:
            for route in routes:
                route.fuel_consumption = route.calculate_fuel_consumption(
                    aircraft, route.weather_data
                )
                route.estimated_time = route.calculate_estimated_time(aircraft)
                route.calculate_total_distance()  # Ensure per-leg distances are calculated
                route.calculate_leg_times(aircraft)  # <-- Calculate per-segment times

        # Return all routes and optimized route
        return {
            "all_routes": [route.to_dict() for route in routes],
            "optimized_route": optimized_route.to_dict() if optimized_route else None,
        }

    except Exception as e:
        logger.error(f"Error generating routes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reroute", response_model=Dict[str, Any])
async def reroute_flight(reroute_request: RerouteRequest):
    """Dynamically reroute a flight when encountering a blocked waypoint using PPO."""
    try:
        logger.info(f"Rerouting flight around blocked waypoint")

        # Convert dictionary data to model objects
        current_route = Route.from_dict(reroute_request.current_route)

        # Convert waypoint dict to object
        from models.waypoint import Waypoint

        blocked_waypoint = Waypoint.from_dict(reroute_request.blocked_waypoint)

        # Create current position waypoint
        from uuid import uuid4

        current_position = Waypoint(
            id=uuid4(),
            name="CurrentPosition",
            latitude=reroute_request.current_position["latitude"],
            longitude=reroute_request.current_position["longitude"],
            order=0,
        )

        # Convert alternative routes if provided
        alternative_routes = []
        if reroute_request.alternative_routes:
            alternative_routes = [
                Route.from_dict(route_data)
                for route_data in reroute_request.alternative_routes
            ]

        # If no alternative routes provided, generate some
        if not alternative_routes:
            # Get airport data
            airports = await airport_api.fetch_airports()
            airport_dict = {airport.iata_code: airport for airport in airports}

            # Generate alternative routes
            alternative_routes = await route_generator.generate_alternative_routes(
                origin=current_route.origin,
                destination=current_route.destination,
                route_types=["left", "right", "north", "south", "wide"],
                excluded_areas=[
                    {
                        "center": {
                            "latitude": blocked_waypoint.latitude,
                            "longitude": blocked_waypoint.longitude,
                        },
                        "radius_km": 100,
                    }
                ],
            )

        # Get aircraft if specified
        aircraft = None
        if reroute_request.aircraft_model:
            aircraft = await aircraft_api.get_aircraft(reroute_request.aircraft_model)
            if not aircraft:
                aircraft = await aircraft_api.get_aircraft("Jet")[0]
            else:
                aircraft = aircraft[0]  # Return only the first aircraft found

        # Get PPO rerouter
        ppo_rerouter = optimizer_factory.get_rerouter(aircraft)

        # Perform rerouting
        rerouted_route = await ppo_rerouter.reroute(
            blocked_waypoint=blocked_waypoint,
            current_route=current_route,
            alternative_routes=alternative_routes,
            current_position=current_position,
        )

        if not rerouted_route:
            raise HTTPException(
                status_code=500, detail="Rerouting failed to produce a valid route"
            )

        # Calculate original route ID and other metadata for the response
        original_route_id = str(current_route.id)

        # Determine the waypoint before the blocked one
        try:
            blocked_index = current_route.waypoints.index(blocked_waypoint)
            if blocked_index > 0:
                reroute_starting_point = current_route.waypoints[blocked_index - 1].name
            else:
                reroute_starting_point = (
                    current_route.origin.name if current_route.origin else "Unknown"
                )
        except ValueError:
            reroute_starting_point = "Unknown"

        # Determine alternative route type
        alt_route_type = "unknown"
        if (
            hasattr(rerouted_route, "reroute_history")
            and rerouted_route.reroute_history
        ):
            last_reroute = rerouted_route.reroute_history[-1]
            if len(last_reroute) >= 2:
                alt_route_type = last_reroute[1]

        if not rerouted_route.estimated_time and aircraft:
            # Calculate flight time if it wasn't already done
            flight_time = rerouted_route.calculate_estimated_time(aircraft)
            rerouted_route.estimated_time = flight_time

        rerouted_route.calculate_total_distance()  # Ensures leg_distances is up to date
        if aircraft:
            rerouted_route.calculate_leg_times(aircraft)  # <-- Added: Calculate per-segment times

        # Calculate distance increase
        distance_increase_km = rerouted_route.distance - current_route.distance

        return {
            "rerouted_route": rerouted_route.to_dict(),
            "reroute_details": {
                "original_route_id": original_route_id,
                "blocked_waypoint": blocked_waypoint.name,
                "reroute_starting_point": reroute_starting_point,
                "alternative_route_type": alt_route_type,
                "distance_increase_km": distance_increase_km,
                "rerouted_segment_distances": rerouted_route.leg_distances,
                "rerouted_segment_times": rerouted_route.leg_times,  # <-- Add segment times in response
            },
        }

    except Exception as e:
        logger.error(f"Error rerouting flight: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ccu-routes", response_model=Dict[str, Any])
async def get_ccu_routes():
    """
    Generate and return optimized routes from CCU (Kolkata) to all available destinations.

    Returns:
        Dictionary containing routes to all available destinations from CCU
    """
    try:
        logger.info("Generating routes from CCU to all available destinations")

        # Get all airports
        airports = airport_api.fetch_airports()
        airport_dict = {airport.iata_code: airport for airport in airports}

        # Verify CCU exists
        if "CCU" not in airport_dict:
            raise HTTPException(
                status_code=404, detail="Origin airport CCU (Kolkata) not found"
            )

        origin = airport_dict["CCU"]

        # Get available destinations from CCU
        routes = airport_api.fetch_routes()

        # Check if CCU has any destinations
        if "CCU" not in routes:
            return {"message": "No destinations found for CCU airport", "routes": []}

        destination_codes = routes["CCU"]

        # Get default aircraft for calculations
        default_aircraft = await aircraft_api.get_aircraft("Jet")
        if default_aircraft and len(default_aircraft) > 0:
            aircraft = default_aircraft[0]
        else:
            aircraft = None

        # Generate routes to each destination
        all_routes = []

        for dest_code in destination_codes:
            # Skip if destination airport not found
            if dest_code not in airport_dict:
                logger.warning(
                    f"Destination airport {dest_code} not found in airport database"
                )
                continue

            destination = airport_dict[dest_code]

            # Generate route (using just direct route type for efficiency)
            routes = await route_generator.generate_alternative_routes(
                origin=origin,
                destination=destination,
                route_types=["direct"],
                aircraft_model=aircraft.model if aircraft else None,
                use_cache=True,
            )

            # Skip if no routes could be generated
            if not routes:
                logger.warning(f"No routes could be generated from CCU to {dest_code}")
                continue

            # Use optimizer to find best route
            optimizer = optimizer_factory.get_optimizer("aco")  # Default to ACO
            optimized_route = optimizer.optimize(routes)

            if optimized_route:
                # Add fuel consumption and time estimates if aircraft is available
                if aircraft:
                    optimized_route.fuel_consumption = (
                        optimized_route.calculate_fuel_consumption(
                            aircraft, optimized_route.weather_data
                        )
                    )
                    optimized_route.estimated_time = (
                        optimized_route.calculate_estimated_time(aircraft)
                    )
                    optimized_route.calculate_leg_times(aircraft)  # <-- Calculate per-segment times
                optimized_route.calculate_total_distance()  # Ensure leg_distances is calculated

                # Add to results
                all_routes.append(
                    {
                        "destination": {
                            "code": destination.iata_code,
                            "name": destination.name,
                            "city": destination.city,
                            "country": destination.country,
                        },
                        "route": optimized_route.to_dict(),
                    }
                )

        return {
            "origin": {
                "code": origin.iata_code,
                "name": origin.name,
                "city": origin.city,
                "country": origin.country,
            },
            "route_count": len(all_routes),
            "routes": all_routes,
        }

    except Exception as e:
        logger.error(f"Error generating routes from CCU: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{route_id}", response_model=Dict[str, Any])
async def get_route(route_id: str):
    """Get a specific route by ID."""
    # In a real implementation, this would retrieve from a database
    # For now, we'll return a 404 as we don't have persistence
    raise HTTPException(status_code=404, detail=f"Route {route_id} not found")


@router.post("/block-waypoint", response_model=Dict[str, Any])
async def block_waypoint(request: BlockWaypointRequest):
    """Register a blocked waypoint and recalculate the route."""
    from realtime.route_adjuster import route_adjuster

    try:
        new_route = await route_adjuster.handle_blocked_waypoint(
            request.route_id, request.waypoint_id
        )

        if not new_route:
            raise HTTPException(
                status_code=404, detail=f"Route {request.route_id} not found"
            )

        return {"new_route": new_route.to_dict()}

    except Exception as e:
        logger.error(f"Error handling blocked waypoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_routes(optimization_request: RouteOptimizationRequest):
    """Optimize a set of routes using the specified method."""
    try:
        logger.info(f"Optimizing routes using {optimization_request.method} method")

        # Convert route dictionaries to Route objects
        routes = [
            Route.from_dict(route_data) for route_data in optimization_request.routes
        ]

        if not routes:
            raise HTTPException(
                status_code=400, detail="No routes provided for optimization"
            )

        # Get optimizer based on method
        optimizer = optimizer_factory.get_optimizer(optimization_request.method)

        # Set iterations if provided
        if hasattr(optimizer, "iterations"):
            optimizer.iterations = optimization_request.iterations

        # Perform optimization
        import time

        start_time = time.time()
        optimized_route = optimizer.optimize(routes)
        execution_time_ms = (time.time() - start_time) * 1000

        if not optimized_route:
            raise HTTPException(
                status_code=500, detail="Optimization failed to produce a valid route"
            )

        optimized_route.calculate_total_distance()  # Ensure per-leg distances
        if hasattr(optimized_route, "calculate_leg_times"):
            # Try to get the aircraft for per-leg times if present in input
            if hasattr(optimized_route, "aircraft") and optimized_route.aircraft:
                optimized_route.calculate_leg_times(optimized_route.aircraft)
            else:
                # Try to get a default aircraft if not present
                default_aircraft = await aircraft_api.get_aircraft("Jet")
                if default_aircraft and len(default_aircraft) > 0:
                    optimized_route.calculate_leg_times(default_aircraft[0])

        return {
            "optimized_route": optimized_route.to_dict(),
            "optimization_method": optimization_request.method,
            "fitness_score": optimized_route.fitness_score,
            "execution_time_ms": execution_time_ms,
        }

    except Exception as e:
        logger.error(f"Error optimizing routes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))