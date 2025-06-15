import os
import logging
import json
import pandas as pd
from typing import List, Dict, Optional
from models.airport import Airport
from uuid import uuid4

logger = logging.getLogger(__name__)


class AirportAPI:
    """Interface to access airport data from local JSON files."""

    def __init__(self):
        self.data_dir = "data"
        self.airports_file = os.path.join(self.data_dir, "airports.json")
        self.routes_file = os.path.join(self.data_dir, "routes.json")
        self.cache_dir = "cache"
        self.ensure_cache_dir()

    def ensure_cache_dir(self):
        """Ensure cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def fetch_airports(self, country_code: Optional[str] = "IN") -> List[Airport]:
        """Fetch all airports, with optional country filter."""
        logger.info(f"Loading airports from local file: {self.airports_file}")

        try:
            with open(self.airports_file, "r", encoding="utf-8") as f:
                airports_data = json.load(f)

            # Filter by country if specified
            if country_code:
                airports_data = [
                    a for a in airports_data if a.get("country_code") == country_code
                ]

            # Convert to Airport objects with new model
            airports = []
            for airport_data in airports_data:
                airports.append(
                    Airport(
                        id=uuid4(),
                        iata_code=airport_data.get("code", ""),
                        name=airport_data.get("name", ""),
                        city=airport_data.get(
                            "city_code", ""
                        ),  # Using city_code as city name
                        country=airport_data.get("country_code", ""),
                        latitude=airport_data.get("coordinates", {}).get("lat", 0),
                        longitude=airport_data.get("coordinates", {}).get("lon", 0),
                    )
                )

            # Cache the processed results
            cache_file = os.path.join(
                self.cache_dir, f"airports_{country_code or 'all'}.json"
            )
            with open(cache_file, "w") as f:
                json.dump([airport.to_dict() for airport in airports], f)

            return airports

        except Exception as e:
            logger.error(f"Error loading airports from file: {str(e)}", exc_info=True)

            # Fall back to bundled data if JSON fails
            try:
                bundled_file = os.path.join("data", "narudata.csv")
                if not os.path.exists(bundled_file):
                    bundled_file = os.path.join("data", "airports.csv")

                df = pd.read_csv(bundled_file)

                if country_code:
                    df = df[df["country_code"] == country_code]

                airports = []
                for _, row in df.iterrows():
                    airports.append(
                        Airport(
                            id=uuid4(),
                            iata_code=row["iata_code"],
                            name=row["name"],
                            city=row["city"],
                            country=row["country_name"],
                            latitude=row["latitude"],
                            longitude=row["longitude"],
                        )
                    )

                return airports

            except Exception as inner_e:
                logger.error(
                    f"Error loading bundled airport data: {str(inner_e)}", exc_info=True
                )
                return []

    def fetch_routes(self, country_code: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Fetch all direct routes, with optional country filter for departure airports.

        Args:
            country_code: If provided, only include routes where departure airport is in this country

        Returns:
            Dictionary mapping departure airport codes to lists of destination airport codes
        """
        logger.info(f"Loading routes from local file: {self.routes_file}")

        try:
            with open(self.routes_file, "r",encoding="utf-8") as f:
                routes_data = json.load(f)

            # If country code is specified, we need to know which airports are in that country
            departure_airports_in_country = set()
            if country_code:
                logger.info(f"Filtering routes for country code: {country_code}")
                # Load airports to check country codes
                try:
                    with open(self.airports_file, "r",encoding="utf-8") as f:
                        airports_data = json.load(f)

                    # Create a set of airport codes in the specified country
                    departure_airports_in_country = {
                        airport.get("code")
                        for airport in airports_data
                        if airport.get("country_code") == country_code
                    }

                    logger.info(
                        f"Found {len(departure_airports_in_country)} airports in {country_code}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error loading airports for country filtering: {str(e)}",
                        exc_info=True,
                    )
                    # Continue without country filtering if airports can't be loaded

            # Process routes into dict of airport -> destinations
            airport_routes = {}
            for route in routes_data:
                origin = route.get("departure_airport_iata")
                destination = route.get("arrival_airport_iata")

                # Skip if origin or destination is missing
                if not origin or not destination:
                    continue

                # Skip if country_code is specified and origin airport is not in that country
                if (
                    country_code
                    and departure_airports_in_country
                    and origin not in departure_airports_in_country
                ):
                    continue

                if origin not in airport_routes:
                    airport_routes[origin] = []
                if destination not in airport_routes[origin]:
                    airport_routes[origin].append(destination)

            # Cache the results with country code in the filename if specified
            cache_filename = (
                f"routes_{country_code}.json" if country_code else "routes.json"
            )
            cache_file = os.path.join(self.cache_dir, cache_filename)
            with open(cache_file, "w") as f:
                json.dump(airport_routes, f)

            return airport_routes

        except Exception as e:
            logger.error(f"Error loading routes from file: {str(e)}", exc_info=True)

            # Fall back to bundled data if JSON fails
            try:
                bundled_file = os.path.join("data", "routes.csv")
                df = pd.read_csv(bundled_file)

                # Apply country filter on CSV data if needed
                if country_code:
                    # This assumes your CSV has a column with departure airport country codes
                    # If not, you'd need to join with airport data
                    if "departure_country" in df.columns:
                        df = df[df["departure_country"] == country_code]
                    else:
                        logger.warning(
                            "Cannot filter by country in CSV fallback - country column not present"
                        )

                airport_routes = {}
                for _, row in df.iterrows():
                    origin = row["origin"]
                    destination = row["destination"]

                    if origin not in airport_routes:
                        airport_routes[origin] = []
                    if destination not in airport_routes[origin]:
                        airport_routes[origin].append(destination)

                return airport_routes

            except Exception as inner_e:
                logger.error(
                    f"Error loading bundled route data: {str(inner_e)}", exc_info=True
                )
                return {}
