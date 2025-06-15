# services/optimization/genetic_optimizer.py
import logging
import random
from typing import List, Optional
from models.route import Route

logger = logging.getLogger(__name__)

class GeneticOptimizer:
    """Genetic Algorithm for route optimization."""
    
    def __init__(self, 
                 generations: int = 20, 
                 population_size: int = 10, 
                 mutation_rate: float = 0.2,
                 elite_size: int = 2):
        self.generations = generations
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        
    def optimize(self, routes: List[Route]) -> Optional[Route]:
        """Optimize routes using a Genetic Algorithm."""
        if not routes:
            logger.warning("No routes provided for optimization")
            return None
            
        if len(routes) < 2:
            logger.warning("Genetic algorithm needs at least 2 routes")
            return routes[0]
            
        # Initial population
        population = random.choices(routes, k=self.population_size)
        
        logger.info(f"Running Genetic optimization with {self.generations} generations")
        
        for gen in range(self.generations):
            logger.debug(f"GA Generation {gen+1}")
            
            # Score and sort the population
            scored = sorted(population, key=lambda r: r.calculate_fitness_score())
            
            # Select elites directly for next generation
            next_gen = scored[:self.elite_size]
            
            # Generate the rest of the population through crossover and mutation
            while len(next_gen) < self.population_size:
                # Tournament selection
                parent1, parent2 = self._selection(scored)
                child = self._crossover(parent1, parent2)
                
                # Apply mutation with probability
                if random.random() < self.mutation_rate:
                    child = self._mutate(child, routes)
                    
                next_gen.append(child)
                
            population = next_gen
            
        # Return the best route from the final population
        best_route = min(population, key=lambda r: r.calculate_fitness_score())
        best_route.optimization_method = "genetic"
        
        logger.info(f"Genetic optimization complete. Best route score: {best_route.calculate_fitness_score()}")
        return best_route
        
    def _selection(self, scored_population: List[Route]) -> tuple:
        """Tournament selection for parent routes."""
        # Prefer routes with better scores (lower values)
        tournament_size = min(5, len(scored_population))
        tournament = random.sample(scored_population[:max(tournament_size, len(scored_population)//2)], 2)
        return tournament[0], tournament[1]
        
    def _crossover(self, parent1: Route, parent2: Route) -> Route:
        """Crossover operation between two parent routes."""
        # Simple implementation: choose the better parent
        if parent1.calculate_fitness_score() <= parent2.calculate_fitness_score():
            return parent1
        return parent2
        
    def _mutate(self, route: Route, all_routes: List[Route]) -> Route:
        """Mutation operation to introduce variation."""
        # Simple implementation: replace with another random route
        alternatives = [r for r in all_routes if r.id != route.id]
        if alternatives:
            return random.choice(alternatives)
        return route
