// threeUtils.js
// Utility helpers for building orbital visualization scene elements
import * as THREE from 'three';

export function createRenderer(container) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.physicallyCorrectLights = true;
  renderer.setSize(container.clientWidth, container.clientHeight);
  return renderer;
}

export function createCamera(container) {
  const camera = new THREE.PerspectiveCamera(
    50,
    container.clientWidth / container.clientHeight,
    0.1,
    2000
  );
  camera.position.set(0, 2, 5);
  return camera;
}

export function createLight(scene) {
  const light = new THREE.PointLight(0xffffff, 10000, 0, 2);
  light.position.set(0, 0, 0);
  scene.add(light);
  return light;
}

export function resizeRenderer(renderer, camera, container) {
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
}

let _nebulaTexture = null;

function createNebulaBackground() {
  if (_nebulaTexture) return _nebulaTexture;
  const size = 1024;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');

  // Radial gradient (center brighter, edges darker)
  const grad = ctx.createRadialGradient(
    size * 0.5, size * 0.5, size * 0.1,
    size * 0.5, size * 0.5, size * 0.6
  );
  grad.addColorStop(0.0, '#1d1f30');
  grad.addColorStop(0.4, '#0f1322');
  grad.addColorStop(1.0, '#03040a');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);

  // Soft noise (subtle nebulous texture)
  const imgData = ctx.getImageData(0, 0, size, size);
  const d = imgData.data;
  for (let i = 0; i < d.length; i += 4) {
    // Low-frequency blotches via coarse sampling
    if (Math.random() < 0.015) {
      const tint = 20 + Math.random() * 35;
      d[i] = Math.min(d[i] + tint, 255);
      d[i + 1] = Math.min(d[i + 1] + tint * 0.6, 255);
      d[i + 2] = Math.min(d[i + 2] + tint * 0.9, 255);
    }
    // Slight dark specks
    if (Math.random() < 0.01) {
      const dip = Math.random() * 35;
      d[i] = Math.max(d[i] - dip, 0);
      d[i + 1] = Math.max(d[i + 1] - dip, 0);
      d[i + 2] = Math.max(d[i + 2] - dip, 0);
    }
  }
  ctx.putImageData(imgData, 0, 0);

  _nebulaTexture = new THREE.CanvasTexture(canvas);
  _nebulaTexture.colorSpace = THREE.SRGBColorSpace;
  return _nebulaTexture;
}

export function applyNebulaBackground(scene) {
  scene.background = createNebulaBackground();
  return scene.background;
}
