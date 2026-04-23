import { Points, useGLTF } from "@react-three/drei";
import { useFrame, useLoader } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import {
  BufferGeometry,
  Color,
  Group,
  MathUtils,
  Mesh,
  TextureLoader,
  Vector3,
} from "three";

const solarSystemStarPosition = new Vector3(
  0.038105392881217164,
  -2.745814737039023,
  0.7172299984047412,
);

function GalaxyScene() {
  const galaxyRef = useRef<Group | null>(null);
  const solarSystemStarRef = useRef<Mesh | null>(null);

  const starTexture = useLoader(TextureLoader, "/assets/img/discs/disc.png");
  const { nodes } = useGLTF("/assets/models/galaxy.glb") as unknown as {
    nodes: {
      Object_2: {
        geometry: BufferGeometry;
      };
    };
  };

  const [positions, colors] = useMemo(() => {
    nodes.Object_2.geometry.center();

    const centeredPositions = new Float32Array(nodes.Object_2.geometry.attributes.position.array.buffer);
    const centeredColors = new Float32Array(centeredPositions.length);
    const color = new Color();

    const getDistanceToCenter = (x: number, y: number, z: number) =>
      Math.sqrt(x * x + y * y + z * z);

    for (let index = 0; index < centeredPositions.length; index += 3) {
      const x = centeredPositions[index];
      const y = centeredPositions[index + 1];
      const z = centeredPositions[index + 2];
      const normalizedDistanceToCenter = getDistanceToCenter(x, y, z) / 100;

      color.setRGB(
        Math.cos(normalizedDistanceToCenter),
        MathUtils.randFloat(0, 0.8),
        Math.sin(normalizedDistanceToCenter),
      );
      color.toArray(centeredColors, index);
    }

    return [centeredPositions, centeredColors];
  }, [nodes]);

  useFrame(({ clock, camera }) => {
    if (galaxyRef.current) {
      galaxyRef.current.rotation.z = clock.getElapsedTime() / 15;
    }

    if (solarSystemStarRef.current) {
      const objectPosition = new Vector3();
      solarSystemStarRef.current.getWorldPosition(objectPosition);

      const dist = objectPosition.distanceTo(camera.position);
      let starSize = 1 / (dist * 0.5);
      starSize = Math.max(0.01, Math.min(starSize, 15));
      solarSystemStarRef.current.scale.set(starSize, starSize, starSize);
    }
  });

  return (
    <group dispose={null} ref={galaxyRef} position={[0, -5.0, 0]}>
      <light position={[0, 0, 0]} intensity={0.2} />
      <ambientLight intensity={0.1} />

      <Points scale={0.065} positions={positions} colors={colors}>
        <pointsMaterial
          transparent
          depthWrite={false}
          vertexColors
          opacity={1}
          size={0.01}
          sizeAttenuation
          blending={2}
        />
      </Points>

      <group name="SolarSystemStar">
        <mesh ref={solarSystemStarRef} position={solarSystemStarPosition}>
          <sphereGeometry args={[0.01, 32, 32]} />
          <meshStandardMaterial
            map={starTexture}
            color={0xffffcc}
            emissive={0xffffff}
            emissiveIntensity={2}
          />
        </mesh>
      </group>
    </group>
  );
}

useGLTF.preload("/assets/models/galaxy.glb");

export default GalaxyScene;
