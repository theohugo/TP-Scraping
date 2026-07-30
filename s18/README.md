# GreenKart scraper (cible S18)

TP individuel de la formation *Web Scraping moderne et industrialisation*.
Cible attribuee : **S18 — GreenKart** (Rahul Shetty Academy),
`https://rahulshettyacademy.com/seleniumPractise/`.

## Cible et perimetre

- **Catalogue principal** : les 30 articles (fruits, legumes, fruits secs)
  publies par le site, avec nom, prix, unite de vente et categorie.
- **Complement demande par la fiche de cible** : les offres de la page
  "Top Deals" (`#/offers`), 19 lignes sur 4 pages.
- Aucune page de detail, aucune pagination sur le catalogue principal
  (inventaire complet servi en un seul appel).
- Diagnostic complet, preuves et decisions d'architecture :
  [`docs/architecture.md`](docs/architecture.md).

## Prerequis

- Python >= 3.11
- Un navigateur Chromium pour Playwright (installe automatiquement, voir
  ci-dessous)
- Connexion internet (la cible est un site public reel, pas une stack
  locale)

## Installation

```bash
python -m venv .venv
# Windows : .venv\Scripts\Activate.ps1
# Linux/macOS : source .venv/bin/activate
pip install -e ".[dev]"
python -m playwright install chromium
```

## Lancer une collecte limitee

```bash
python -m greenkart_scraper.cli --catalog-limit 5 --max-offers-pages 1
```

## Lancer la collecte complete

```bash
python -m greenkart_scraper.cli
```

Sortie : `data/products.jsonl` (30 lignes) et `data/offers.jsonl` (19
lignes). Le resume imprime en fin d'execution donne les compteurs vus /
exportes / rejetes / doublons pour chaque jeu de donnees.

Reglages (copier `config.example` en `.env` pour les ajuster) :
`GK_REQUEST_DELAY_S`, `GK_MAX_RETRIES`, `GK_MAX_OFFERS_PAGES`,
`GK_OUTPUT_DIR`.

## Verification (sans reseau)

```bash
pytest
```

Douze tests, tous rejouables hors ligne sur les pages enregistrees dans
`tests/fixtures/` (copie de `data/products.json` et des lignes de la table
Top Deals, capturees le 2026-07-30) :

1. nombre d'objets extraits d'une page enregistree (`test_build_product_count_matches_recorded_catalog`,
   `test_build_deal_count_matches_recorded_offers`) ;
2. normalisation prix et unite (`tests/test_normalize.py`) ;
3. deduplication et rejet d'un objet incomplet (`test_dedupe_by_sku_drops_duplicate_products`,
   `test_build_product_rejects_incomplete_record`).

## Architecture

Six responsabilites separees : `config.py` (configuration),
`acquisition.py` (recuperation brute — HTTP pour le catalogue, Playwright
pour Top Deals), `extraction.py` (extraction + normalisation + validation
Pydantic), `storage.py` (deduplication + export JSONL), `logging_conf.py`
(traces horodatees), `cli.py` (orchestration). Detail, schema et preuves de
diagnostic : [`docs/architecture.md`](docs/architecture.md).

## Format de sortie

JSONL, un objet par ligne. `Product` : `sku, name, unit, quantity_step,
price, currency, category, image_url, url, scraped_at, source`. `Deal` :
`deal_id, name, price, discount_price, currency, page, url, scraped_at,
source`. Echantillon : [`samples/sample_output.json`](samples/sample_output.json).

## Limites connues

- `quantity_step` et `currency` sont des constantes documentees (voir
  `docs/architecture.md`), pas des valeurs extraites : le site ne les
  expose dans aucune des deux sources de donnees utilisees.
- Le catalogue est collecte via le fichier `data/products.json` plutot que
  depuis le DOM : plus rapide et plus sur (voir le piege du 31e element
  `.product` documente dans `docs/architecture.md`), mais si ce fichier
  disparaissait un jour au profit d'un rendu purement DOM, l'extracteur du
  catalogue devrait etre reecrit en Playwright, sur le meme modele que celui
  de la table Top Deals.
  <!-- amelioration prioritaire si je disposais d'une demi-journee de plus :
       ajouter un extracteur DOM de repli (Playwright) pour le catalogue,
       qui prendrait le relais si data/products.json cessait de repondre.
       C'est la limite la plus probable a moyen terme : c'est un fichier
       decouvert par retro-ingenierie du bundle JS, pas un contrat documente. -->
- Aucune page de detail produit n'existe sur cette cible : rien a suivre
  au-dela du fichier catalogue et de la table d'offres.
- La table Top Deals ne porte aucun identifiant propre : `deal_id` est un
  slug du nom (regle documentee dans `contracts.py`), a surveiller si deux
  offres partageaient un jour le meme nom.

## Usage responsable applique

- `robots.txt` lu avant toute collecte (`Disallow: /AutomationPractice/`,
  chemin hors perimetre ; voir `docs/architecture.md`).
- Un seul client HTTP reutilise, `User-Agent` identifiant avec contact,
  delai configurable entre requêtes.
- Retries bornes (`GK_MAX_RETRIES`, defaut 3) et uniquement sur les statuts
  transitoires (408/429/5xx) ; un 4xx definitif n'est jamais rejoue.
- Aucune authentification, aucune donnee personnelle, aucune action
  irreversible (le panier de demonstration n'est jamais valide).
- Volume plafonne : 30 produits + 19 offres, sous le maximum de 31 indique
  par la fiche de cible.

## Usage de l'IA

Voir [`docs/AI_USAGE.md`](docs/AI_USAGE.md).
