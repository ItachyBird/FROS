import { useGLTF } from "@react-three/drei";
import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { useScroll } from "@react-three/drei";
import * as THREE from "three";

export default function Scene() {
  const ref = useRef();
  const scroll = useScroll();
  const { nodes } = useGLTF("/aircraft.glb");

  // Glossy dark material with color #424243
  const glossyMaterial = useMemo(() => {
    return new THREE.MeshPhysicalMaterial({
      color: "#424243",
      metalness: 1,
      roughness: 0.2,
      clearcoat: 1,
      clearcoatRoughness: 0.05,
    });
  }, []);

  const views = [
    {
      position: [0, -0.2, 2],
      rotation: [-Math.PI / 1.7, 0, 0],
      scale: 5,
    },
    {
      position: [3, 0.1, 1],
      rotation: [-Math.PI / 1.7, 0, -1],
      scale: 7,
    },
    {
      position: [-2.5, 1, -1],
      rotation: [0, 0, -Math.PI / 2],
      scale: 7,
    },
    {
      position: [-2.5, 1, -1],
      rotation: [0, 0, -Math.PI / 2],
      scale: 7,
    },
    {
      position: [4, 2, -1],
      rotation: [-1.5, 0, -Math.PI / -0.8],
      scale: 40,
    },
    {
      position: [4, 2, -1],
      rotation: [-1.5, 0, -Math.PI / -0.8],
      scale: 40,
    },
    {
      position: [0, 0, 0],
      rotation: [-Math.PI / 2, 0, 0],
      scale: 5,
    },
  ];

  useFrame(() => {
    const scrollY = scroll.offset;
    const sectionCount = views.length;
    const sectionIndex = Math.min(
      sectionCount - 1,
      Math.floor(scrollY * sectionCount)
    );
    const target = views[sectionIndex];

    if (ref.current && target) {
      ref.current.position.lerp(new THREE.Vector3(...target.position), 0.05);
      ref.current.rotation.x = THREE.MathUtils.lerp(
        ref.current.rotation.x,
        target.rotation[0],
        0.05
      );
      ref.current.rotation.y = THREE.MathUtils.lerp(
        ref.current.rotation.y,
        target.rotation[1],
        0.05
      );
      ref.current.rotation.z = THREE.MathUtils.lerp(
        ref.current.rotation.z,
        target.rotation[2],
        0.05
      );
      const currentScale = ref.current.scale.x;
      const targetScale = target.scale;
      const newScale = THREE.MathUtils.lerp(currentScale, targetScale, 0.05);
      ref.current.scale.set(newScale, newScale, newScale);
    }
  });

  return (
    <group ref={ref} dispose={null}>
      <group rotation={[Math.PI / 2, 0, 0]}>
        <group position={[0.004, -0.05, 0.234]} scale={0.002}>
          <mesh
            castShadow
            receiveShadow
            geometry={nodes.Object_7.geometry}
            material={glossyMaterial}
            position={[0.007, 14.932, 18.934]}
          />
        </group>
      </group>
    </group>
  );
}

useGLTF.preload("/aircraft.glb");
