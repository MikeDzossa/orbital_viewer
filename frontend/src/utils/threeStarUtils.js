import * as THREE from 'three';
import { STAR_TEXTURES, STAR_SCALES, STAR_DEFAULT_COLORS, SIZE_SCALE } from './constants';

// Preload textures synchronously using dynamic import of static asset paths.
// For textures managed in src/assets, replace STAR_TEXTURES with import.meta.glob if desired.
// Here we assume STAR_TEXTURES maps names to public or build-served URLs.
const _textureLoader = new THREE.TextureLoader();
const _materialCache = new Map();

function createMaterial(name, fallbackColor) {
  if (_materialCache.has(name)) return _materialCache.get(name);
  const url = STAR_TEXTURES[name];
  let mat;
  if (url) {
    const texture = _textureLoader.load(url, tex => { tex.colorSpace = THREE.SRGBColorSpace; });
    mat = new THREE.MeshBasicMaterial({ map: texture });
  } else {
    mat = new THREE.MeshBasicMaterial({ color: fallbackColor });
  }
  _materialCache.set(name, mat);
  return mat;
}

export function getPlanetScale(name) {
  const base = STAR_SCALES[name] || 0.5;
  return base * SIZE_SCALE; // apply global uniform scale
}

export function createSun(scene) {
  const name = 'Sun';
  const radius = getPlanetScale(name);
  const fallbackColor = STAR_DEFAULT_COLORS.Sun || 0xffff66;
  const mat = createMaterial(name, fallbackColor);

  const sun = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 48, 48),
    mat
  );
  scene.add(sun);
  return sun;
}

export function createLabelSprite(text, options = {}) {
  const {
    fontSize = 48,
    color = 'white',
    padding = 8,
    background = 'rgba(0,0,0,0.35)',
    borderRadius = 6,
    scaleFactor = 1.0, // additional multiplier after radius-based scale
  } = options;

  const dpr = (typeof window !== 'undefined' && window.devicePixelRatio) ? window.devicePixelRatio : 1;
  const ctxFont = `${fontSize}px sans-serif`;
  // Create a temporary canvas to measure
  const measureCanvas = document.createElement('canvas');
  const measureCtx = measureCanvas.getContext('2d');
  measureCtx.font = ctxFont;
  const metrics = measureCtx.measureText(text);
  const textWidth = metrics.width;
  const textHeight = fontSize * 1.1;
  const totalWidth = textWidth + padding * 2;
  const totalHeight = textHeight + padding * 2;

  const canvas = document.createElement('canvas');
  canvas.width = Math.ceil(totalWidth * dpr);
  canvas.height = Math.ceil(totalHeight * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.font = ctxFont;
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = background;
  // Rounded rect background
  if (borderRadius > 0) {
    const r = borderRadius;
    ctx.beginPath();
    ctx.moveTo(r, 0);
    ctx.lineTo(totalWidth - r, 0);
    ctx.quadraticCurveTo(totalWidth, 0, totalWidth, r);
    ctx.lineTo(totalWidth, totalHeight - r);
    ctx.quadraticCurveTo(totalWidth, totalHeight, totalWidth - r, totalHeight);
    ctx.lineTo(r, totalHeight);
    ctx.quadraticCurveTo(0, totalHeight, 0, totalHeight - r);
    ctx.lineTo(0, r);
    ctx.quadraticCurveTo(0, 0, r, 0);
    ctx.closePath();
    ctx.fill();
  } else {
    ctx.fillRect(0, 0, totalWidth, totalHeight);
  }
  ctx.fillStyle = color;
  ctx.fillText(text, padding, padding + fontSize);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false, depthWrite: false });
  const sprite = new THREE.Sprite(spriteMat);
  // We'll scale later in update using stored intrinsic size
  sprite.userData.labelDimensions = { w: totalWidth / fontSize, h: totalHeight / fontSize, scaleFactor };
  sprite.renderOrder = 999; // draw above planets
  return sprite;
}

export function buildPlanetOrbitWithTexture(scene, name, trajectory, fallbackColor) {
  const pts = trajectory.map(p => new THREE.Vector3(p.x, p.y, p.z));
  const geometry = new THREE.BufferGeometry().setFromPoints(pts);
  const material = new THREE.LineBasicMaterial({ color: fallbackColor });
  const orbitLine = new THREE.Line(geometry, material);
  scene.add(orbitLine);

  const radius = getPlanetScale(name);
  const bodyMat = createMaterial(name, fallbackColor);
  const body = new THREE.Mesh(new THREE.SphereGeometry(radius, 32, 32), bodyMat);
  scene.add(body);

  const sprite = createLabelSprite(name, { scaleFactor: 1.0 });
  scene.add(sprite);

  return { name, pts, body, sprite, orbitLine, radius };
}

export function buildPlanetOrbit(scene, name, trajectory, color) {
  const pts = trajectory.map(p => new THREE.Vector3(p.x, p.y, p.z));
  const geometry = new THREE.BufferGeometry().setFromPoints(pts);
  const material = new THREE.LineBasicMaterial({ color });
  const orbitLine = new THREE.Line(geometry, material);
  scene.add(orbitLine);

  const radius = 1; // default
  const body = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 16, 16),
    new THREE.MeshBasicMaterial({ color })
  );
  scene.add(body);

  const sprite = createLabelSprite(name, { scaleFactor: 1.0 });
  scene.add(sprite);

  return { name, pts, body, sprite, orbitLine, radius };
}

export function updatePlanetObject(obj, frame) {
  const { pts, body, sprite, radius } = obj;
  if (!pts.length) return;
  const p = pts[frame % pts.length];
  body.position.copy(p);
  body.position.y += 0.0005 * Math.sin(frame * 0.01);
  if (sprite) {
    // Position label above planet
    const verticalOffset = radius * 1.4;
    sprite.position.copy(p).add(new THREE.Vector3(0, verticalOffset, 0));
    // Scale sprite relative to radius & intrinsic size
    const dims = sprite.userData.labelDimensions;
    if (dims) {
      const base = radius * 0.6 * dims.scaleFactor;
      sprite.scale.set(base * dims.w, base * dims.h, 1);
    }
  }
}

export function disposePlanetObject(obj) {
  if (obj.orbitLine) {
    obj.orbitLine.geometry?.dispose();
    obj.orbitLine.material?.dispose();
  }
  if (obj.body) {
    obj.body.geometry?.dispose();
    // Do not dispose shared material if other planets use it
  }
  if (obj.sprite) {
    obj.sprite.material?.map?.dispose();
    obj.sprite.material?.dispose();
  }
}