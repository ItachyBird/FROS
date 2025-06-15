===================

# Comprehensive Technical Report -- “Flight-Route Generation, Evaluation & Dynamic Rerouting System”  

===================

## CONTENTS  

1. High-Level Architecture  
2. Core Data-Models & Geo-Math Utilities  
3. Weather Pipeline – parameters collected & caching  
4. Per-Route Fuel & Risk Evaluation (fitness function)  
5. Ant Colony Optimisation (ACO) – static route selection  
6. PPO-based Rerouter – dynamic block avoidance  
7. Putting it all together – end-to-end flow  
8. Key Equations (quick reference)  

──────────────────────────────────────────────────────────────────
### 1. HIGH-LEVEL ARCHITECTURE
──────────────────────────────────────────────────────────────────

```
                         ┌───────────────┐
                         │ AirportAPI    │  ← local JSON/CSV
                         └──────┬────────┘
                                │Airports
                                ▼
   Client ▸ FastAPI ▸ routes_controller.py
                                │
            ┌───────────────────┴───────────────────┐
            │                                       │
  RouteGenerator (static alternatives)     PPORerouter (live)
   │ uses PathCalculator + WeatherService   │ uses WeatherService
   │                                        │
   ▼                                        ▼
 Optimisers/Factory ——— (ACO | GA) <—— fitness() ———  Route model
                                ▲
                                │weather_data (cached per lat/lon)
                                │fuel, risks, distance
                                ▼
                         Open-Meteo API (free)
```

#### Key folders / files (click-through):

– [route.py](https://github.com/XronTrix10/flight-optimiser/blob/main/models/route.py) (fitness, fuel, risk)  
– [waypoint.py](https://github.com/XronTrix10/flight-optimiser/blob/main/models/waypoint.py) (distance, bearing)  
– [path_calculator.py](https://github.com/XronTrix10/flight-optimiser/blob/main/services/path_calculator.py) (great-circle + deflection)  
– [aco_optimizer.py](https://github.com/XronTrix10/flight-optimiser/blob/main/services/optimization/aco_optimizer.py)  
– [ppo_rerouter.py](https://github.com/XronTrix10/flight-optimiser/blob/main/services/optimization/ppo_rerouter.py)  
– [weather_service.py](https://github.com/XronTrix10/flight-optimiser/blob/main/services/weather_service.py)  

──────────────────────────────────────────────────────────────────
### 2. CORE DATA-MODELS & GEO-MATH
──────────────────────────────────────────────────────────────────

Airport, Waypoint and Route each expose Haversine-based helpers:

Distance  
 R = 6 371 km  
 Δφ = φ₂-φ₁, Δλ = λ₂-λ₁  
 a = sin²(Δφ/2)+cosφ₁·cosφ₂·sin²(Δλ/2)  
 d = 2R·atan2(√a,√(1-a))

Bearing (initial azimuth)  
 θ = atan2( sinΔλ·cosφ₂ , cosφ₁·sinφ₂ – sinφ₁·cosφ₂·cosΔλ ) (°0–360)

Both implemented in [waypoint.py](https://github.com/XronTrix10/flight-optimiser/blob/main/models/waypoint.py) and reused by aircraft-wind logic.

──────────────────────────────────────────────────────────────────
### 3. WEATHER PIPELINE
──────────────────────────────────────────────────────────────────

WeatherService hits the Open-Meteo “aviation bundle” once per node
(origin, every waypointᵢ, destination) and file-caches by rounded
lat/lon.  Key properties extracted:

• Surface:  temperature_2m, visibility, wind_speed_10m, wind_direction_10m, precipitation, rain, showers, snowfall, cloud_cover  
• Jet-stream / cruise: windspeed_250hPa, winddirection_250hPa, vertical_velocity_250hPa, geopotential_height_250hPa  
• Mid/low layers: temperature_500hPa & 700hPa, relative humidity, CAPE, cloud_cover_low/mid/high  

All values arrive as plain floats in `route.weather_data[“waypoint_i”]`.

──────────────────────────────────────────────────────────────────
### 4. ROUTE FITNESS FUNCTION  (see [route.py](https://github.com/XronTrix10/flight-optimiser/blob/main/models/route.py))
──────────────────────────────────────────────────────────────────

Overall score ↓ is better.  Constituents:

a) Distance & Time  
 distance_km computed once.  
 Heading ≈ atan2(Δlon, Δlat).  
 Ground-speed for each node  
  V₍g₎ = V_air + V_jet·cos(heading – jet_dir)  
  average over nodes ⇒ flight_time = d / ⟨V₍g₎⟩

b) Fuel Consumption  
 base_fuel = rate_kg·flight_time  
 headwind/tailwind tweaks per segment  
  Δf = ±2 %·wind_speed_10m·cos(wind-track) (headwind positive)  
 Fuel penalty if fuel_needed > tank_capacity.

c) Safety / Weather Penalties  
 turbulence: |vertical_velocity_250hPa| > 0.5 m/s → +2 per hit  
 thunderstorm: CAPE>1000 or cloud_cover_high>80 % → +3 per hit  
 low visibility (<5 km) → +1  
 high cloud cover (>80 %) → +0.5  
 runway contaminants (precipitation>10 mm, etc.) → +0.75 each end  
 cross-wind (>20 kt component) → +0.5 each end  
 severe METAR codes (>50) → +0.3 each end

d) Weighted merge  
 fitness = 0.6·safety_score + 0.4·fuel_norm + fuel_capacity_penalty  
 additional term if route >5 000 km.

All penalties are dimension-less and tuned so typical fitness ∈ [2,8].

──────────────────────────────────────────────────────────────────
### 5. ANT COLONY OPTIMISATION  ([aco_optimizer.py](https://github.com/XronTrix10/flight-optimiser/blob/main/services/optimization/aco_optimizer.py))
──────────────────────────────────────────────────────────────────

• Pheromone table τ(route_id) initialised to 1.0  
• For each iteration (≈10):  
 – For each ant (≈10) pick a route with probability  

  P(r) = [τ(r)]^α · [1/fitness(r)]^β (α=1, β=2)  

 – Evaluate fitness; store best.  
• Evaporation: τ ← (1–ρ)·τ (ρ=0.5)  
• Deposit: τ(r) += 1/fitness(r) for each visited r  
• After iterations, route with global best fitness returned.

Notes  
– Deterministic fitness means ants effectively sample the
probability distribution shaped by τ and heuristic.  
– Complexity O(ants·iterations·|routes|).

──────────────────────────────────────────────────────────────────
### 6. PPO-BASED REROUTER  ([ppo_rerouter.py](https://github.com/XronTrix10/flight-optimiser/blob/main/services/optimization/ppo_rerouter.py))
──────────────────────────────────────────────────────────────────

Goal: mid-flight avoidance of a blocked waypoint.

6.1  Gathering Alternatives  
• RouteGenerator pre-created “left/right/north/south/wide” variants.  
• Any time reroute is invoked we prune alternatives whose `path_type`
already used in `current_route.reroute_history`.

6.2  Target Selection  
For every candidate route:  
 d = min distance from current_position to any waypointᵢ_alt  
Pick route with smallest d (closest join point).

6.3  Path Splicing (`_create_rerouted_path`)  
 new_waypoints = current_route[≤current_position] ⊕ alt_route[join: ]  
 All downstream waypoint names are renumbered (WPn_type) and IDs
re-UUIDed to avoid duplication.  

6.4  Scoring with Fuel & Weather (evaluate_alternatives)  
Optionally (flag `consider_fuel`): call WeatherService then
`calculate_fuel_consumption()` (same equations as §4) and add:

 score = fitness + 0.2·fuel_kg + 0.1·weather_risk  

where `weather_risk` counts vertical-velocity, visibility, cloud.

6.5  Output  
• `rerouted_route` keeps `.reroute_history` = [(blocked_name, alt_type), …]  
• `path_type` e.g. “rerouted_north”.  
• Distance & fitness recalculated.

──────────────────────────────────────────────────────────────────
### 7. END-TO-END FLOW
──────────────────────────────────────────────────────────────────

1.  `/routes/generate`  
 RouteGenerator→ 20 waypoints/route → WeatherService → fitness  
 ACO (default) picks best → JSON back to client.

2.  `/routes/optimize`  
 Client may resubmit subset; OptimizerFactory chooses ACO | GA.

3.  In-flight monitoring  
 If external hazard closes WP_k → `/routes/reroute`  
 PPORerouter splices & returns safe path; repeats if further blocks.

Caching  
• Route JSON cached by (origin,destination,route_types,aircraft,exclusions)  
• Weather per 0.0001° lat/lon JSON.

──────────────────────────────────────────────────────────────────
### 8. KEY EQUATIONS QUICK REFERENCE
──────────────────────────────────────────────────────────────────

Great-circle distance d = 2R·asin(√a) with a as above  
Bearing θ = atan2(y,x)  
Head/Tail component V_ht = V_wind·cos(Δψ)  
Ground speed V_g = V_air + V_ht  
Flight time t = d / ⟨V_g⟩  
Fuel m_fuel = t · ṁ (± wind factors)  
Fitness F = 0.6·S + 0.4·(m_fuel/10 000) + penalties  

──────────────────────────────────────────

The system therefore fuses deterministic physics (great-circle,
fuel burn) with stochastic search (ACO / GA) and reinforcement
concepts (PPO-style scoring for live reroutes) while continuously
folding in high-resolution meteorological data.  Every optimisation
stage—static or dynamic—ultimately relies on the uniform fitness
function, ensuring consistency between strategic planning and
tactical avoidance.