/* ATELIER BRUT — configurateur (aperçus photoréalistes pré-calculés + estimation) */
(function () {
  const state = { format: "bout", wood: "pin", top: "bois", cords: "chanvre", pattern: "centre", text: "", extras: new Set() };

  const LABEL = {
    format: { bout: "Bout de canapé 62 × 62 × 74 cm", console: "Console 120 × 42 × 78 cm", manger: "Table à manger 190 × 88 × 75 cm" },
    wood: { pin: "pin brossé", chene: "chêne", noyer: "noyer", olivier: "olivier", frene: "frêne brûlé" },
    top: { bois: "plateau bois plein", echiquier: "plateau échiquier en céramique émaillée" },
    cords: { chanvre: "cordes de chanvre", noir: "cordes de lin noir", bordeaux: "cordes de lin bordeaux", mousse: "cordes vert mousse", laiton: "câbles de laiton" },
    pattern: { centre: "cinq cordes", harpe: "harpe, 18 cordes" },
    extras: { inlay: "filet de laiton au chant", lamp: "lumière intégrée sous le plateau" },
  };
  const NOTE = {
    centre: "Quatre haubans aux coins et la corde centrale qui porte le plateau.",
    harpe: "Dix-huit cordes tendues à la verticale dans les deux triangles. Elles vibrent quand on les pince.",
  };

  const BASE = { bout: 420, console: 1100, manger: 2900 };
  const WOOD = { pin: 1, chene: 1.35, noyer: 1.6, olivier: 1.75, frene: 1.5 };
  const CORD = { chanvre: 0, noir: 40, bordeaux: 40, mousse: 40, laiton: 160 };
  const OPT = { echiquier: 620, harpe: 260, lev: 380, text: 120, inlay: 240, lamp: 290 };

  /** Choix de l'image la plus proche parmi les pièces rendues. */
  function preview() {
    const s = state;
    if (s.format === "manger") return ["manger", "Table à manger « Grande table »"];
    if (s.format === "console") return ["console", "Console « Olivier »"];
    if (s.top === "echiquier") return ["echec", "« Échec et mat »"];
    if (s.pattern === "harpe") return ["harpe", "« Harpe »"];
    if (s.extras.has("lamp") || s.extras.has("inlay")) return ["nocturne", "« Nocturne »"];
    if (s.text) return ["manifeste", "« Manifeste »"];
    return ({ pin: ["origine", "N°1 « Origine »"], chene: ["harpe", "« Harpe »"], noyer: ["manifeste", "« Manifeste »"], frene: ["brulee", "« Brûlée »"], olivier: ["console", "Console « Olivier »"] })[s.wood];
  }

  function price() {
    let p = BASE[state.format] * WOOD[state.wood];
    p += CORD[state.cords] * (state.format === "manger" ? 2 : 1);
    if (state.top === "echiquier") p += OPT.echiquier * (state.format === "manger" ? 1.6 : 1);
    if (state.pattern === "harpe") p += OPT.harpe * (state.format === "bout" ? 1 : 2);
    if (state.text) p += OPT.text;
    if (state.extras.has("inlay")) p += OPT.inlay * (state.format === "manger" ? 1.8 : 1);
    if (state.extras.has("lamp")) p += OPT.lamp;
    return Math.round(p / 10) * 10;
  }
  function delay() {
    let w = state.format === "manger" ? [8, 10] : state.format === "console" ? [7, 9] : [6, 8];
    if (state.top === "echiquier") w = [w[0] + 2, w[1] + 2];
    return `${w[0]} à ${w[1]} semaines`;
  }
  function summaryText() {
    const parts = [LABEL.format[state.format], LABEL.wood[state.wood], LABEL.top[state.top], LABEL.cords[state.cords], LABEL.pattern[state.pattern]];
    state.extras.forEach(e => parts.push(LABEL.extras[e]));
    if (state.text) parts.push(`gravure « ${state.text} »`);
    return parts.join(", ");
  }

  const img = document.getElementById("preview"), note = document.getElementById("previewNote");
  const priceEl = document.getElementById("price"), delayEl = document.getElementById("delay");
  const sum = document.getElementById("summary"), ask = document.getElementById("ask"), pnote = document.getElementById("patternNote");
  const fmt = new Intl.NumberFormat("fr-FR");

  function render() {
    const [key, name] = preview();
    const src = `img/pieces/${key}-studio.jpg`;
    if (!img.src.endsWith(src)) { img.style.opacity = 0; const im = new Image(); im.onload = () => { img.src = src; img.style.opacity = 1; }; im.src = src; }
    note.textContent = `Aperçu : ${name}, la pièce la plus proche de votre composition.`;
    pnote.textContent = NOTE[state.pattern];
    const p = price();
    priceEl.textContent = `${fmt.format(p)} €`;
    delayEl.textContent = delay();
    const txt = summaryText();
    sum.textContent = txt.charAt(0).toUpperCase() + txt.slice(1) + ".";
    const body = `Bonjour,\n\nJe souhaite un devis pour la table suivante :\n— ${txt}\n\nEstimation affichée : ${fmt.format(p)} €\n\nMes coordonnées :\n`;
    ask.href = `mailto:contact@atelierbrut.fr?subject=${encodeURIComponent("Demande de devis — table sur mesure")}&body=${encodeURIComponent(body)}`;
  }

  document.querySelectorAll("[data-key]").forEach(group => {
    const key = group.dataset.key, multi = group.dataset.multi === "true";
    group.querySelectorAll("button").forEach(btn => btn.addEventListener("click", () => {
      const v = btn.dataset.v;
      if (multi) {
        const on = btn.getAttribute("aria-pressed") !== "true";
        btn.setAttribute("aria-pressed", on); on ? state.extras.add(v) : state.extras.delete(v);
      } else {
        group.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b === btn));
        state[key] = v;
      }
      render();
    }));
  });
  const text = document.getElementById("text");
  text.addEventListener("input", () => { state.text = text.value.trim(); render(); });

  // préremplissage depuis l'URL (?wood=noyer&top=echiquier…)
  const q = new URLSearchParams(location.search);
  ["format", "wood", "top", "cords", "pattern"].forEach(k => {
    const v = q.get(k); if (!v) return;
    const b = document.querySelector(`[data-key="${k}"] [data-v="${v}"]`); if (b) b.click();
  });
  render();
})();
