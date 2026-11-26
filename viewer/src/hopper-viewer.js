// Home page feature box: a 3D model of the hopper plus photos, chosen with the
// thumbnails under the main view. This file is small; the 3D part (three.js and
// the model) only downloads once the box is about to scroll into view.

const box = document.querySelector("[data-hopper-feature]");
if (box) setUp(box);

function setUp(box) {
  const stage = box.querySelector(".feature-stage");
  const mount = stage.querySelector(".feature-3d");
  const photo = stage.querySelector(".feature-photo");
  const status = stage.querySelector(".feature-status");
  const reset = stage.querySelector(".feature-reset");
  const buttons = [...box.querySelectorAll(".feature-thumbs button")];
  const modelButton = buttons.find((b) => b.dataset.view === "model");
  const base = import.meta.url;
  let viewer = null;
  let loading = null;
  let visible = false;

  function webglWorks() {
    try {
      const c = document.createElement("canvas");
      return !!(window.WebGLRenderingContext && (c.getContext("webgl2") || c.getContext("webgl")));
    } catch (e) {
      return false;
    }
  }

  function showPhoto(button) {
    photo.src = button.dataset.src;
    photo.alt = button.dataset.alt || "";
    stage.dataset.view = "photo";
    if (viewer) viewer.pause();
  }

  function showModel() {
    stage.dataset.view = "model";
    if (visible) start();
    if (viewer) viewer.resume();
  }

  function choose(button) {
    buttons.forEach((b) => b.setAttribute("aria-pressed", b === button ? "true" : "false"));
    if (button.dataset.view === "model") showModel();
    else showPhoto(button);
  }

  function start() {
    if (loading) return loading;
    status.textContent = "Loading 3D model";
    loading = import("./hopper-scene.js")
      .then((m) =>
        m.mount(mount, {
          modelUrl: new URL("../models/hopper.glb", base).href,
          decoderUrl: new URL("./draco/", base).href,
          onProgress(fraction) {
            status.textContent = fraction < 1
              ? `Loading 3D model, ${Math.round(fraction * 100)}%`
              : "Preparing 3D model";
          },
        })
      )
      .then((v) => {
        viewer = v;
        status.textContent = "";
        stage.classList.add("ready");
        if (stage.dataset.view !== "model" || !visible) viewer.pause();
        return v;
      })
      .catch((err) => {
        console.error(err);
        fallBack();
      });
    return loading;
  }

  // No 3D: drop the model button and open the first photo instead.
  function fallBack() {
    if (modelButton) modelButton.remove();
    buttons.splice(buttons.indexOf(modelButton), 1);
    stage.classList.add("no-3d");
    status.textContent = "";
    if (buttons[0]) choose(buttons[0]);
  }

  buttons.forEach((b) => b.addEventListener("click", () => choose(b)));
  if (reset) reset.addEventListener("click", () => viewer && viewer.reset());

  if (!webglWorks()) {
    fallBack();
    return;
  }

  new IntersectionObserver(
    (entries) => {
      visible = entries[0].isIntersecting;
      if (visible && stage.dataset.view === "model") start();
      if (viewer) visible && stage.dataset.view === "model" ? viewer.resume() : viewer.pause();
    },
    { rootMargin: "200px 0px" }
  ).observe(stage);
}
