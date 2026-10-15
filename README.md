# Atelier Brut — site vitrine

Site statique (HTML / CSS / JS, sans build) pour la marque de mobilier artisanal **Atelier Brut** :
tables en tenségrité, bois massif et cordes tendues, déclinaisons, potagers suspendus, configurateur sur-mesure.

## Déploiement

Dépôt pensé pour **Vercel** : importer le repo, framework « Other », aucun build, dossier racine `/`.
`vercel.json` gère les URL propres (`/collection` → `collection.html`), le cache des images et quelques en-têtes de sécurité.

Avant mise en ligne :

1. Remplacer `https://atelierbrut.fr` (canonical, Open Graph, `sitemap.xml`, `robots.txt`, JSON-LD) par le domaine définitif.
2. Compléter `mentions-legales.html` (raison sociale, SIREN, adresse) et faire relire les CGV.
3. Remplacer `contact@atelierbrut.fr` par l'adresse réelle (pages + `js/configurateur.js`).
4. Ajouter les visuels Open Graph dans `img/og/` (1200 × 630) : `atelier-brut-table-w.jpg`, `atelier-brut-collection.jpg`, `atelier-brut-configurateur.jpg`, `logo.png`.
5. Déclarer le sitemap dans Google Search Console.

## Images

- `img/pieces/<piece>-studio.jpg` — visuels produits (4:5). Rendus photoréalistes Cycles, à remplacer par les photos studio quand elles existent, **en gardant le même nom de fichier**.
- `img/spin/origine/frame-000.jpg … frame-035.jpg` — rotation 360° de la pièce signature (36 vues, 10° d'écart, sens horaire). Pour la remplacer par des photos sur plateau tournant : 36 clichés, même cadrage, même nom. Pour un autre nombre de vues, changer `data-frames` dans `index.html` et `collection.html`.
- `img/scenes/`, `img/potagers/` — mises en situation.
- `img/atelier/` — photos du prototype n°1.

Les scripts de rendu (Blender / Cycles) sont dans `render/` et se lancent avec `python3 render/tensegrite.py <variante> <dossier> [--spin 36] [--samples 40] [--res 1000 1250] [--scene studio|salon] [--shift -0.17]`.

## Structure

```
index.html            accueil (hero 360°, manifeste, collection, potagers, atelier, FAQ)
collection.html       les huit tables (toutes « épuisé »)
potagers.html         potagers suspendus
configurateur.html    configurateur sur-mesure (estimation + demande de devis)
atelier.html          storytelling
contact.html          contact / presse
mentions-legales.html
css/style.css         feuille de style unique
js/spin.js            visionneuse 360°
js/configurateur.js   logique du configurateur
js/site.js            menu mobile, lien courant, apparitions
```

## SEO

Balises title / description uniques, canonical, Open Graph, données structurées (Organization, WebSite, Product avec `availability: SoldOut`, ItemList, FAQPage, BreadcrumbList, Article), sitemap image, textes alternatifs descriptifs, URL propres, pages légères (aucune dépendance JS externe, polices Google uniquement).
