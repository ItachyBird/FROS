import { useEffect, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  Tooltip,
  useMap,
  ScaleControl,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import "leaflet-rotatedmarker";

// COLOR PALETTE
const COLORS = {
  background: "#28292a",
  card: "#1f1f21",
  icon: "#c0beb1",
  line: "#c0beb1",
  waypoint: "#c0beb1",
  route: "#c0beb1",
  alternate: "#525252",
  label: "#c0beb1",
  popupBg: "#1f1f21",
  popupText: "#c0beb1",
  tooltipBg: "rgba(17, 17, 18, 0.55)", // semi-transparent black for blur effect
  tooltipText: "#c9c7ba",
  tooltipBorder: "#c9c7ba",
  tooltipShadow: "#11111244",
  shadow: "#111112",
  airportPin: "#c9c7ba",
};

// Add global CSS for blur and transparent background on Tooltip
if (typeof document !== "undefined" && !document.getElementById("custom-leaflet-tooltip-style")) {
  const style = document.createElement("style");
  style.id = "custom-leaflet-tooltip-style";
  style.innerHTML = `
    .leaflet-tooltip.custom-tooltip {
      background: ${COLORS.tooltipBg} !important;
      color: ${COLORS.tooltipText} !important;
      border: 2px solid ${COLORS.tooltipBorder} !important;
      font-weight: 600 !important;
      border-radius: 8px !important;
      font-size: 14px !important;
      padding: 2px 10px !important;
      box-shadow: 0 2px 8px 0 ${COLORS.tooltipShadow} !important;
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      transition: background 0.2s, color 0.2s;
      opacity: 1 !important;
    }
    .leaflet-tooltip.custom-tooltip.show {
      background: ${COLORS.tooltipBg} !important;
      color: ${COLORS.tooltipText} !important;
    }
  `;
  document.head.appendChild(style);
}

// Fix for default marker icons in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
});

// Custom airport marker (fa-map-pin, small, #c9c7ba)
const airportPinSVG = encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 384 512" fill="${COLORS.airportPin}">
  <path d="M192 0C86 0 0 86.1 0 192c0 77.7 99.3 220.3 146.7 287.5 9.6 13.4 28 13.4 37.6 0C284.7 412.3 384 269.7 384 192 384 86.1 298 0 192 0zm0 272c-44.2 0-80-35.8-80-80s35.8-80 80-80 80 35.8 80 80-35.8 80-80 80z"/>
</svg>
`);
const airportPinIcon = new L.Icon({
  iconUrl: `data:image/svg+xml,${airportPinSVG}`,
  iconSize: [18, 18],
  iconAnchor: [9, 18],
  popupAnchor: [0, -16],
  className: "fa-map-pin-airport-marker",
});

// Custom marker icon (tinted with #c0beb1)
const markerIcon = new L.Icon({
  iconUrl:
    "https://api.iconify.design/mdi:map-marker.svg?color=%23c0beb1",
  iconSize: [32, 38],
  iconAnchor: [16, 38],
  popupAnchor: [0, -30],
  shadowUrl: "",
  className: "custom-leaflet-marker",
});

// FontAwesome plane icon (small, blue)
const planeMarkerSVG = encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 576 512" fill="#2196f3">
  <path d="M480 192H365.71l-83.19-128H320a16 16 0 0 0 0-32h-64a16 16 0 0 0 0 32h37.48l-83.19 128H96a32 32 0 0 0-32 32v48a32 32 0 0 0 32 32h69.29l83.19 128H256a16 16 0 0 0 0 32h64a16 16 0 0 0 0-32h-37.48l83.19-128H480a32 32 0 0 0 32-32v-48a32 32 0 0 0-32-32z"/>
</svg>
`);
const planeIcon = new L.Icon({
  iconUrl: `data:image/svg+xml,${planeMarkerSVG}`,
  iconSize: [22, 22], // A bit smaller
  iconAnchor: [11, 11],
  className: "fa-plane-marker",
});

// Custom FA circle-dot icon for waypoints (main route)
const faCircleDotSVG = encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 512 512" fill="${COLORS.waypoint}">
  <circle cx="256" cy="256" r="192" fill="${COLORS.waypoint}" opacity="0.16"/>
  <circle cx="256" cy="256" r="80" fill="${COLORS.waypoint}"/>
  <circle cx="256" cy="256" r="120" fill="none" stroke="${COLORS.waypoint}" stroke-width="24" opacity="0.6"/>
</svg>
`);
const faCircleDotIcon = new L.Icon({
  iconUrl: `data:image/svg+xml,${faCircleDotSVG}`,
  iconSize: [26, 26],
  iconAnchor: [13, 13],
  popupAnchor: [0, -13],
  className: "fa-circle-dot-waypoint-marker",
});

// Small dot icon for alternate route waypoints
const smallAltDotSVG = encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="${COLORS.alternate}">
  <circle cx="12" cy="12" r="6" fill="${COLORS.alternate}" />
</svg>
`);
const smallAltDotIcon = new L.Icon({
  iconUrl: `data:image/svg+xml,${smallAltDotSVG}`,
  iconSize: [12, 12],
  iconAnchor: [6, 6],
  className: "small-alt-dot-waypoint-marker",
});

function PlaneMarker({ route, position, simulationActive }) {
  const map = useMap();
  const markerRef = useRef(null);

  useEffect(() => {
    if (!route || !simulationActive || position === undefined) return;

    // Get the current waypoint position
    const waypoints = route.waypoints;

    // Get the integer and fractional parts of the position
    const currentIndex = Math.floor(position);
    const progress = position - currentIndex;

    // If we're at the last waypoint, just use its position
    if (currentIndex >= waypoints.length - 1) {
      const lastWaypoint = waypoints[waypoints.length - 1];
      if (markerRef.current) {
        markerRef.current.setLatLng([
          lastWaypoint.latitude,
          lastWaypoint.longitude,
        ]);
        markerRef.current.setRotationAngle(0);
      }
      return;
    }

    // Get current and next waypoints
    const currentWp = waypoints[currentIndex];
    const nextWp = waypoints[currentIndex + 1];

    // Interpolate between waypoints
    const lat =
      currentWp.latitude + (nextWp.latitude - currentWp.latitude) * progress;
    const lng =
      currentWp.longitude + (nextWp.longitude - currentWp.longitude) * progress;

    if (markerRef.current) {
      markerRef.current.setLatLng([lat, lng]);
      // Calculate bearing for plane rotation
      const bearing = calculateBearing(
        currentWp.latitude,
        currentWp.longitude,
        nextWp.latitude,
        nextWp.longitude
      );
      markerRef.current.setRotationAngle(bearing);
    }
  }, [route, position, simulationActive, map]);

  if (!route || !simulationActive) return null;

  // Start at the first waypoint
  const initialWaypoint = route.waypoints[0];

  return (
    <Marker
      position={[initialWaypoint.latitude, initialWaypoint.longitude]}
      icon={planeIcon}
      rotationAngle={0}
      rotationOrigin="center"
      ref={markerRef}
    />
  );
}

// Calculate bearing between two points
function calculateBearing(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => (deg * Math.PI) / 180;
  const toDeg = (rad) => (rad * 180) / Math.PI;

  const dLon = toRad(lon2 - lon1);
  const lat1Rad = toRad(lat1);
  const lat2Rad = toRad(lat2);

  const y = Math.sin(dLon) * Math.cos(lat2Rad);
  const x =
    Math.cos(lat1Rad) * Math.sin(lat2Rad) -
    Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);

  let bearing = toDeg(Math.atan2(y, x));
  bearing = (bearing + 360) % 360;

  return bearing;
}

// Helper to show all direct routes from every airport (not just CCU)
function AllDirectRoutesDisplay({ airports = [], directRoutes = [] }) {
  return (
    <>
      {/* Mark all airports */}
      {airports.map((airport) => (
        <Marker
          key={airport.id}
          position={[airport.latitude, airport.longitude]}
          icon={airportPinIcon}
        >
          <Popup>
            <div
              style={{
                background: COLORS.popupBg,
                color: COLORS.popupText,
                borderRadius: 8,
                padding: 4,
                fontWeight: 500,
              }}
            >
              <strong>{airport.name}</strong>
              <br />
              {airport.city}, {airport.country}
            </div>
          </Popup>
        </Marker>
      ))}
      {/* Draw all direct routes */}
      {directRoutes.map((route, idx) => (
        <Polyline
          key={`direct-route-${idx}`}
          positions={[
            [route.source.latitude, route.source.longitude],
            [route.destination.latitude, route.destination.longitude],
          ]}
          color={COLORS.line}
          weight={2}
          opacity={0.7}
          dashArray="8, 8"
        />
      ))}
    </>
  );
}

// Fit bounds to all airports and all direct routes
function FitAllBounds({ airports = [], directRoutes = [], alternateRoutes = [], source, destination }) {
  const map = useMap();
  useEffect(() => {
    let points = [];
    // All airports
    airports.forEach((airport) =>
      points.push([airport.latitude, airport.longitude])
    );
    // All direct routes
    directRoutes.forEach((route) => {
      points.push([route.source.latitude, route.source.longitude]);
      points.push([route.destination.latitude, route.destination.longitude]);
    });
    // Alternates
    alternateRoutes.forEach((route) => {
      if (route.waypoints?.length) {
        points.push(...route.waypoints.map((wp) => [wp.latitude, wp.longitude]));
      }
    });
    // If optimized route present
    if (source && destination) {
      points.push([source.latitude, source.longitude]);
      points.push([destination.latitude, destination.longitude]);
    }
    if (points.length > 1) {
      map.fitBounds(points, { padding: [50, 50] });
    }
  }, [airports, directRoutes, alternateRoutes, source, destination, map]);
  return null;
}

// Custom dark tile layer (CartoDB Dark Matter)
const darkTile =
  "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const darkAttribution =
  '&copy; <a href="https://carto.com/attributions">CARTO</a> | <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

export default function FlightMap({
  sourceAirport,
  destinationAirport,
  optimizedRoute,
  simulationActive,
  simulationPosition,
  onWaypointClick,
  airports = [],
  directRoutes = [],
  alternateRoutes = [],
}) {
  // Show all direct routes from all airports if no optimized route shown
  const showAllDirect = !optimizedRoute && airports.length > 0 && directRoutes.length > 0;

  // Prepare optimized route positions
  const directRoute = optimizedRoute
    ? optimizedRoute.waypoints.map((wp) => [wp.latitude, wp.longitude])
    : [];
  const waypoints = optimizedRoute?.waypoints || [];

  // Helper to render markers for a route's waypoints
  const renderWaypoints = (
    waypointsArr,
    icon,
    prefix = "wp",
    onClickHandler = null
  ) =>
    waypointsArr.map((waypoint, index) => (
      <Marker
        key={`${prefix}-${waypoint.id || index}`}
        position={[waypoint.latitude, waypoint.longitude]}
        icon={icon}
        eventHandlers={
          onClickHandler
            ? {
                click: () => onClickHandler(waypoint.id),
              }
            : undefined
        }
      >
        <Tooltip
          direction="top"
          offset={[0, -20]}
          className="custom-tooltip"
          opacity={1}
        >
          {waypoint.name}
        </Tooltip>
        {/* Only show popup for main waypoints */}
        {icon === faCircleDotIcon && (
          <Popup>
            <div
              style={{
                background: COLORS.popupBg,
                color: COLORS.popupText,
                borderRadius: 8,
                padding: 4,
                fontWeight: 500,
              }}
            >
              <strong>
                Waypoint {index + 1}: {waypoint.name}
              </strong>
              <br />
              Latitude: {waypoint.latitude.toFixed(4)}
              <br />
              Longitude: {waypoint.longitude.toFixed(4)}
            </div>
          </Popup>
        )}
      </Marker>
    ));

  return (
    <MapContainer
      center={[20.5937, 78.9629]} // Center of India
      zoom={5}
      style={{
        height: "500px",
        width: "100%",
        background: COLORS.background,
        borderRadius: 18,
        boxShadow: `0 8px 36px 0 ${COLORS.shadow}`,
        overflow: "hidden",
      }}
      className="custom-dark-map"
    >
      <TileLayer attribution={darkAttribution} url={darkTile} />

      {/* All airports & direct routes display */}
      {showAllDirect && (
        <AllDirectRoutesDisplay airports={airports} directRoutes={directRoutes} />
      )}

      {/* Only show optimized route and its markers if present */}
      {optimizedRoute && (
        <>
          {/* Source marker */}
          {sourceAirport && (
            <Marker
              position={[sourceAirport.latitude, sourceAirport.longitude]}
              icon={markerIcon}
            >
              <Popup>
                <div
                  style={{
                    background: COLORS.popupBg,
                    color: COLORS.popupText,
                    borderRadius: 8,
                    padding: 4,
                    fontWeight: 500,
                  }}
                >
                  <strong>{sourceAirport.name}</strong>
                  <br />
                  {sourceAirport.city}, {sourceAirport.country}
                </div>
              </Popup>
            </Marker>
          )}

          {/* Destination marker */}
          {destinationAirport && (
            <Marker
              position={[destinationAirport.latitude, destinationAirport.longitude]}
              icon={markerIcon}
            >
              <Popup>
                <div
                  style={{
                    background: COLORS.popupBg,
                    color: COLORS.popupText,
                    borderRadius: 8,
                    padding: 4,
                    fontWeight: 500,
                  }}
                >
                  <strong>{destinationAirport.name}</strong>
                  <br />
                  {destinationAirport.city}, {destinationAirport.country}
                </div>
              </Popup>
            </Marker>
          )}

          {/* Optimized route */}
          {directRoute.length > 0 && (
            <Polyline
              positions={directRoute}
              color={COLORS.route}
              weight={4}
              opacity={0.9}
            />
          )}

          {/* Optimized route waypoints */}
          {renderWaypoints(
            waypoints,
            faCircleDotIcon,
            "mainwp",
            onWaypointClick
          )}

          {/* Alternate routes - muted, with small dots for waypoints */}
          {alternateRoutes.length > 0 &&
            alternateRoutes.map((route, idx) => (
              <>
                <Polyline
                  key={`alt-route-${idx}`}
                  positions={
                    route.waypoints
                      ? route.waypoints.map((wp) => [wp.latitude, wp.longitude])
                      : []
                  }
                  color={COLORS.alternate}
                  weight={2}
                  opacity={0.5}
                  dashArray="4, 10"
                />
                {/* Alternate route waypoints as small dots */}
                {route.waypoints &&
                  renderWaypoints(
                    route.waypoints,
                    smallAltDotIcon,
                    `altwp-${idx}`
                  )}
              </>
            ))}
          {/* Plane marker for simulation */}
          <PlaneMarker
            route={optimizedRoute}
            position={simulationPosition}
            simulationActive={simulationActive}
          />
        </>
      )}

      {/* Fit bounds to all airports and routes */}
      <FitAllBounds
        airports={airports}
        directRoutes={directRoutes}
        alternateRoutes={alternateRoutes}
        source={sourceAirport}
        destination={destinationAirport}
      />

      <ScaleControl position="bottomleft" />
    </MapContainer>
  );
}