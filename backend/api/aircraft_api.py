# api/aircraft_api.py
import os
import json  # still used when we persist a cached JSON version
import logging
from typing import List, Optional, Dict, Any

import pandas as pd  # NEW: read the CSV file

from models.aircraft import Aircraft

logger = logging.getLogger(__name__)


class AircraftAPI:
    """
    Interface for aircraft specifications data.

    Primary source  : data/aircraft.csv
    Cached JSON copy: data/aircraft.json   (auto-generated to speed up reloads)
    """

    def __init__(self) -> None:
        self.csv_file = os.path.join("data", "aircraft.csv")
        self.json_cache_file = os.path.join("cache", "aircraft.json")
        self.aircraft_cache: Optional[List[Aircraft]] = None

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #
    async def get_all_aircraft(self) -> List[Aircraft]:
        """
        Return every aircraft entry found in aircraft.csv.
        Creates aircraft.json as a fast reload cache the first time we parse
        the CSV (or whenever the CSV is newer than the cache).
        """
        if self.aircraft_cache is not None:
            return self.aircraft_cache

        # 1) Try fast-path: cached JSON ----------------------------------
        if await self._cache_is_fresh():
            try:
                with open(self.json_cache_file, "r") as fh:
                    cached_data = json.load(fh)
                self.aircraft_cache = [Aircraft(**row) for row in cached_data]
                return self.aircraft_cache
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Failed to load aircraft JSON cache (%s): %s",
                    self.json_cache_file,
                    exc,
                )

        # 2) Parse the CSV ------------------------------------------------
        if os.path.exists(self.csv_file):
            try:
                df = pd.read_csv(self.csv_file)

                aircraft_list: List[Aircraft] = []
                for _, row in df.iterrows():
                    aircraft_list.append(self._row_to_aircraft(row))

                # Persist JSON cache for next boot
                self._save_json_cache(aircraft_list)

                self.aircraft_cache = aircraft_list
                return aircraft_list

            except Exception as exc:
                logger.error(
                    "Error parsing aircraft CSV %s: %s",
                    self.csv_file,
                    exc,
                    exc_info=True,
                )

        # 3) Fallback default list ---------------------------------------
        logger.warning("Using default aircraft list - CSV file not found")
        self.aircraft_cache = self._get_default_aircraft()
        return self.aircraft_cache

    async def get_aircraft(self, model: str, **specs) -> List[Aircraft]:
        """Return aircraft by case-insensitive model name and optional specifications.

        Args:
            model: The aircraft model name (case-insensitive)
            **specs: Optional specifications to filter by (e.g. manufacturer, mtow_kg)

        Returns:
            List of matching Aircraft objects, or empty list if none found
        """
        aircraft_list = await self.get_all_aircraft()
        matching_aircraft = []

        for ac in aircraft_list:
            # First filter by model name (case-insensitive)
            if ac.model.lower() == model.lower():
                # If no specs provided, add to matches
                if not specs:
                    matching_aircraft.append(ac)
                    continue

                # If specs provided, check if all specs match
                specs_match = True
                for key, value in specs.items():
                    if hasattr(ac, key):
                        # Convert to same type for comparison
                        ac_value = getattr(ac, key)
                        if type(ac_value) is float and type(value) is str:
                            try:
                                value = float(value)
                            except ValueError:
                                specs_match = False
                                break

                        # Compare values
                        if ac_value != value:
                            specs_match = False
                            break
                    else:
                        # If aircraft doesn't have the specified attribute
                        specs_match = False
                        break

                if specs_match:
                    matching_aircraft.append(ac)

        return matching_aircraft

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    async def _cache_is_fresh(self) -> bool:
        """
        Return True if aircraft.json exists and is newer than aircraft.csv.
        """
        if not (os.path.exists(self.json_cache_file) and os.path.exists(self.csv_file)):
            return False
        return os.path.getmtime(self.json_cache_file) >= os.path.getmtime(self.csv_file)

    def _save_json_cache(self, aircraft_list: List[Aircraft]) -> None:
        """Persist a pretty-printed JSON cache beside the CSV file."""
        try:
            os.makedirs(
                os.path.dirname(self.json_cache_file), exist_ok=True
            )  # Create cache directory if it doesn't exist
            with open(self.json_cache_file, "w") as fh:
                json.dump([ac.to_dict() for ac in aircraft_list], fh, indent=2)
        except Exception as exc:  # pragma: no cover
            logger.warning("Could not write aircraft JSON cache: %s", exc)

    # ---------------- CSV → Aircraft conversion ------------------------ #
    @staticmethod
    def _row_to_aircraft(row) -> Aircraft:
        """
        Map a pandas Series (one CSV line) to our Aircraft pydantic model.

        Column → Aircraft field mapping (+ unit conversions):
        ------------------------------------------------------
        Engine_Type              ➜ model  (we'll use this until we have a proper model field)
        *manufacturer*           ➜ 'Unknown' (CSV lacks this - change if you add a column)
        MTOW_kg                  ➜ mtow_kg
        Range_km                 ➜ max_range_km
        Cruise_Speed_knots       ➜ cruise_speed_kmh  (knots x 1.852)
        Fuel_Capacity_L          ➜ fuel_capacity_liters
        Fuel_Consumption_Rate_kg_hr ➜ fuel_consumption_rate_kg_hr
        Cruising_Altitude_ft     ➜ ceiling_m (ft x 0.3048)

        All remaining CSV columns are tucked into Aircraft.additional_specs
        for completeness.
        """
        # mandatory / mapped fields
        model = str(
            row.get("Engine_Type", "Unknown")
        ).strip()  # We'll use Engine_Type as model for now
        manufacturer = "Unknown"
        mtow_kg = float(row.get("MTOW_kg", 0))
        max_range_km = float(row.get("Range_km", 0))
        cruise_speed_kmh = float(row.get("Cruise_Speed_knots", 0)) * 1.852
        fuel_capacity_liters = float(row.get("Fuel_Capacity_L", 0))
        fuel_consumption_rate_kg_hr = float(row.get("Fuel_Consumption_Rate_kg_hr", 0))
        ceiling_m = float(row.get("Cruising_Altitude_ft", 0)) * 0.3048

        # collect any additional columns into a dict
        std_cols = {
            "Engine_Type",
            "MTOW_kg",
            "Range_km",
            "Fuel_Consumption_Rate_kg_hr",
            "Cruise_Speed_knots",
            "Cruising_Altitude_ft",
            "Fuel_Capacity_L",
        }
        additional_specs: Dict[str, Any] = {
            col: (None if pd.isna(val) else val)
            for col, val in row.items()
            if col not in std_cols
        }

        return Aircraft(
            model=model,
            manufacturer=manufacturer,
            mtow_kg=mtow_kg,
            max_range_km=max_range_km,
            cruise_speed_kmh=cruise_speed_kmh,
            fuel_capacity_liters=fuel_capacity_liters,
            fuel_consumption_rate_kg_hr=fuel_consumption_rate_kg_hr,
            ceiling_m=ceiling_m,
            additional_specs=additional_specs or None,
        )

    # ---------------- hard-coded fallback list ------------------------- #
    @staticmethod
    def _get_default_aircraft() -> List[Aircraft]:
        """Return a minimal hard-coded catalogue if CSV is unavailable."""
        return [
            Aircraft(
                model="A320",
                manufacturer="Airbus",
                mtow_kg=78000,
                max_range_km=6100,
                cruise_speed_kmh=840,
                fuel_capacity_liters=24210,
                fuel_consumption_rate_kg_hr=2500,
                ceiling_m=12000,
            ),
            Aircraft(
                model="B737-800",
                manufacturer="Boeing",
                mtow_kg=79010,
                max_range_km=5765,
                cruise_speed_kmh=842,
                fuel_capacity_liters=26020,
                fuel_consumption_rate_kg_hr=2600,
                ceiling_m=12500,
            ),
            Aircraft(
                model="ATR-72",
                manufacturer="ATR",
                mtow_kg=23000,
                max_range_km=1700,
                cruise_speed_kmh=511,
                fuel_capacity_liters=5000,
                fuel_consumption_rate_kg_hr=800,
                ceiling_m=7600,
            ),
        ]
