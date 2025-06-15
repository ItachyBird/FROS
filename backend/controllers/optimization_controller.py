import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID

from models.route import Route
from services.optimization.optimizer_factory import OptimizerFactory
from services.weather_service import WeatherService

logger = logging.getLogger(__name__)
router = APIRouter()

# Create services
weather_service = WeatherService()
optimizer_factory = OptimizerFactory(weather_service)


class OptimizeRoutesRequest(BaseModel):
    route_ids: List[str]
    optimization_method: Optional[str] = None


@router.post("/compare", response_model=Dict[str, Any])
async def compare_optimization_methods(routes: List[Dict[str, Any]]):
    """Compare different optimization methods on the same set of routes."""
    try:
        # Convert dict to Route objects
        route_objects = [Route(**route) for route in routes]

        # Run both optimization methods
        aco_optimizer = optimizer_factory.get_optimizer("aco")
        genetic_optimizer = optimizer_factory.get_optimizer("genetic")

        aco_result = aco_optimizer.optimize(route_objects)
        genetic_result = genetic_optimizer.optimize(route_objects)

        # Return results
        return {
            "aco_result": aco_result.to_dict() if aco_result else None,
            "genetic_result": genetic_result.to_dict() if genetic_result else None,
            "recommendation": (
                aco_result.to_dict()
                if (
                    aco_result
                    and genetic_result
                    and aco_result.fitness_score <= genetic_result.fitness_score
                )
                else genetic_result.to_dict()
            ),
        }

    except Exception as e:
        logger.error(f"Error comparing optimization methods: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_routes(optimize_request: OptimizeRoutesRequest):
    """
    Optimize a set of routes with a specified method.

    Note: This would normally fetch routes from a database, but for now
    we just return a placeholder error.
    """
    # In a real implementation, this would retrieve routes from a database
    # For now, we'll return a 404 as we don't have persistence
    raise HTTPException(
        status_code=501,
        detail="Route optimization from IDs not implemented - use /api/routes/generate instead",
    )
