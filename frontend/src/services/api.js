// src/services/api.js
const API_BASE_URL = "http://localhost:8000";

export const fetchAirports = async (countryCode = "IN") => {
  const response = await fetch(
    `${API_BASE_URL}/api/airports?country_code=${countryCode}`
  );
  if (!response.ok) throw new Error("Failed to fetch airports");
  return response.json();
};

export const fetchAirportDetails = async (iataCode) => {
  const response = await fetch(`${API_BASE_URL}/api/airports/${iataCode}`);
  if (!response.ok)
    throw new Error(`Failed to fetch airport details for ${iataCode}`);
  return response.json();
};

export const fetchAirportDestinations = async (iataCode) => {
  const response = await fetch(
    `${API_BASE_URL}/api/airports/${iataCode}/destinations`
  );
  if (!response.ok)
    throw new Error(`Failed to fetch destinations for ${iataCode}`);
  return response.json();
};

export const fetchAircraft = async () => {
  const response = await fetch(`${API_BASE_URL}/api/aircraft`);
  if (!response.ok) throw new Error("Failed to fetch aircraft models");
  return response.json();
};

export const generateRoutes = async (params) => {
  const response = await fetch(`${API_BASE_URL}/api/routes/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!response.ok) throw new Error("Failed to generate routes");
  return response.json();
};

export const rerouteFlightPath = async (rerouteData) => {
  const response = await fetch(`${API_BASE_URL}/api/routes/reroute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rerouteData),
  });
  if (!response.ok) throw new Error("Failed to reroute flight path");
  return response.json();
};

export const fetchCCURoutes = async () => {
  const response = await fetch(`${API_BASE_URL}/api/routes/ccu-routes`);
  if (!response.ok) throw new Error("Failed to fetch CCU routes");
  return response.json();
};
