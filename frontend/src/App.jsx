import { useState } from "react";
import OrbitVisualizer from "./components/OrbitVisualizer";
import ErrorBoundary from './components/ErrorBoundary';
import VerticalMenu from './components/VerticalMenu';
import { fetchOrbit } from "./services/api";

import './css/App.css';

function App() {
  const [trajectory, setTrajectory] = useState(null);

  const loadOrbit = async () => {
    const data = await fetchOrbit({
      a: 1.5,
      e: 0.2,
      i: 10,
      raan: 45,
      argp: 30,
      M0: 0,
      epoch: "2025-10-01T00:00:00"
    });
    setTrajectory(data.trajectory);
  };

  return (
    <div id="root">
      {/* Left vertical menu */}
      <VerticalMenu>
        <button onClick={loadOrbit} style={{ marginTop: "20px" }}>
          Load Orbit
        </button>
      </VerticalMenu>

      {/* Main content area */}
      <div className="main-content">
        {trajectory ? (
          <ErrorBoundary>
            <OrbitVisualizer trajectory={trajectory} />
          </ErrorBoundary>
        ) : (
          <div className="placeholder-message">
            Click "Load Orbit" to display the orbit
          </div>
        )}
      </div>
    </div>
  );
}

export default App;