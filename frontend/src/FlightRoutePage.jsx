import { useFlightData } from "./hooks/useFlightData";
import AirportSelector from "./components/AirportSelector";
import AircraftSelector from "./components/AircraftSelector";
import FlightMap from "./components/FlightMap";
import RouteDetails from "./components/RouteDetails";
import FlightSimulation from "./components/FlightSimulation";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";

export default function FlightRoutePage() {
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
  } = useFlightData();

  // Find the CCU airport object from airports list
  const ccuAirport = airports.find((airport) => airport.iata_code === "CCU");

  const handleBlockWaypoint = (waypointId) => {
    if (simulationActive) {
      stopSimulation();
    }
    blockWaypoint(waypointId);
  };

  return (
    <div className="min-h-screen container mx-auto py-8 px-4">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Flight Route Optimizer</h1>
        <p className="text-gray-600">
          Plan, visualize, and optimize flight routes between airports
        </p>
      </header>

      {error && (
        <Alert variant="destructive" className="mb-6">
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
              <div className="bg-white rounded-lg shadow-md p-4 mb-4">
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
                />
              </div>
            </div>

            {/* Only show the right panel when there's an optimized route */}
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

          {optimizedRoute &&
            optimizedRoute.reroute_history &&
            optimizedRoute.reroute_history.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-8">
                <h3 className="text-lg font-medium text-amber-800 mb-2">
                  Reroute History
                </h3>
                <ul className="space-y-1">
                  {optimizedRoute.reroute_history.map((reroute, index) => (
                    <li key={index} className="text-amber-700">
                      Blocked waypoint <strong>{reroute[0]}</strong> and
                      rerouted via <strong>{reroute[1]}</strong> path
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
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <h3 className="text-lg font-medium text-blue-800 mb-2">
              Get Started
            </h3>
            <p className="text-blue-600 mb-4">
              Select a source airport, destination airport, and aircraft type to
              generate optimized flight routes.
            </p>
          </div>
        )}

      <footer className="mt-12 text-center text-gray-500 text-sm">
        <p>Flight Route Optimizer &copy; {new Date().getFullYear()}</p>
        <p className="mt-1">Using ACO, GA, and PPO optimization algorithms</p>
      </footer>
    </div>
  );
}