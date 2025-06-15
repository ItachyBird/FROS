# controllers/airports_controller.py
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from api.airport_api import AirportAPI

logger = logging.getLogger(__name__)
router = APIRouter()

airport_api = AirportAPI()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_airports(country_code: str = "IN"):
    """
    Get all airports, optionally filtered by country code.
    Default is India (IN).
    """
    try:
        airports = airport_api.fetch_airports(country_code)
        return [airport.to_dict() for airport in airports]
    except Exception as e:
        logger.error(f"Error fetching airports: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes", response_model=Dict[str, List[str]])
async def get_direct_routes(country_code: Optional[str] = "IN"):
    """
    Get all direct routes between airports, optionally filtered by country code.
    Default is India (IN).
    """
    try:
        routes = airport_api.fetch_routes(country_code)
        return routes
    except Exception as e:
        logger.error(f"Error fetching routes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{iata_code}", response_model=Dict[str, Any])
async def get_airport(iata_code: str):
    """Get airport details by IATA code."""
    try:
        airports = await airport_api.fetch_airports()
        for airport in airports:
            if airport.iata_code.upper() == iata_code.upper():
                return airport.to_dict()
        raise HTTPException(status_code=404, detail=f"Airport {iata_code} not found")
    except Exception as e:
        logger.error(f"Error fetching airport {iata_code}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{iata_code}/destinations", response_model=List[Dict[str, Any]])
async def get_destinations(iata_code: str):
    """
    Get all available destination airports from a specific source airport.
    
    Args:
        iata_code: IATA code of the source airport
    
    Returns:
        List of airport objects that are directly reachable from the source airport
    """
    try:
        # Get the routes dictionary
        routes = airport_api.fetch_routes()
        
        # Check if the source airport exists in routes
        if iata_code.upper() not in routes:
            raise HTTPException(
                status_code=404, 
                detail=f"No destinations found for airport {iata_code}"
            )
            
        # Get destination IATA codes
        destination_codes = routes[iata_code.upper()]
        
        # Get all airports to find details for destination codes
        all_airports = airport_api.fetch_airports()
        
        # Filter airports by destination codes
        destination_airports = [
            airport.to_dict() for airport in all_airports 
            if airport.iata_code in destination_codes
        ]
        
        return destination_airports
        
    except Exception as e:
        logger.error(f"Error fetching destinations for {iata_code}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

