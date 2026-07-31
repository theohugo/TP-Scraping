# GreenKart scraper — cible S18

Travail de groupe (binôme) de la formation **Web Scraping moderne et industrialisation**
(IPSSI, formateur Romain VASSEUR) : **TALEB Amine** (cible S18, ce dossier) et **RAGUIN
Hugo** (cible S30, [`../s30-harvard-art-museums-scraper`](../s30-harvard-art-museums-scraper)).
Le détail du binôme et des fonctions partagées entre les deux collecteurs est dans
[`../README.md`](../README.md) et [`../commun/README.md`](../commun/README.md).

Cible attribuée à Amine : **S18 — GreenKart** (Rahul Shetty Academy),
`https://rahulshettyacademy.com/seleniumPractise/`.

## Cible et périmètre

- **Catalogue principal** : les 30 articles (fruits, légumes, fruits secs)
  publiés par le site, avec nom, prix, unité de vente et catégorie.
- **Complément demandé par la fiche de cible** : les offres de la page
  "Top Deals" (`#/offers`), 19 lignes sur 4 pages.
- Aucune page de détail, aucune pagination sur le catalogue principal
  (inventaire complet servi en un seul appel).
- Diagnostic complet, preuves et décisions d'architecture :
  [`docs/architecture.md`](docs/architecture.md).

## Prérequis

- Python >= 3.11
- Un navigateur Chromium pour Playwright (installé automatiquement, voir
  ci-dessous)
- Connexion internet (la cible est un site public réel, pas une stack
  locale)

## Installation

Ce projet dépend du package partagé `commun/` (racine du dépôt), qui factorise le retry
HTTP, la déduplication/export JSONL et le chargement du `.env` avec le collecteur S30 du
binôme — voir [`../commun/README.md`](../commun/README.md).

```bash
python -m venv .venv
# Windows : .venv\Scripts\Activate.ps1
# Linux/macOS : source .venv/bin/activate
pip install -e ../commun
pip install -e ".[dev]"
python -m playwright install chromium
```

## Lancer une collecte limitée

```bash
python -m greenkart_scraper.cli --catalog-limit 5 --max-offers-pages 1
```

## Lancer la collecte complète

```bash
python -m greenkart_scraper.cli
```

Sortie : `data/products.jsonl` (30 lignes) et `data/offers.jsonl` (19
lignes). Le résumé imprimé en fin d'exécution donne les compteurs vus /
exportés / rejetés / doublons pour chaque jeu de données.

Réglages (copier `config.example` en `.env` pour les ajuster) :
`GK_REQUEST_DELAY_S`, `GK_MAX_RETRIES`, `GK_MAX_OFFERS_PAGES`,
`GK_OUTPUT_DIR`.

## Vérification (sans réseau)

```bash
pytest
```

Douze tests, tous rejouables hors ligne sur les pages enregistrées dans
`tests/fixtures/` (copie de `data/products.json` et des lignes de la table
Top Deals, capturées le 2026-07-30) :

1. nombre d'objets extraits d'une page enregistrée (`test_build_product_count_matches_recorded_catalog`,
   `test_build_deal_count_matches_recorded_offers`) ;
2. normalisation prix et unité (`tests/test_normalize.py`) ;
3. déduplication et rejet d'un objet incomplet (`test_dedupe_by_sku_drops_duplicate_products`,
   `test_build_product_rejects_incomplete_record`).

## Architecture

Six responsabilités séparées : `config.py` (configuration),
`acquisition.py` (récupération brute — HTTP pour le catalogue, Playwright
pour Top Deals), `extraction.py` (extraction + normalisation + validation
Pydantic), `storage.py` (déduplication + export JSONL), `logging_conf.py`
(traces horodatées), `cli.py` (orchestration). Détail, schéma et preuves de
diagnostic : [`docs/architecture.md`](docs/architecture.md).

`http_client.py`, `storage.py` et le chargement du `.env` (`config.py`)
délèguent désormais au package partagé [`../commun`](../commun) : la boucle de
retry HTTP et la déduplication/export JSONL génériques sont strictement
identiques à celles du collecteur S30 du binôme, donc factorisées plutôt que
dupliquées. Les signatures publiques de ces modules sont inchangées ; le reste
(modèles, extraction, acquisition Playwright, CLI) reste propre à ce projet.

## Format de sortie

JSONL, un objet par ligne. `Product` : `sku, name, unit, quantity_step,
price, currency, category, image_url, url, scraped_at, source`. `Deal` :
`deal_id, name, price, discount_price, currency, page, url, scraped_at,
source`. Échantillon : [`samples/sample_output.json`](samples/sample_output.json).

## Limites connues

- `quantity_step` et `currency` sont des constantes documentées (voir
  `docs/architecture.md`), pas des valeurs extraites : le site ne les
  expose dans aucune des deux sources de données utilisées.
- Le catalogue est collecté via le fichier `data/products.json` plutôt que
  depuis le DOM : plus rapide et plus sûr (voir le piège du 31e élément
  `.product` documenté dans `docs/architecture.md`), mais si ce fichier
  disparaissait un jour au profit d'un rendu purement DOM, l'extracteur du
  catalogue devrait être réécrit en Playwright, sur le même modèle que celui
  de la table Top Deals.
- Aucune page de détail produit n'existe sur cette cible : rien à suivre
  au-delà du fichier catalogue et de la table d'offres.
- La table Top Deals ne porte aucun identifiant propre : `deal_id` est un
  slug du nom (règle documentée dans `contracts.py`), à surveiller si deux
  offres partageaient un jour le même nom.

## Usage responsable appliqué

- `robots.txt` lu avant toute collecte (`Disallow: /AutomationPractice/`,
  chemin hors périmètre ; voir `docs/architecture.md`).
- Un seul client HTTP réutilisé, `User-Agent` identifiant avec contact,
  délai configurable entre requêtes.
- Retries bornés (`GK_MAX_RETRIES`, défaut 3) et uniquement sur les statuts
  transitoires (408/429/5xx) ; un 4xx définitif n'est jamais rejoué.
- Aucune authentification, aucune donnée personnelle, aucune action
  irréversible (le panier de démonstration n'est jamais validé).
- Volume plafonné : 30 produits + 19 offres, sous le maximum de 31 indiqué
  par la fiche de cible.

## Usage de l'IA

Voir [`docs/AI_USAGE.md`](docs/AI_USAGE.md).
