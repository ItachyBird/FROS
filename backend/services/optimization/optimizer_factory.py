# services/optimization/optimizer_factory.py
import logging
from typing import Optional

from models.aircraft import Aircraft
from services.weather_service import WeatherService
from services.optimization.aco_optimizer import ACOOptimizer
from services.optimization.genetic_optimizer import GeneticOptimizer
from services.optimization.ppo_rerouter import PPORerouter

logger = logging.getLogger(__name__)

class OptimizerFactory:
    """Factory for creating route optimization algorithms."""
    
    def __init__(self, weather_service: WeatherService):
        self.weather_service = weather_service
        
    def get_optimizer(self, method: Optional[str] = None):
        """Return the appropriate optimizer based on method name."""
        method = method.lower() if method else "aco"
        
        if method == "aco":
            return ACOOptimizer()
        elif method == "genetic":
            return GeneticOptimizer()
        elif method == "ppo":
            # PPO is not a standalone optimizer but a rerouter
            # This is here for completeness, but should be used through the reroute method
            return ACOOptimizer()  # Default to ACO when incorrectly called
        else:
            logger.warning(f"Unknown optimization method: {method}. Using ACO as default.")
            return ACOOptimizer()
            
    def get_rerouter(self, aircraft: Aircraft=None) -> PPORerouter:
        """Get a PPO rerouter instance."""

        ppo_router = PPORerouter(self.weather_service, aircraft)
        ppo_router.consider_fuel = True

        return ppo_router
