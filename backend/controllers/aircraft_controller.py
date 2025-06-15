import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from api.aircraft_api import AircraftAPI

logger = logging.getLogger(__name__)
router = APIRouter()

aircraft_api = AircraftAPI()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_aircraft():
    """Get all available aircraft models."""
    try:
        aircraft_list = await aircraft_api.get_all_aircraft()
        return [aircraft.to_dict() for aircraft in aircraft_list]
    except Exception as e:
        logger.error(f"Error fetching aircraft: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model}", response_model=List[Dict[str, Any]])
async def get_aircraft(model: str, request: Request):
    """Get aircraft details by model name.

    Can filter by additional specifications as query parameters.
    If no query parameters are provided, returns all aircraft with matching model name.
    """
    try:
        # Extract query parameters as specs
        specs = {}
        for key, value in request.query_params.items():
            if key != "model":  # Skip the model parameter
                specs[key] = value

        # Get matching aircraft
        matching_aircraft = await aircraft_api.get_aircraft(model, **specs)

        if not matching_aircraft:
            raise HTTPException(
                status_code=404,
                detail=f"No aircraft models matching '{model}'{' with given specifications' if specs else ''} found",
            )

        # Return list of aircraft
        return [ac.to_dict() for ac in matching_aircraft]

    except Exception as e:
        logger.error(f"Error fetching aircraft {model}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
