# Flight Optimization API – Reference Guide

================================================

## See also [REPORT.md](https://github.com/XronTrix10/flight-optimiser/blob/main/backend/REPORT.md) for technical details.

---

Base URL (default dev server)

```
http://localhost:8000
```

Health-check

```
GET /health          → 200 OK {"status":"healthy"}
```

No authentication is required right now; every endpoint returns JSON unless noted.

---

1. Airports API [controllers/airports_controller.py](file:///flight_optimization/controllers/airports_controller.py)

---

| Verb | Path                                   | Description                                  |
| ---- | -------------------------------------- | -------------------------------------------- |
| GET  | /api/airports                          | List airports (optionally filter by country) |
| GET  | /api/airports/routes                   | Direct-flight adjacency list                 |
| GET  | /api/airports/{iata_code}              | Airport detail by IATA code                  |
| GET  | /api/airports/{iata_code}/destinations | List airports reachable by direct flight     |

### 1.1 GET /api/airports

Query-string  ?country_code=IN (default “IN”).  
Response `200 OK` – array of Airport objects.

Airport schema

```json
{
  "iata_code": "BLR",
  "name": "Kempegowda International Airport",
  "city": "Bangalore",
  "country": "India",
  "latitude": 12.95,
  "longitude": 77.668,
  "timezone": "Asia/Kolkata",
  "direct_connections": ["DEL", "BOM", "..."]
}
```

### 1.2 GET /api/airports/routes

Returns a dictionary where each key is an origin IATA and the value is a list of IATA codes that can be reached by direct flight.

```json
{
  "BLR": ["DEL", "BOM"],
  "DEL": ["BLR", "BOM"]
}
```

### 1.3 GET /api/airports/{iata_code}

404 if airport not found.

### 1.4 GET /api/airports/{iata_code}/destinations

Returns a list of airports that can be reached by direct flight from the source airport.

```json
[
  {
    "id": "3f89390b-8dcb-43c8-b416-0af713658a4b",
    "iata_code": "CCU",
    "name": "Netaji Subhas Chandra Bose Airport",
    "city": "CCU",
    "country": "IN",
    "latitude": 22.64531,
    "longitude": 88.43931
  },
  {
    "id": "6097d359-1d74-4a93-91f9-89bba38f04fe",
    "iata_code": "BOM",
    "name": "Chhatrapati Shivaji International Airport",
    "city": "BOM",
    "country": "IN",
    "latitude": 19.095509,
    "longitude": 72.87497
  }..
]
```

---

2. Aircraft API [controllers/aircraft_controller.py](file:///flight_optimization/controllers/aircraft_controller.py)

---

| Verb | Path                  | Description              |
| ---- | --------------------- | ------------------------ |
| GET  | /api/aircraft         | List all aircraft models |
| GET  | /api/aircraft/{model} | Get specs for one model  |

Aircraft schema

```json
{
  "model": "A320",
  "manufacturer": "Airbus",
  "mtow_kg": 78000,
  "max_range_km": 6100,
  "cruise_speed_kmh": 840,
  "fuel_capacity_liters": 24210,
  "fuel_consumption_lph": 2500,
  "ceiling_m": 12000,
  "additional_specs": null
}
```

---

3. Route Generation & Management  
   [controllers/routes_controller.py](file:///flight_optimization/controllers/routes_controller.py)

---

| Verb | Path                   | Description                                                       |
| ---- | ---------------------- | ----------------------------------------------------------------- |
| POST | /api/routes/generate   | Create alternative routes and return the optimized one            |
| GET  | /api/routes/{route_id} | Fetch a stored route _(not yet implemented, returns 404)_         |
| POST | /api/routes/reroute    | Dynamically reroute a flight when encountering a blocked waypoint |
| GET  | /api/routes/ccu-routes | Generate and return optimized routes from CCU (Kolkata) to all available destinations |

### 3.1 POST /api/routes/generate

Request body

```json
{
  "origin": "BLR",
  "destination": "DEL",
  "aircraft_model": "Jet", // available options are "Jet", "Piston", "Turboprop"
  "route_types": ["direct", "left", "right", "north", "south", "wide"], // optional – default six presets
  "optimization_method": "aco", // "aco" | "genetic" | null
  "excluded_areas": [
    // optional – circles to avoid
    { "center": [12.8, 77.6], "radius": 0.2 }
  ]
}
```

Response `200 OK`

```json
{
  "all_routes": [ { /* Route */ }, ... ],
  "optimized_route": { /* Route */ }
}
```

Route schema (truncated)

```json
{
  "id": "9f4d7a08-6c2e-4e9d-9b47-fc8d2caa8e54",
  "name": "BLR to DEL (left)",
  "origin": {
    /* Airport */
  },
  "destination": {
    /* Airport */
  },
  "waypoints": [
    {
      "id": "7b44e510-c482-4c05-a40a-256e7a132842",
      "name": "WP1_direct",
      "latitude": 27.0562,
      "longitude": 76.2,
      "order": 1
    }
    // Additional waypoints...
  ],
  "path_type": "left",
  "optimization_method": "aco",
  "distance_km": 485.82069364597777,
  "fitness_score": 1.7962441147749173,
  "created_at": "2025-06-07T05:21:56.274642",
  "reroute_history": [],
  "fuel_consumption": 3106.84,
  "estimated_time": {
    "hours": 1,
    "minutes": 10
  }
}
```


### 3.2 `POST /api/routes/reroute`

Dynamically reroutes a flight when encountering a blocked waypoint using PPO.

**Request Body:**

```json
{
  "current_route": {
    // Current route object
  },
  "blocked_waypoint": {
    "id": "7b44e510-c482-4c05-a40a-256e7a132842",
    "name": "WP3_direct",
    "latitude": 25.0562,
    "longitude": 74.8,
    "order": 3
  },
  "aircraft_model": "Jet",
  "current_position": {
    "id": "7b44e510-c482-4c05-a40a-256e7a132842", // current waypoint id
    "latitude": 26.5,
    "longitude": 75.5
  },
  "alternative_routes": [
    // Array of alternative route objects
  ]
}
```

**Response:**

```json
{
  "rerouted_route": {
    "id": "a50e8400-e29b-41d4-a716-446655440123",
    "name": "Rerouted_DEL-BOM",
    "origin": {
      // Origin details
    },
    "destination": {
      // Destination details
    },
    "waypoints": [
      // Updated waypoints
    ],
    "path_type": "rerouted_north",
    "optimization_method": "ppo",
    "distance_km": 1195.32,
    "fitness_score": 4.56,
    "created_at": "2025-05-17T10:45:23.123456",
    "reroute_history": [["WP3_direct", "north"]],
    "fuel_consumption": 3106.84,
    "estimated_time": {
      "hours": 1,
      "minutes": 10
    }
  },
  "reroute_details": {
    "original_route_id": "550e8400-e29b-41d4-a716-446655440000",
    "blocked_waypoint": "WP3_direct",
    "reroute_starting_point": "WP2_direct",
    "alternative_route_type": "north",
    "distance_increase_km": 46.76
  }
}
```

### 3.2 GET /api/routes/ccu-routes

Generate and return optimized routes from CCU (Kolkata) to all available destinations.

Returns:

```json
{
   "origin": {
    "code": "CCU",
    "name": "Netaji Subhas Chandra Bose Airport",
    "city": "CCU",
    "country": "IN"
  },
  "route_count": 27,
  "routes": [
    {
      "destination": {
        "code": "AMD",
        "name": "Ahmedabad Airport",
        "city": "AMD",
        "country": "IN"
      },
      "route": {... Route object ...}
    },
    ... Other 26 routes ...
  ]
}


- `Note:` reroute_history is an empty array for now.
- `Note:` all_routes contains a route which is of type "direct". This route is a straight line between origin and destination. it is meant to be rendered as a straight line on the map for the user. Planes are not allowed to fly on a straight line.

Errors:  
• 404 if origin/destination not found  
• 500 on unexpected failure

---

6. Error Model

---

Every controller ultimately raises `fastapi.HTTPException`.  
Standard payload:

```json
{
  "detail": "Human-readable message"
}
```

Status codes used: 400, 404, 500, 501.

---

7. Environment / Config reference [utils/config.py](file:///flight_optimization/utils/config.py)

---

Important variables (defaults in parentheses):

- HOST (0.0.0.0) PORT (8000) DEBUG (False)
- TRAVELPAYOUTS_API_KEY
- REDIS_URL (for weather cache)
- WEATHER_CACHE_TTL (3600 s)
- DEFAULT_OPTIMIZATION_METHOD (aco)
- ACO_ITERATIONS (50) GA_GENERATIONS (50) POPULATION_SIZE (100)
- WEATHER_VS_DISTANCE_WEIGHT (0.7) etc.

---

8. Running the service

---

```bash
pip install -r requirements.txt
cp .env.example .env  # edit as needed
python main.py        # starts Uvicorn server
```

---

## Conclusion

The implementation of PPO, along with ACO and GA optimization techniques, has significantly enhanced our flight optimization system. The new APIs provide robust route generation, optimization, and dynamic rerouting capabilities that adapt to changing conditions in real-time, ensuring safer and more efficient flight operations.
