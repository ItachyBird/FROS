import React from "react";
import { useFlightData } from "./hooks/useFlightData";
import AirportSelector from "./components/AirportSelector";
import AircraftSelector from "./components/AircraftSelector";
import FlightMap from "./components/FlightMap";
import RouteDetails from "./components/RouteDetails";
import FlightSimulation from "./components/FlightSimulation";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";

const Flightmainpage = () => {
  const {
    airports,
    destinationAirports,
    aircraft,
    loading,
    loadingDestinations,
    error,
    sourceAirport,
    setSourceAirport,
    destinationAirport,
    setDestinationAirport,
    selectedAircraft,
    setSelectedAircraft,
    optimizedRoute,
    simulationActive,
    simulationPosition,
    setSimulationPosition,
    isRerouting,
    startSimulation,
    stopSimulation,
    blockWaypoint,
    generateFlightRoutes,
    ccuRoutes,
    allRoutes,
  } = useFlightData();

  const ccuAirport = airports.find((airport) => airport.iata_code === "CCU");

  const handleBlockWaypoint = (waypointId) => {
    if (simulationActive) {
      stopSimulation();
    }
    blockWaypoint(waypointId);
  };

  return (
    <div className="min-h-screen container mx-auto py-8 px-4" style={{ backgroundColor: "#28292a", color: "#c9c7ba" }}>
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Flight Route Optimizer</h1>
        <p className="text-gray-400">
          Plan, visualize, and optimize flight routes between airports
        </p>
      </header>

      {error && (
        <Alert variant="destructive" className="mb-6" style={{ backgroundColor: "#1f1f21", color: "#c9c7ba" }}>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <AirportSelector
          airports={airports}
          label="Source"
          value={sourceAirport}
          onChange={setSourceAirport}
          disabled={loading}
          loading={loading}
        />

        <AirportSelector
          airports={destinationAirports}
          label="Destination"
          value={destinationAirport}
          onChange={setDestinationAirport}
          disabled={loading || !sourceAirport}
          loading={loadingDestinations}
        />

        <AircraftSelector
          aircraft={aircraft}
          value={selectedAircraft}
          onChange={setSelectedAircraft}
          disabled={loading || !sourceAirport || !destinationAirport}
        />
      </div>

      {(loading || loadingDestinations) && (
        <div className="flex justify-center items-center h-40">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-lg">Loading flight data...</span>
        </div>
      )}

      {!loading && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2">
              <div className="rounded-lg shadow-md p-4 mb-4" style={{ backgroundColor: "#1f1f21" }}>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold">Flight Route Map</h2>
                  {optimizedRoute && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={generateFlightRoutes}
                      disabled={isRerouting}
                    >
                      <RefreshCw className="h-4 w-4 mr-1" />
                      Regenerate Routes
                    </Button>
                  )}
                </div>

                <FlightMap
                  sourceAirport={sourceAirport}
                  destinationAirport={destinationAirport}
                  optimizedRoute={optimizedRoute}
                  simulationActive={simulationActive}
                  simulationPosition={simulationPosition}
                  onWaypointClick={handleBlockWaypoint}
                  ccuRoutes={ccuRoutes}
                  ccuAirport={ccuAirport}
                  alternateRoutes={
                    allRoutes && optimizedRoute
                      ? allRoutes.filter((route) => route.id !== optimizedRoute.id)
                      : []
                  }
                />
              </div>
            </div>

            {optimizedRoute && (
              <div className="space-y-6">
                <RouteDetails route={optimizedRoute} />
                <FlightSimulation
                  route={optimizedRoute}
                  active={simulationActive}
                  position={simulationPosition}
                  setPosition={setSimulationPosition}
                  onStart={startSimulation}
                  onStop={stopSimulation}
                  onBlockWaypoint={handleBlockWaypoint}
                  isRerouting={isRerouting}
                />
              </div>
            )}
          </div>

          {optimizedRoute?.reroute_history?.length > 0 && (
            <div className="rounded-lg p-4 mb-8" style={{ backgroundColor: "#1f1f21", borderColor: "#c9c7ba", borderWidth: 1 }}>
              <h3 className="text-lg font-medium mb-2">Reroute History</h3>
              <ul className="space-y-1">
                {optimizedRoute.reroute_history.map((reroute, index) => (
                  <li key={index}>
                    Blocked waypoint <strong>{reroute[0]}</strong> and rerouted
                    via <strong>{reroute[1]}</strong> path
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {!loading &&
        !loadingDestinations &&
        (!sourceAirport || !destinationAirport || !selectedAircraft) && (
          <div className="rounded-lg p-6 text-center" style={{ backgroundColor: "#1f1f21", borderColor: "#c9c7ba", borderWidth: 1 }}>
            <h3 className="text-lg font-medium mb-2">Get Started</h3>
            <p className="mb-4">
              Select a source airport, destination airport, and aircraft type to
              generate optimized flight routes.
            </p>
          </div>
        )}

      <footer className="mt-12 text-center text-sm" style={{ color: "#c9c7ba" }}>
        <p>Flight Route Optimizer &copy; {new Date().getFullYear()}</p>
        <p className="mt-1">Using ACO, GA, and PPO optimization algorithms</p>
      </footer>
    </div>
  );
};

export default Flightmainpage;
