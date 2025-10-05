import { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { createRenderer, createCamera, createLight, applyNebulaBackground, resizeRenderer } from '../utils/threeSceneUtils';
import { buildPlanetOrbitWithTexture, createSun, updatePlanetObject, disposePlanetObject } from '../utils/threeStarUtils';
import { STAR_DEFAULT_COLORS } from '../utils/constants';

function autoFrame(camera, controls, objects, padding = 1.2) {
  if (!objects.length) return;
  const box = new THREE.Box3();
  objects.forEach(o => {
    if (o.pts && o.pts.length) {
      for (let i = 0; i < o.pts.length; i++) box.expandByPoint(o.pts[i]);
    }
  });
  if (box.isEmpty()) return;
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);

  // Largest dimension defines distance
  const maxDim = Math.max(size.x, size.y, size.z) * padding;

  // Adjust camera so that maxDim fits in vertical FOV
  const fovRad = THREE.MathUtils.degToRad(camera.fov);
  const dist = maxDim / (2 * Math.tan(fovRad / 2));

  camera.position.set(center.x + dist, center.y + dist * 0.25, center.z + dist);
  camera.lookAt(center);
  camera.near = dist * 0.001;
  camera.far = dist * 5;
  camera.updateProjectionMatrix();

  if (controls) {
    controls.target.copy(center);
    controls.update();
  }

  // Return for potential logging
  return { center, dist, maxDim };
}

export default function OrbitVisualizer({ trajectories }) {
  const mountRef = useRef(null);

  useEffect(() => {
    if (!trajectories || Object.keys(trajectories).length === 0) return;

    const container = mountRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    applyNebulaBackground(scene);
    const camera = createCamera(container);
    const renderer = createRenderer(container);
    container.appendChild(renderer.domElement);
    createLight(scene);
    createSun(scene);

    const planetObjects = [];
    let frame = 0;
    let cancelled = false;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    console.log('[OrbitVisualizer] Building planet meshes (static textures sync)');
    const names = Object.keys(trajectories);
    names.forEach(name => {
      const traj = trajectories[name];
      if (!Array.isArray(traj) || traj.length === 0) return;
      const fallbackColor = STAR_DEFAULT_COLORS[name] ?? 0xffffff;
      try {
        const planetObj = buildPlanetOrbitWithTexture(scene, name, traj, fallbackColor);
        planetObjects.push(planetObj);
      } catch (e) {
        console.warn(`[OrbitVisualizer] Failed building ${name}:`, e);
      }
    });

    console.log('[OrbitVisualizer] Planets ready:', planetObjects.map(p => p.name));
    const framed = autoFrame(camera, controls, planetObjects, 1.25);
    if (framed) console.log('[OrbitVisualizer] Autoframe result:', framed);

    const animate = () => {
      if (cancelled) return;
      frame++;
      planetObjects.forEach(o => updatePlanetObject(o, frame));
      controls.update();
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    };
    animate();

    const handleResize = () => {
      resizeRenderer(renderer, camera, container);
      autoFrame(camera, null, planetObjects, 1.25); // re-fit on resize (keep current orbit positions)
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelled = true;
      window.removeEventListener('resize', handleResize);
      planetObjects.forEach(disposePlanetObject);
      renderer.dispose();
      try { container.removeChild(renderer.domElement); } catch { }
      scene.clear();
      console.log('[OrbitVisualizer] Cleanup complete');
    };
  }, [trajectories]);

  return <div ref={mountRef} style={{ width: '100%', height: '100%' }} />;
}