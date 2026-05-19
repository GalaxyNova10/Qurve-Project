import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Line } from '@react-three/drei';
import * as THREE from 'three';

interface SimplifiedMetrics {
  utilization: number;
  memory: number;
  temperature: number;
  power: number;
  energy: number;
}

interface EnergyLandscape3DProps {
  metrics: SimplifiedMetrics | null;
  convergenceProgress: number;
}

const SurfaceMesh = ({ metrics }: { metrics: SimplifiedMetrics | null }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  
  // Create geometry
  const gridSize = 50;
  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(20, 20, gridSize, gridSize);
    geo.rotateX(-Math.PI / 2); // Lay flat
    return geo;
  }, []);

  // Update vertices in render loop
  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.getElapsedTime();
    const positions = meshRef.current.geometry.attributes.position;
    
    // Base influence from metrics
    const utilFactor = (metrics?.utilization || 50) / 100;
    const tempFactor = (metrics?.temperature || 50) / 100;
    
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const z = positions.getZ(i); // Since we rotated X, Z is the depth
      
      // Energy function (Himmelblau-like or Ackley-like, simplified + noise)
      let y = Math.sin(x * 0.5 + time * 0.5) * Math.cos(z * 0.5 + time * 0.3) * 2;
      y += Math.sin(x * 1.5 - time) * 0.5 * utilFactor;
      y += Math.cos(z * 2.0 + time * 2) * 0.3 * tempFactor;
      
      // Add a deep minimum in the center
      const distToCenter = Math.sqrt(x*x + z*z);
      y -= Math.exp(-distToCenter * 0.2) * 3;
      
      positions.setY(i, y);
    }
    positions.needsUpdate = true;
    meshRef.current.geometry.computeVertexNormals();
  });

  // Custom shader material for the surface to map from deep navy -> cyan -> neon purple
  const material = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        minHeight: { value: -4.0 },
        maxHeight: { value: 3.0 },
        colorMin: { value: new THREE.Color('#0F172A') },   // Deep Navy
        colorMid: { value: new THREE.Color('#06B6D4') },   // Cyan
        colorMax: { value: new THREE.Color('#7C3AED') },   // Neon Purple
      },
      vertexShader: `
        varying float vHeight;
        void main() {
          vHeight = position.y;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float minHeight;
        uniform float maxHeight;
        uniform vec3 colorMin;
        uniform vec3 colorMid;
        uniform vec3 colorMax;
        varying float vHeight;
        
        void main() {
          float t = clamp((vHeight - minHeight) / (maxHeight - minHeight), 0.0, 1.0);
          vec3 color;
          if(t < 0.5) {
            color = mix(colorMin, colorMid, t * 2.0);
          } else {
            color = mix(colorMid, colorMax, (t - 0.5) * 2.0);
          }
          // Wireframe-like grid effect
          gl_FragColor = vec4(color, 0.9);
        }
      `,
      wireframe: true,
      transparent: true,
    });
  }, []);

  return (
    <mesh ref={meshRef} geometry={geometry} material={material} />
  );
};

const BifurcationPath = ({ progress }: { progress: number }) => {
  const points = useMemo(() => {
    const pts = [];
    const steps = 100;
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      // Define a path that spirals down to the center
      const r = 10 * (1 - t);
      const theta = t * Math.PI * 4;
      const x = r * Math.cos(theta);
      const z = r * Math.sin(theta);
      
      // Height calculation matching the surface approximately
      let y = Math.sin(x * 0.5) * Math.cos(z * 0.5) * 2;
      const distToCenter = Math.sqrt(x*x + z*z);
      y -= Math.exp(-distToCenter * 0.2) * 3;
      y += 0.5; // Offset slightly above surface
      
      pts.push(new THREE.Vector3(x, y, z));
    }
    return pts;
  }, []);

  // Display only the portion of the path up to the current progress
  const visiblePointsCount = Math.max(2, Math.floor((progress / 100) * points.length));
  const visiblePoints = points.slice(0, visiblePointsCount);

  if (visiblePoints.length < 2) return null;

  return (
    <group>
      <Line
        points={visiblePoints}
        color="#7C3AED" // Changed from Cyan to Neon Purple for Qurve aesthetic
        lineWidth={3}
        transparent
        opacity={0.8}
      />
      {/* Current position marker */}
      <mesh position={visiblePoints[visiblePoints.length - 1]}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshBasicMaterial color="#ffffff" />
        <pointLight color="#7C3AED" intensity={2} distance={5} />
      </mesh>
    </group>
  );
};

export default function EnergyLandscape3D({ metrics, convergenceProgress = 0 }: EnergyLandscape3DProps) {
  return (
    <div className="w-full h-full min-h-[400px] bg-[#0B0E14] rounded-xl overflow-hidden relative">
      <Canvas camera={{ position: [15, 12, 15], fov: 45 }} className="w-full h-full">
        <color attach="background" args={['#0B0E14']} />
        <ambientLight intensity={0.5} />
        <SurfaceMesh metrics={metrics} />
        <BifurcationPath progress={convergenceProgress} />
        <OrbitControls 
          enableDamping 
          dampingFactor={0.05} 
          autoRotate 
          autoRotateSpeed={0.5} 
          maxPolarAngle={Math.PI / 2.2} 
        />
      </Canvas>
    </div>
  );
}
