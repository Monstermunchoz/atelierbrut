/* ATELIER BRUT — configurateur : aperçu de la pièce la plus proche + estimation + demande de devis */
(function () {
  const state = { format: "appoint", wood: "pin", top: "bois", cords: "chaine", text: "", extras: new Set() };

  const LABEL = {
    format: { appoint: "table d'appoint 50 × 50 × 62 cm", gueridon: "guéridon rond Ø 56 × 52 cm", basse: "table basse 100 × 56 × 40 cm", console: "console 96 × 32 × 80 cm" },
    wood: { pin: "pin brossé", chene: "chêne", noyer: "noyer", olivier: "olivier", frene: "frêne brûlé" },
    top: { bois: "plateau bois plein", echiquier: "plateau échiquier en céramique émaillée" },
    cords: { chaine: "chaînettes de laiton", laiton: "câbles de laiton", chanvre: "cordes de chanvre", noir: "cordes de lin noir", bordeaux: "cordes de lin bordeaux" },
    extras: { inlay: "filet de laiton au chant", lamp: "lumière intégrée sous le plateau" },
  };

  const BASE = { appoint: 420, gueridon: 560, basse: 1050, console: 980 };
  const WOOD = { pin: 1, chene: 1.3, noyer: 1.55, olivier: 1.7, frene: 1.45 };
  const CORD = { chaine: 90, laiton: 140, chanvre: 0, noir: 30, bordeaux: 30 };
  const OPT = { echiquier: 620, text: 160, inlay: 240, lamp: 290 };

  /** Pièce de la collection la plus proche de la composition. */
  function preview() {
    const s = state;
    if (s.top === "echiquier") return ["echec", "« Échec et mat »"];
    if (s.format === "basse") return ["basse", "Table basse « Horizon »"];
    if (s.format === "console") return ["console", "Console « Fil »"];
    if (s.format === "gueridon") return ["lune", "« Lune »"];
    if (s.extras.has("lamp") || s.extras.has("inlay")) return ["nocturne", "« Nocturne »"];
    if (s.text) return ["manifeste", "« Manifeste »"];
    return ({ pin: ["origine", "N°1 « Origine »"], chene: ["echec", "« Échec et mat »"], noyer: ["manifeste", "« Manifeste »"], frene: ["brulee", "« Brûlée »"], olivier: ["lune", "« Lune »"] })[s.wood];
  }

  function price() {
    let p = BASE[state.format] * WOOD[state.wood] + CORD[state.cords];
    if (state.top === "echiquier") p += OPT.echiquier * (state.format === "basse" ? 1.5 : 1);
    if (state.text) p += OPT.text;
    if (state.extras.has("inlay")) p += OPT.inlay * (state.format === "basse" ? 1.5 : 1);
    if (state.extras.has("lamp")) p += OPT.lamp;
    return Math.round(p / 10) * 10;
  }
  function delay() {
    let w = state.format === "basse" || state.format === "console" ? [6, 8] : [5, 7];
    if (state.top === "echiquier") w = [w[0] + 2, w[1] + 2];
    return `${w[0]} à ${w[1]} semaines`;
  }
  function summaryText() {
    const parts = [LABEL.format[state.format], LABEL.wood[state.wood], LABEL.top[state.top], LABEL.cords[state.cords]];
    state.extras.forEach(e => parts.push(LABEL.extras[e]));
    if (state.text) parts.push(`gravure « ${state.text} »`);
    return parts.join(", ");
  }

  const img = document.getElementById("preview"), note = document.getElementById("previewNote");
  const priceEl = document.getElementById("price"), delayEl = document.getElementById("delay");
  const sum = document.getElementById("summary"), ask = document.getElementById("ask");
  const fmt = new Intl.NumberFormat("fr-FR");

  // échiquier : seulement sur les plateaux carrés
  function syncConstraints() {
    const chessBtn = document.querySelector('[data-key="top"] [data-v="echiquier"]');
    const round = state.format === "gueridon";
    chessBtn.disabled = round; chessBtn.title = round ? "L'échiquier se fait sur un plateau carré" : "";
    if (round && state.top === "echiquier") document.querySelector('[data-key="top"] [data-v="bois"]').click();
  }

  let current = "";
  function render() {
    const [key, name] = preview();
    if (key !== current) {
      current = key;
      const src = `img/pieces/${key}-studio.jpg`;
      img.style.opacity = 0;
      const im = new Image();
      im.onload = () => { img.src = src; requestAnimationFrame(() => { img.style.opacity = 1; }); };
      im.onerror = () => { img.style.opacity = 1; };
      im.src = src;
    }
    note.textContent = `Aperçu : ${name}, la pièce de la collection la plus proche.`;
    const p = price();
    priceEl.textContent = `${fmt.format(p)} €`;
    delayEl.textContent = delay();
    const txt = summaryText();
    sum.textContent = txt.charAt(0).toUpperCase() + txt.slice(1) + ".";
    const body = `Bonjour,\n\nJe souhaite un devis pour la table en tenségrité suivante :\n— ${txt}\n\nEstimation affichée : ${fmt.format(p)} €\n\nMes coordonnées :\n`;
    ask.href = `mailto:contact@atelierbrut.fr?subject=${encodeURIComponent("Demande de devis — table sur mesure")}&body=${encodeURIComponent(body)}`;
  }

  document.querySelectorAll("[data-key]").forEach(group => {
    const key = group.dataset.key, multi = group.dataset.multi === "true";
    group.querySelectorAll("button").forEach(btn => btn.addEventListener("click", () => {
      if (btn.disabled) return;
      const v = btn.dataset.v;
      if (multi) {
        const on = btn.getAttribute("aria-pressed") !== "true";
        btn.setAttribute("aria-pressed", String(on)); on ? state.extras.add(v) : state.extras.delete(v);
      } else {
        group.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(b === btn)));
        state[key] = v;
      }
      syncConstraints(); render();
    }));
  });
  const text = document.getElementById("text");
  text.addEventListener("input", () => { state.text = text.value.trim(); render(); });

  const q = new URLSearchParams(location.search);
  ["format", "wood", "top", "cords"].forEach(k => {
    const v = q.get(k); if (!v) return;
    const b = document.querySelector(`[data-key="${k}"] [data-v="${v}"]`); if (b) b.click();
  });
  syncConstraints(); render();
})();
