// The 3D part of the home page feature box. Loaded on demand by hopper-viewer.js.
import {
  Box3, Color, DirectionalLight, GridHelper, HemisphereLight, MathUtils,
  NeutralToneMapping, PerspectiveCamera, Scene, SRGBColorSpace, Vector3, WebGLRenderer,
} from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";

const RESUME_AFTER_MS = 4000; // auto-rotate starts again this long after the visitor lets go

export function mount(el, { modelUrl, decoderUrl, onProgress }) {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  const renderer = new WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = NeutralToneMapping;
  renderer.setClearColor(0x000000, 0);
  el.appendChild(renderer.domElement);

  const scene = new Scene();
  scene.add(new HemisphereLight(0xffffff, 0x8a94a6, 2.0));
  const key = new DirectionalLight(0xffffff, 2.2);
  key.position.set(1.2, 2, 1.4);
  scene.add(key);
  const fill = new DirectionalLight(0xffffff, 0.8);
  fill.position.set(-1.5, 0.6, -1);
  scene.add(fill);

  const camera = new PerspectiveCamera(30, 1, 1, 20000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enablePan = true; // right-drag, Shift-drag or two fingers
  controls.screenSpacePanning = true;
  controls.autoRotateSpeed = 1.6;
  controls.minPolarAngle = 0; // straight down from above...
  controls.maxPolarAngle = Math.PI; // ...all the way round to straight up from underneath
  controls.rotateSpeed = 0.9;
  controls.zoomSpeed = 1.2;
  controls.autoRotate = !reducedMotion.matches;

  let resumeTimer = 0;
  controls.addEventListener("start", () => {
    clearTimeout(resumeTimer);
    controls.autoRotate = false;
  });
  controls.addEventListener("end", () => {
    clearTimeout(resumeTimer);
    if (!reducedMotion.matches) resumeTimer = setTimeout(() => (controls.autoRotate = true), RESUME_AFTER_MS);
  });

  let grid = null;
  let home = null;

  function themeColours() {
    const css = getComputedStyle(document.documentElement);
    return {
      line: new Color(css.getPropertyValue("--line").trim() || "#d3d9e2"),
      muted: new Color(css.getPropertyValue("--muted").trim() || "#566076"),
    };
  }
  function paintGrid() {
    if (!grid) return;
    const { line, muted } = themeColours();
    const mats = Array.isArray(grid.material) ? grid.material : [grid.material];
    mats.forEach((m) => { m.vertexColors = false; m.color = line.clone().lerp(muted, 0.35); m.transparent = true; m.opacity = 0.7; m.needsUpdate = true; });
  }
  const themeWatch = new MutationObserver(paintGrid);
  themeWatch.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  function resize() {
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    if (home) frame(false);
  }
  const sizeWatch = new ResizeObserver(resize);
  sizeWatch.observe(el);

  // Fit the whole hopper in view, whatever the box's shape.
  function frame(moveCamera = true) {
    const { size, centre } = home;
    const vFov = MathUtils.degToRad(camera.fov);
    const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
    const radius = Math.max(size.x, size.z) / 2;
    const fitH = (size.y / 2) / Math.tan(vFov / 2);
    const fitW = radius / Math.tan(hFov / 2);
    const dist = Math.max(fitH, fitW) * 1.25 + radius * 0.85;
    controls.minDistance = radius * 0.35;
    controls.maxDistance = dist * 3;
    if (moveCamera) {
      controls.target.copy(centre);
      const dir = new Vector3(1, 0.32, 1).normalize();
      camera.position.copy(centre).addScaledVector(dir, dist);
    }
    controls.update();
  }

  let running = false;
  function tick() { controls.update(); renderer.render(scene, camera); }
  function resume() { if (!running) { running = true; renderer.setAnimationLoop(tick); } }
  function pause() { running = false; renderer.setAnimationLoop(null); }
  document.addEventListener("visibilitychange", () => (document.hidden ? renderer.setAnimationLoop(null) : running && renderer.setAnimationLoop(tick)));

  const draco = new DRACOLoader().setDecoderPath(decoderUrl).setDecoderConfig({ type: "wasm" });
  const loader = new GLTFLoader().setDRACOLoader(draco);

  return new Promise((resolve, reject) => {
    loader.load(
      modelUrl,
      (gltf) => {
        draco.dispose();
        const model = gltf.scene;
        // Stand the model on the floor, centred.
        const box = new Box3().setFromObject(model);
        const size = box.getSize(new Vector3());
        const mid = box.getCenter(new Vector3());
        model.position.set(-mid.x, -box.min.y, -mid.z);
        scene.add(model);

        const span = Math.max(size.x, size.z) * 2.4;
        grid = new GridHelper(span, 12);
        scene.add(grid);
        paintGrid();

        home = { size, centre: new Vector3(0, size.y * 0.46, 0) };
        resize();
        frame();
        tick();
        resume();
        resolve({
          pause,
          resume,
          reset() {
            frame();
            controls.autoRotate = !reducedMotion.matches;
          },
        });
      },
      (e) => { if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total); },
      reject
    );
  });
}
