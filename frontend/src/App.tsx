import "./App.css";
import { lazy, Suspense, useState } from "react";
import Dashboard from "./components/Dashboard";

type AppScreen = "landing" | "dashboard";
const LandingExperience = lazy(() => import("./components/LandingExperience"));

function App() {
  const [activeScreen, setActiveScreen] = useState<AppScreen>("landing");

  if (activeScreen === "dashboard") {
    return <Dashboard onBack={() => setActiveScreen("landing")} />;
  }

  return (
    <Suspense fallback={<div className="landing-loading">Spendly</div>}>
      <LandingExperience onGetStarted={() => setActiveScreen("dashboard")} />
    </Suspense>
  );
}

export default App;
