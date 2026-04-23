import "./App.css";
import { Canvas } from "@react-three/fiber";
import { Suspense, useMemo, useState } from "react";
import { NoToneMapping } from "three";
import Galaxy from "./components/Galaxy";
import GalaxyScene from "./components/GalaxyScene";
import Vignette from "./components/Vignette";
import { Bloom, EffectComposer, Select, Selection } from "@react-three/postprocessing";

const galaxyFocal: [number, number] = [0.5, 0.25];
const galaxyRotation: [number, number] = [1.0, 0.0];

function App() {
  const [mousePosition, setMousePosition] = useState({ x: 0.5, y: 0.5 });

  const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
    const { clientX, clientY, currentTarget } = event;
    const { left, top, width, height } = currentTarget.getBoundingClientRect();
    const x = (clientX - left) / width;
    const y = 1.0 - (clientY - top) / height;

    setMousePosition({ x, y });
  };

  const galaxySceneCanvas = useMemo(
    () => (
      <Canvas
        className="galaxy-scene-canvas"
        camera={{ position: [0, -10, 4.5], fov: 75 }}
        gl={{ alpha: true, toneMapping: NoToneMapping }}
      >
        <Suspense fallback={null}>
          <Selection>
            <EffectComposer multisampling={0} enableNormalPass={false}>
              <Bloom
                intensity={2}
                luminanceThreshold={0.1}
                luminanceSmoothing={0.1}
                height={1024}
                mipmapBlur
              />
            </EffectComposer>
            <Select enabled>
              <GalaxyScene />
            </Select>
          </Selection>
        </Suspense>
      </Canvas>
    ),
    [],
  );

  return (
    <div className="app-container" onMouseMove={handleMouseMove}>
      <div className="galaxy-background">
        <Galaxy
          focal={galaxyFocal}
          rotation={galaxyRotation}
          mouseRepulsion
          mouseInteraction={false}
          mousePosition={mousePosition}
          density={1}
          glowIntensity={0.5}
          saturation={0.5}
          hueShift={200}
          repulsionStrength={1}
          twinkleIntensity={0.4}
          rotationSpeed={0.1}
          animateIn={false}
        />
      </div>

      {galaxySceneCanvas}
      <Vignette />
      <div className="content-container" />
    </div>
  );
}

export default App;
