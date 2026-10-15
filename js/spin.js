/* ATELIER BRUT — visionneuse 360° (séquence d'images)
   <div class="spin" data-src="img/spin/origine/frame-{i}.jpg" data-frames="36" data-start="0">
   Glisser pour tourner, molette ignorée, flèches ← → au clavier, inertie douce. */

const pad = (n) => String(n).padStart(3, "0");

export function initSpin(el) {
  const src = el.dataset.src, n = +el.dataset.frames || 36;
  const autoplay = el.dataset.autoplay !== "false";
  let frame = +el.dataset.start || 0;
  const img = document.createElement("img");
  img.alt = el.dataset.alt || ""; img.draggable = false; img.decoding = "async";
  el.appendChild(img);
  const bar = document.createElement("div"); bar.className = "spin-bar"; el.appendChild(bar);
  const hint = document.createElement("div"); hint.className = "spin-hint"; hint.textContent = el.dataset.hint || "Glissez pour tourner"; el.appendChild(hint);
  const meta = el.parentElement && el.parentElement.querySelector(".spinmeta-bar");
  const urls = Array.from({ length: n }, (_, i) => src.replace("{i}", pad(i)));
  const loaded = new Array(n).fill(false);
  let loadedCount = 0;

  function show(i) {
    frame = ((Math.round(i) % n) + n) % n;
    if (loaded[frame]) img.src = urls[frame];
    bar.style.setProperty("--p", (frame / n));
    if (meta) meta.style.setProperty("--p", (frame / n));
  }
  // chargement : la première image, puis par bonds (0, 18, 9, 27…) pour une rotation utilisable très vite
  const order = [];
  (function rec(a, b) { if (b - a < 1) return; const m = Math.floor((a + b) / 2); order.push(m); rec(a, m); rec(m + 1, b); })(0, n);
  const seq = [0, ...order.filter(x => x !== 0)];
  let idx = 0, inflight = 0;
  function pump() {
    while (inflight < 3 && idx < seq.length) {
      const i = seq[idx++]; inflight++;
      const im = new Image(); im.decoding = "async";
      im.onload = im.onerror = () => { inflight--; loaded[i] = true; loadedCount++; if (i === frame) img.src = urls[i]; el.classList.toggle("ready", loadedCount >= Math.min(n, 8)); pump(); };
      im.src = urls[i];
    }
  }
  pump();
  show(frame);

  // interaction
  let dragging = false, lastX = 0, vel = 0, acc = 0, raf = null, idle = true;
  const perFrame = () => Math.max(4, el.clientWidth / n);
  function onDown(e) {
    dragging = true; idle = false; lastX = e.clientX; vel = 0; el.classList.add("grabbing"); hint.classList.add("off");
    el.setPointerCapture?.(e.pointerId);
  }
  function onMove(e) {
    if (!dragging) return;
    const dx = e.clientX - lastX; lastX = e.clientX;
    acc += dx; vel = dx;
    const steps = Math.trunc(acc / perFrame());
    if (steps) { show(frame - steps); acc -= steps * perFrame(); }
  }
  function onUp() {
    if (!dragging) return; dragging = false; el.classList.remove("grabbing");
    // inertie
    let v = vel * .9;
    cancelAnimationFrame(raf);
    const step = () => {
      if (Math.abs(v) < .4) { idle = true; return; }
      acc += v; v *= .92;
      const steps = Math.trunc(acc / perFrame());
      if (steps) { show(frame - steps); acc -= steps * perFrame(); }
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  }
  el.addEventListener("pointerdown", onDown);
  el.addEventListener("pointermove", onMove);
  el.addEventListener("pointerup", onUp); el.addEventListener("pointercancel", onUp); el.addEventListener("pointerleave", onUp);
  el.tabIndex = 0; el.setAttribute("role", "img"); el.setAttribute("aria-label", img.alt + " — vue à 360°, utilisez les flèches pour tourner");
  el.addEventListener("keydown", e => { if (e.key === "ArrowLeft") { show(frame - 1); idle = false; } if (e.key === "ArrowRight") { show(frame + 1); idle = false; } });

  // rotation lente automatique tant que l'utilisateur n'a pas touché (respecte prefers-reduced-motion)
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (autoplay && !reduce) {
    let t = 0, visible = true;
    new IntersectionObserver(e => visible = e[0].isIntersecting, { threshold: .1 }).observe(el);
    const tick = (now) => {
      if (idle && visible && loadedCount >= Math.min(n, 8) && now - t > 140) { t = now; show(frame + 1); }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
  return { show, get frame() { return frame; } };
}

document.querySelectorAll(".spin[data-src]").forEach(initSpin);
