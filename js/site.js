/* ATELIER BRUT — interactions légères */
(function () {
  const hdr = document.querySelector(".hdr"), burger = document.querySelector(".burger");
  if (burger) burger.addEventListener("click", () => {
    const open = hdr.classList.toggle("open"); burger.setAttribute("aria-expanded", open); burger.textContent = open ? "Fermer" : "Menu";
  });
  // lien courant
  const here = "/" + (location.pathname.split("/").pop() || "").replace(/\.html$/, "");
  document.querySelectorAll(".hdr nav a").forEach(a => { if (a.getAttribute("href") === here) a.setAttribute("aria-current", "page"); });
  // en-tête : fond au défilement
  const onScroll = () => hdr && hdr.classList.toggle("scrolled", scrollY > 24);
  addEventListener("scroll", onScroll, { passive: true }); onScroll();
  // apparition des images (une seule fois)
  if (!matchMedia("(prefers-reduced-motion: reduce)").matches && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { rootMargin: "0px 0px -8% 0px" });
    document.querySelectorAll(".reveal").forEach(el => io.observe(el));
    // filet de sécurité : tout est visible après 2,5 s quoi qu'il arrive
    setTimeout(() => document.querySelectorAll(".reveal:not(.in)").forEach(el => el.classList.add("in")), 2500);
  } else document.querySelectorAll(".reveal").forEach(el => el.classList.add("in"));
})();
