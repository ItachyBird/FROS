# services/optimization/aco_optimizer.py
import logging
import numpy as np
from typing import List, Optional
from models.route import Route

logger = logging.getLogger(__name__)

class ACOOptimizer:
    """Ant Colony Optimization algorithm for route optimization."""
    
    def __init__(self, 
                 alpha: float = 1, 
                 beta: float = 2, 
                 evaporation_rate: float = 0.5, 
                 ants: int = 10, 
                 iterations: int = 10):
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.ants = ants
        self.iterations = iterations
        self.pheromone = {}
        
    def optimize(self, routes: List[Route]) -> Optional[Route]:
        """Optimize routes using Ant Colony Optimization."""
        if not routes:
            logger.warning("No routes provided for optimization")
            return None
            
        # Initialize pheromones for each route
        self.pheromone = {route.id: 1.0 for route in routes}
        
        best_route = None
        best_score = float('inf')
        
        logger.info(f"Running ACO optimization with {self.iterations} iterations and {self.ants} ants")
        
        for iteration in range(self.iterations):
            logger.debug(f"ACO Iteration {iteration+1}")
            all_scores = {}
            
            for _ in range(self.ants):
                route = self._select_route(routes)
                score = route.calculate_fitness_score()
                all_scores[route.id] = score
                
                if score < best_score:
                    best_score = score
                    best_route = route
                    
            self._update_pheromone(all_scores)
            
        if best_route:
            best_route.optimization_method = "aco"
            logger.info(f"ACO optimization complete. Best route score: {best_score}")
        
        return best_route
        
    def _select_route(self, routes: List[Route]) -> Route:
        """Select a route based on pheromone levels and heuristic information."""
        probabilities = []
        total = 0.0
        
        for route in routes:
            phero = self.pheromone[route.id] ** self.alpha
            heuristic = (1.0 / max(0.001, route.calculate_fitness_score())) ** self.beta
            score = phero * heuristic
            probabilities.append(score)
            total += score
            
        if total == 0:
            # Fallback to random selection if all scores are 0
            return np.random.choice(routes)
            
        probs = [p / total for p in probabilities]
        return np.random.choice(routes, p=probs)
        
    def _update_pheromone(self, scores):
        """Update pheromone levels based on route scores."""
        # Evaporation
        for route_id in self.pheromone:
            self.pheromone[route_id] *= (1 - self.evaporation_rate)
            
        # Deposit
        for route_id, score in scores.items():
            if score > 0:
                self.pheromone[route_id] += 1.0 / score
