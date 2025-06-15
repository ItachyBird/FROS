// src/components/RouteDetails.jsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function RouteDetails({ route }) {
  if (!route) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Route Details</span>
          <Badge variant="outline" className="text-[#c9c7ba] border-[#c9c7ba]">
  {route.path_type}
</Badge>

        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <p className="text-sm text-gray-500">Distance</p>
            <p className="font-medium">{route.distance_km.toFixed(2)} km</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Estimated Time</p>
            <p className="font-medium">
              {route.estimated_time.hours}h {route.estimated_time.minutes}m
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Fuel Consumption</p>
            <p className="font-medium">{route.fuel_consumption.toFixed(2)} L</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Optimization Method</p>
            <p className="font-medium">
              {route.optimization_method.toUpperCase()}
            </p>
          </div>
        </div>

<div>
  <p className="text-sm text-gray-500 mb-1">Waypoints</p>
  <div className="max-h-32 overflow-y-auto scrollbar-hide">
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b">
          <th className="py-1 text-left">Name</th>
          <th className="py-1 text-left">Latitude</th>
          <th className="py-1 text-left">Longitude</th>
        </tr>
      </thead>
      <tbody>
        {route.waypoints.map((waypoint) => (
          <tr key={waypoint.id} className="border-b border-gray-100">
            <td className="py-1">{waypoint.name}</td>
            <td className="py-1">{waypoint.latitude.toFixed(4)}</td>
            <td className="py-1">{waypoint.longitude.toFixed(4)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
</div>

      </CardContent>
    </Card>
  );
}
