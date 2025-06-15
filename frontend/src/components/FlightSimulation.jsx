// src/components/FlightSimulation.jsx
import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Slider } from "@/components/ui/slider";
import { Play, Pause, RotateCcw, AlertTriangle, Clock } from "lucide-react";

export default function FlightSimulation({
  route,
  active,
  position,
  setPosition,
  onStart,
  onStop,
  onBlockWaypoint,
  isRerouting,
}) {
  // Slower default speed (0.5x instead of 1x)
  const [speed, setSpeed] = useState(0.5);
  const [selectedWaypoint, setSelectedWaypoint] = useState(null);
  const intervalRef = useRef(null);

  // Store the last position before pausing or rerouting
  const lastPositionRef = useRef(position);

  // Manage simulation timer with smoother movement
  useEffect(() => {
    if (active && route) {
      const updateInterval = 100; // Update every 100ms for smoother movement
      intervalRef.current = setInterval(() => {
        setPosition((prevPos) => {
          // Using smaller increments for smoother movement
          // The increment size depends on the speed
          const increment = 0.1 * speed;
          const newPos = prevPos + increment;

          if (newPos >= route.waypoints.length - 1) {
            onStop();
            return route.waypoints.length - 1; // Stay at last waypoint
          }
          return newPos;
        });
      }, updateInterval);
    } else if (intervalRef.current) {
      // When stopping, store the current position
      lastPositionRef.current = position;
      clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [active, route, speed, setPosition, onStop, position]);

  // Only reset position when a new route is set (not on reroute)
  useEffect(() => {
    // Check if this is a completely new route (e.g., new origin/destination)
    // rather than a reroute of an existing path
    const isNewRoute =
      !route?.reroute_history || route.reroute_history.length === 0;

    if (isNewRoute) {
      setPosition(0);
      lastPositionRef.current = 0;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [route?.id, setPosition]);

  // When rerouting completes, restore the last position
  useEffect(() => {
    if (!isRerouting && route && lastPositionRef.current > 0) {
      // Find the corresponding waypoint in the new route
      const currentWaypointIndex = Math.min(
        Math.floor(lastPositionRef.current),
        route.waypoints.length - 2 // Make sure we don't exceed bounds
      );
      const progress =
        lastPositionRef.current - Math.floor(lastPositionRef.current);

      // Set position to the corresponding point in the new route
      const newPosition = currentWaypointIndex + progress;
      setPosition(Math.min(newPosition, route.waypoints.length - 1));
    }
  }, [isRerouting, route, setPosition]);

  if (!route) return null;

  // Calculate the current waypoint (integer part of position)
  const currentWaypointIndex = Math.floor(position);
  const progress = position - currentWaypointIndex; // Fractional part for progress

  const handleWaypointBlock = () => {
    if (!selectedWaypoint) return;

    // Store current position before blocking
    lastPositionRef.current = position;

    // Find next waypoint that hasn't been passed yet
    const nextWaypointIndex = route.waypoints.findIndex(
      (wp, idx) => idx > currentWaypointIndex && wp.id === selectedWaypoint
    );
    if (nextWaypointIndex !== -1) {
      onBlockWaypoint(selectedWaypoint);
    }
  };

  // Modified start/stop handlers to use the lastPositionRef
  const handleStart = () => {
    onStart();
  };

  const handleStop = () => {
    onStop();
  };

  const handleReset = () => {
    lastPositionRef.current = 0;
    setPosition(0);
  };

  return (
<div className="space-y-4 p-4 border border-[#c9c7ba] rounded-lg shadow-sm dark:border-[#c9c7ba]">
  <div className="flex items-center justify-between">
    <h3 className="text-lg font-medium text-[#c9c7ba]">
      Flight Simulation
    </h3>
    <div className="flex items-center space-x-2">
      <Clock className="w-4 h-4 text-[#c9c7ba]" />
      <span className="text-sm text-[#c9c7ba]">
        Est. Time: {route.estimated_time.hours}h{" "}
        {route.estimated_time.minutes}m
      </span>
    </div>
  </div>

  <div className="flex items-center space-x-2">
    <Button
      variant={active ? "outline" : "default"}
      size="sm"
      onClick={active ? handleStop : handleStart}
      disabled={isRerouting}
    >
      {active ? (
        <Pause className="w-4 h-4 mr-1" />
      ) : (
        <Play className="w-4 h-4 mr-1" />
      )}
      {active ? "Pause" : "Start"}
    </Button>

    <Button
      variant="outline"
      size="sm"
      onClick={handleReset}
      disabled={active || isRerouting}
    >
      <RotateCcw className="w-4 h-4 mr-1" />
      Reset
    </Button>

    <div className="flex items-center space-x-2 ml-4">
      <span className="text-sm text-[#c9c7ba]">Speed:</span>
      <Slider
        min={0.1}
        max={2}
        step={0.1}
        value={[speed]}
        onValueChange={(value) => setSpeed(value[0])}
        disabled={isRerouting}
        className="w-32"
      />
      <span className="text-sm font-medium text-[#c9c7ba]">
        {speed.toFixed(1)}x
      </span>
    </div>
  </div>

  <div className="space-y-2">
    <div className="flex items-center justify-between">
      <h4 className="text-sm font-medium text-[#c9c7ba]">
        Progress
      </h4>
      <span className="text-xs text-[#c9c7ba]">
        Waypoint {currentWaypointIndex + 1}
        {progress > 0 ? ` → ${currentWaypointIndex + 2}` : ""} of{" "}
        {route.waypoints.length}
      </span>
    </div>
    <Slider
      min={0}
      max={route.waypoints.length - 1}
      step={0.01}
      value={[position]}
      onValueChange={(value) => {
        if (!active) {
          setPosition(value[0]);
          lastPositionRef.current = value[0];
        }
      }}
      disabled={active || isRerouting}
      className="w-full"
    />
  </div>

  <div className="pt-2 border-t border-[#c9c7ba]">
    <h4 className="text-sm font-medium mb-2 text-[#c9c7ba]">
      Waypoint Control
    </h4>
    <div className="flex items-center space-x-2">
           <select
        className="border border-[#c9c7ba] rounded p-1 text-sm flex-1 dark:border-[#c9c7ba] text-[#c9c7ba] dark:text-[#c9c7ba] bg-[#23231d] dark:bg-[#23231d] focus:outline-none focus:ring-2 focus:ring-[#c9c7ba] appearance-none"
        style={{
          backgroundColor: "#23231d",
          color: "#c9c7ba",
          borderColor: "#c9c7ba",
          // --- Hide scroll bar cross-browser ---
          scrollbarWidth: "none",        // Firefox
          msOverflowStyle: "none",       // IE 10+
          overflow: "auto",
        }}
        value={selectedWaypoint || ""}
        onChange={(e) => setSelectedWaypoint(e.target.value)}
        disabled={isRerouting}
        // --- Hide scroll bar for Webkit browsers (Chrome, Safari) ---
        // This is a trick: add a global CSS style below in your app (see note)
      >
        <option value="">Select waypoint to block</option>
        {route.waypoints.map((waypoint, idx) => (
          <option
            key={waypoint.id}
            value={waypoint.id}
            disabled={idx <= currentWaypointIndex}
            style={{
              backgroundColor: "#23231d",
              color: "#c9c7ba"
            }}
          >
            {waypoint.name} {idx <= currentWaypointIndex ? "(passed)" : ""}
          </option>
        ))}
      </select>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleWaypointBlock}
              disabled={!selectedWaypoint || isRerouting}
            >
              <AlertTriangle className="w-4 h-4 mr-1" />
              Block
            </Button>
          </TooltipTrigger>
          <TooltipContent className="text-sm text-[#c9c7ba] border border-[#c9c7ba]">
            <p>Simulate blocking this waypoint, forcing reroute</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>

    {isRerouting && (
      <div className="mt-2 text-amber-600 text-sm flex items-center">
        <AlertTriangle className="w-4 h-4 mr-1" />
        Rerouting in progress...
      </div>
    )}
  </div>
</div>
  );
}



