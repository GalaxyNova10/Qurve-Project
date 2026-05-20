import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

// Mouse-reactive particle field with connecting lines
function ParticleField() {
  const pointsRef = useRef<THREE.Points>(null);
  const linesRef = useRef<THREE.LineSegments>(null);
  const { viewport } = useThree();

  const PARTICLE_COUNT = 1800;
  const CONNECTION_DISTANCE = 0.6;
  const MAX_CONNECTIONS = 300;

  const positions = useMemo(() => {
    const arr = new Float32Array(PARTICLE_COUNT * 3);
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const r = 1.2 + Math.random() * 3.0;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    return arr;
  }, []);

  // Velocities for gentle floating
  const velocities = useMemo(() => {
    const arr = new Float32Array(PARTICLE_COUNT * 3);
    for (let i = 0; i < PARTICLE_COUNT * 3; i++) {
      arr[i] = (Math.random() - 0.5) * 0.003;
    }
    return arr;
  }, []);

  // Pre-allocate line geometry
  const linePositions = useMemo(() => new Float32Array(MAX_CONNECTIONS * 6), []);
  const lineColors = useMemo(() => new Float32Array(MAX_CONNECTIONS * 6), []);  const ptsMaterial = useMemo(() => new THREE.PointsMaterial({
    transparent: true,
    color: new THREE.Color("#a78bfa"),
    size: 0.012,
    sizeAttenuation: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  }), []);

  const lineMaterial = useMemo(() => new THREE.LineBasicMaterial({
    transparent: true,
    opacity: 0.35,
    vertexColors: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  }), []);

  const pointsGeometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    return geo;
  }, [positions]);

  const linesGeometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(lineColors, 3));
    return geo;
  }, [linePositions, lineColors]);
  useFrame((state, delta) => {
    if (!pointsRef.current) return;
    const posAttr = pointsRef.current.geometry.attributes.position;
    const posArray = posAttr.array as Float32Array;

    // Global slow rotation
    pointsRef.current.rotation.y += delta * 0.03;
    pointsRef.current.rotation.x += delta * 0.01;

    // Mouse influence — gentle repulsion
    const mx = (state.pointer.x * viewport.width) / 2;
    const my = (state.pointer.y * viewport.height) / 2;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const i3 = i * 3;
      // Float
      posArray[i3] += velocities[i3] * delta * 30;
      posArray[i3 + 1] += velocities[i3 + 1] * delta * 30;
      posArray[i3 + 2] += velocities[i3 + 2] * delta * 30;

      // Gentle boundary — keep particles in sphere
      const r = Math.sqrt(
        posArray[i3] ** 2 + posArray[i3 + 1] ** 2 + posArray[i3 + 2] ** 2
      );
      if (r > 4.5 || r < 0.8) {
        velocities[i3] *= -1;
        velocities[i3 + 1] *= -1;
        velocities[i3 + 2] *= -1;
      }

      // Mouse repulsion
      const dx = posArray[i3] - mx;
      const dy = posArray[i3 + 1] - my;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 1.2 && dist > 0.01) {
        const force = (1.2 - dist) * 0.015;
        posArray[i3] += (dx / dist) * force;
        posArray[i3 + 1] += (dy / dist) * force;
      }
    }
    posAttr.needsUpdate = true;

    // Update connection lines
    if (linesRef.current) {
      let lineIdx = 0;
      const worldPositions: [number, number, number][] = [];

      // Get world positions (approximation — ignoring rotation for perf)
      for (let i = 0; i < PARTICLE_COUNT && lineIdx < MAX_CONNECTIONS; i++) {
        worldPositions.push([
          posArray[i * 3],
          posArray[i * 3 + 1],
          posArray[i * 3 + 2],
        ]);
      }

      // Find nearby pairs (only check subset for performance)
      const checkCount = Math.min(400, PARTICLE_COUNT);
      for (let i = 0; i < checkCount && lineIdx < MAX_CONNECTIONS; i++) {
        for (
          let j = i + 1;
          j < checkCount && lineIdx < MAX_CONNECTIONS;
          j++
        ) {
          const dx = worldPositions[i][0] - worldPositions[j][0];
          const dy = worldPositions[i][1] - worldPositions[j][1];
          const dz = worldPositions[i][2] - worldPositions[j][2];
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

          if (dist < CONNECTION_DISTANCE) {
            const opacity = 1 - dist / CONNECTION_DISTANCE;
            const idx = lineIdx * 6;
            linePositions[idx] = worldPositions[i][0];
            linePositions[idx + 1] = worldPositions[i][1];
            linePositions[idx + 2] = worldPositions[i][2];
            linePositions[idx + 3] = worldPositions[j][0];
            linePositions[idx + 4] = worldPositions[j][1];
            linePositions[idx + 5] = worldPositions[j][2];

            // Purple to cyan gradient based on opacity
            lineColors[idx] = 0.55 * opacity;
            lineColors[idx + 1] = 0.36 * opacity;
            lineColors[idx + 2] = 0.96 * opacity;
            lineColors[idx + 3] = 0.24 * opacity;
            lineColors[idx + 4] = 0.71 * opacity;
            lineColors[idx + 5] = 0.83 * opacity;
            lineIdx++;
          }
        }
      }

      // Zero out unused lines
      for (let i = lineIdx * 6; i < MAX_CONNECTIONS * 6; i++) {
        linePositions[i] = 0;
        lineColors[i] = 0;
      }

      const lGeom = linesRef.current.geometry;
      (lGeom.attributes.position as THREE.BufferAttribute).needsUpdate = true;
      (lGeom.attributes.color as THREE.BufferAttribute).needsUpdate = true;
      lGeom.setDrawRange(0, lineIdx * 2);
    }
  });

  return (
    <group>
      <points ref={pointsRef} geometry={pointsGeometry} material={ptsMaterial} />
      {/* Connection lines */}
      <lineSegments ref={linesRef} geometry={linesGeometry} material={lineMaterial} />
    </group>
  );
}

// Wireframe icosahedron sphere
function Sphere() {
  const ref = useRef<THREE.Mesh>(null);
  
  const geometry = useMemo(() => new THREE.IcosahedronGeometry(1.3, 3), []);
  const material = useMemo(() => new THREE.MeshBasicMaterial({
    color: new THREE.Color("#8b5cf6"),
    wireframe: true,
    transparent: true,
    opacity: 0.18
  }), []);

  useFrame((state, delta) => {
    if (!ref.current) return;
    ref.current.rotation.y += delta * 0.12;
    ref.current.rotation.x += delta * 0.06;
    // Subtle breathing scale
    const breath = Math.sin(state.clock.elapsedTime * 0.5) * 0.02 + 1;
    ref.current.scale.setScalar(breath);
  });
  
  return <mesh ref={ref} geometry={geometry} material={material} />;
}

// Inner energy core
function EnergyCore() {
  const ref = useRef<THREE.Mesh>(null);
  
  const geometry = useMemo(() => new THREE.SphereGeometry(1, 32, 32), []);
  const material = useMemo(() => new THREE.MeshBasicMaterial({
    color: new THREE.Color("#a78bfa"),
    transparent: true,
    opacity: 0.2,
    blending: THREE.AdditiveBlending
  }), []);

  useFrame((state) => {
    if (!ref.current) return;
    const pulse = Math.sin(state.clock.elapsedTime * 1.5) * 0.15 + 0.85;
    ref.current.scale.setScalar(pulse * 0.4);
    (ref.current.material as THREE.MeshBasicMaterial).opacity = pulse * 0.3;
  });
  
  return <mesh ref={ref} geometry={geometry} material={material} />;
}

export function QuantumScene() {
  return (
    <Canvas
      camera={{ position: [0, 0, 4.5], fov: 55 }}
      dpr={[1, 1]}
      gl={{ powerPreference: "high-performance", antialias: false, alpha: true }}
      performance={{ min: 0.5 }}
      style={{ pointerEvents: "auto" }}
    >
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} color="#a78bfa" intensity={1.5} />
      <pointLight position={[-5, -3, 2]} color="#38bdf8" intensity={1} />
      <pointLight position={[0, -4, 3]} color="#06b6d4" intensity={0.8} />
      <EnergyCore />
      <Sphere />
      <ParticleField />
    </Canvas>
  );
}
