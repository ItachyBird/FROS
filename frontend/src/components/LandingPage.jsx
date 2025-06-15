import { Canvas } from "@react-three/fiber";
import { ScrollControls, Scroll, Environment } from "@react-three/drei";
import Scene from "./Scene";
import Overlay from "./Overlay";
import { useNavigate } from "react-router-dom";

export default function LandingPage() {
  const navigate = useNavigate(); 

  return (
    <div className="relative w-full h-screen">
      <Canvas
        shadows
        camera={{ position: [0, 0, 5], fov: 50 }}
        style={{ position: "fixed", top: 0, left: 0, zIndex: 100, background: "#29292b" }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1.2} castShadow />
        <Environment preset="sunset" />

        <ScrollControls pages={5} damping={0.2}>
          <Scene />
          <Scroll html>
            <Overlay navigate={navigate} /> 
          </Scroll>
        </ScrollControls>
      </Canvas>
    </div>
  );
}
