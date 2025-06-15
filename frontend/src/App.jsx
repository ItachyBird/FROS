import { Routes, Route } from "react-router-dom";
import LandingPage from "./components/LandingPage";
import FlightMainPage from "./FlightMainPage";
import './App.css';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/flightmainpage" element={<FlightMainPage />} />
    </Routes>
  );
}