import { useState, useEffect } from "react";
import OrbitVisualizer from "./components/OrbitVisualizer";
import ErrorBoundary from './components/ErrorBoundary';
import VerticalMenu from './components/VerticalMenu';
import { fetchOrbit, fetchPlanets } from "./services/api";

import './css/App.css';

function App() {
  // Holds API response: { epoch, planets: { Mercury: {...}, Earth: {...}, ... } }
  const [planetsOrbitalElements, setPlanetsOrbitalElements] = useState(null);
  // Holds trajectories per planet: { Earth: [...], Mars: [...], ... }
  const [trajectories, setTrajectories] = useState({});
  // Loading & error states
  const [loadingPlanets, setLoadingPlanets] = useState(false);
  const [loadingTrajectories, setLoadingTrajectories] = useState(false);
  const [error, setError] = useState(null);

  // Fetch planetary orbital elements once on mount
  useEffect(() => {
    const loadPlanets = async () => {
      console.log('[App] Initiating fetchPlanets()');
      setLoadingPlanets(true);
      setError(null);
      try {
        const now = new Date();
        const isoString = now.toISOString();
        // Convert "YYYY-MM-DDTHH:MM:SS.sssZ" to "YYYY-MM-DD HH:MM"
        const todayIso = isoString.replace(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}).*$/, '$1 $2');
        const data = await fetchPlanets(todayIso);
        console.log('[App] fetchPlanets() success:', data);
        setPlanetsOrbitalElements(data);
      } catch (e) {
        console.error('[App] fetchPlanets() failed:', e);
        setError(e.message || 'Failed fetching planets');
      } finally {
        setLoadingPlanets(false);
        console.log('[App] fetchPlanets() done');
      }
    };
    loadPlanets();
  }, []);

  const loadAllTrajectories = async () => {
    if (!planetsOrbitalElements) {
      console.warn('[App] Attempted to load trajectories before planetsOrbitalElements ready');
      return;
    }
    console.log('[App] Starting trajectory fetch for all planets');
    setLoadingTrajectories(true);
    setError(null);
    try {
      const epoch = planetsOrbitalElements.epoch;
      const planetEntries = Object.entries(planetsOrbitalElements.planets);

      const results = {};
      for (const [planet, elems] of planetEntries) {
        if (elems && !elems.error) {
          console.log(`[App] Fetching trajectory for planet=${planet}`);
          try {
            const payload = { ...elems }; // elems already contains orbital elements
            const orbitRes = await fetchOrbit(payload, 500);
            results[planet] = orbitRes.trajectory;
            console.log(`[App] Success trajectory planet=${planet} points=${orbitRes.trajectory?.length}`);
          } catch (innerErr) {
            console.error(`[App] Failed trajectory planet=${planet}:`, innerErr);
            results[planet] = { error: innerErr.message };
          }
        } else {
            if (elems?.error) {
              console.warn(`[App] Skipping planet=${planet} due to previous error: ${elems.error}`);
            } else {
              console.warn(`[App] Skipping planet=${planet}: missing elements`);
            }
            results[planet] = elems; // preserve error state
        }
      }
      setTrajectories(results);
      console.log('[App] All trajectory fetches complete');
    } catch (e) {
      console.error('[App] Bulk trajectory fetch failed:', e);
      setError(e.message || 'Failed fetching trajectories');
    } finally {
      setLoadingTrajectories(false);
      console.log('[App] loadAllTrajectories() done');
    }
  };

  return (
    <div id="root">
      <VerticalMenu>
        <button onClick={loadAllTrajectories} style={{ marginTop: "20px" }} disabled={loadingTrajectories || !planetsOrbitalElements}>
          {loadingTrajectories ? 'Loading...' : 'Load Orbits'}
        </button>
        {loadingPlanets && <div style={{ marginTop: '1rem', fontSize: '0.8rem' }}>Fetching planetary data...</div>}
        {error && <div style={{ color: 'salmon', fontSize: '0.75rem', marginTop: '0.5rem' }}>{error}</div>}
      </VerticalMenu>

      <div className="main-content">
        {Object.keys(trajectories).length > 0 ? (
          <ErrorBoundary>
            <OrbitVisualizer trajectories={trajectories} />
          </ErrorBoundary>
        ) : (
          <div className="placeholder-message">
            {loadingPlanets ? 'Loading planetary orbital elements...' : 'Click "Load Orbits" to fetch trajectories'}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;