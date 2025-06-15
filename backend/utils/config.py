import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# API keys
TRAVELPAYOUTS_API_KEY = os.getenv("TRAVELPAYOUTS_API_KEY")

# Cache configuration
REDIS_URL = os.getenv("REDIS_URL")
WEATHER_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", 3600))  # Default: 1 hour

# Optimization settings
DEFAULT_OPTIMIZATION_METHOD = os.getenv("DEFAULT_OPTIMIZATION_METHOD", "aco")
ACO_ITERATIONS = int(os.getenv("ACO_ITERATIONS", 50))
GA_GENERATIONS = int(os.getenv("GA_GENERATIONS", 50))
POPULATION_SIZE = int(os.getenv("POPULATION_SIZE", 100))

# Weather weights
PRECIPITATION_WEIGHT = float(os.getenv("PRECIPITATION_WEIGHT", 0.6))
CLOUD_COVER_WEIGHT = float(os.getenv("CLOUD_COVER_WEIGHT", 0.4))
WEATHER_VS_DISTANCE_WEIGHT = float(os.getenv("WEATHER_VS_DISTANCE_WEIGHT", 0.7))

# Flight parameters
MIN_FLIGHT_DISTANCE_KM = float(os.getenv("MIN_FLIGHT_DISTANCE_KM", 100))
MAX_FLIGHT_DISTANCE_KM = float(os.getenv("MAX_FLIGHT_DISTANCE_KM", 5000))


# Setup logging
def configure_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.getenv("LOG_FILE", "app.log")),
        ],
    )
