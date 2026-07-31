# GreenKart scraper — cible S18

Travail de groupe (binôme) de la formation **Web Scraping moderne et industrialisation**
(IPSSI, formateur Romain VASSEUR) : **TALEB Amine** (cible S18, ce dossier) et **RAGUIN
Hugo** (cible S30, [`../s30-harvard-art-museums-scraper`](../s30-harvard-art-museums-scraper)).
Le détail du binôme et des fonctions partagées entre les deux collecteurs est dans
[`../README.md`](../README.md) et [`../commun/README.md`](../commun/README.md).

Cible attribuée à Amine : **S18 — GreenKart** (Rahul Shetty Academy),
`https://rahulshettyacademy.com/seleniumPractise/`.

Les supports fournis par le formateur (`eleves/`, `MATRICE_CIBLES_ELEVES.html`) sont à la
racine du dépôt (`../eleves`, `../MATRICE_CIBLES_ELEVES.html`) ; le projet de collecte
lui-même (`src/`, `tests/`, `docs/`) est décrit ci-dessous.

## Démarrage rapide

Toutes les commandes ci-dessous sont à exécuter depuis **ce dossier**
(`s18-greenkart-scraper/`). Prérequis : Python >= 3.11, un navigateur Chromium pour
Playwright (installé ci-dessous), une connexion internet (la cible est un site public réel,
pas une stack locale).

```bash
# 1. Environnement
python -m venv .venv
.venv/Scripts/activate          # Windows ; sous Linux/Mac : source .venv/bin/activate
pip install -e ../commun        # package partagé avec le collecteur S30 du binôme
pip install -e ".[dev]"
python -m playwright install chromium

# 2. Collecte limitée (réseau requis)
python -m greenkart_scraper.cli --catalog-limit 5 --max-offers-pages 1

# 3. Vérification (aucun réseau requis)
pytest
```

La collecte complète (`python -m greenkart_scraper.cli`, sans option) écrit
`data/products.jsonl` (30 lignes) et `data/offers.jsonl` (19 lignes), non versionnés. Le
résumé imprimé en fin d'exécution donne les compteurs vus / exportés / rejetés / doublons
pour chaque jeu de données.

`config.example` documente les paramètres modifiables (`GK_REQUEST_DELAY_S`,
`GK_MAX_RETRIES`, `GK_MAX_OFFERS_PAGES`, `GK_OUTPUT_DIR`) ; aucun n'est un secret, la cible
ne demande aucune authentification. Copiez-le en `.env` si besoin.

## Comment ça marche

La cible (`https://rahulshettyacademy.com/seleniumPractise/`) est une SPA React : le HTML
initial ne contient aucun produit, seulement la coquille de la page. Le diagnostic complet
(preuves à l'appui : requêtes `curl`, comparaison HTML/DOM, lecture du bundle JS) est dans
[`docs/architecture.md`](docs/architecture.md) ; en résumé, le catalogue (30 articles) est
servi par un fichier JSON statique (`data/products.json`), rejoué directement en HTTP,
tandis que la table "Top Deals" (page `#/offers`, 19 lignes sur 4 pages) n'a aucun endpoint
JSON équivalent : elle est peuplée par React depuis des données embarquées dans le bundle,
sans appel réseau observable. Un navigateur (Playwright) est donc utilisé pour cette seule
partie de la collecte — pas par confort, faute d'alternative HTTP qui fonctionne.

Le flux de traitement, fichier par fichier :

```
config.py           Lit les paramètres (GK_*) depuis l'environnement, charge le .env.
      |
acquisition.py       Catalogue : GET data/products.json (httpx, retries bornés). Top Deals :
      |               navigateur Playwright, budget de pages dur, arrêt sur lien "Next" désactivé.
      v
extraction.py        Transforme un enregistrement brut en Product ou Deal : normalise le nom
      |               et l'unité de vente (normalize.py), le prix, résout l'URL d'image. Un
      |               champ obligatoire absent ou invalide fait rejeter l'objet -- proprement,
      |               journalisé, sans planter la collecte.
      v
contracts.py          Les contrats Pydantic Product et Deal : valide les types, rejette un
      |               prix illisible ou une unité inconnue.
      v
storage.py            Déduplique par sku / deal_id, puis exporte en JSONL
                      (data/products.jsonl, data/offers.jsonl).
```

`cli.py` orchestre les deux collectes (catalogue puis Top Deals) et affiche un résumé final
(vus / exportés / rejetés / doublons) pour chaque jeu de données.

`http_client.py`, `storage.py` et le chargement du `.env` (`config.py`) délèguent au package
partagé [`../commun`](../commun) : la boucle de retry HTTP et la déduplication/export JSONL
génériques sont strictement identiques à celles du collecteur S30 du binôme, donc
factorisées plutôt que dupliquées. Les signatures publiques de ces modules sont inchangées ;
le reste (modèles, extraction, acquisition Playwright, CLI) reste propre à ce projet. Voir
[`../commun/README.md`](../commun/README.md) pour le détail.

## Choix techniques, et pourquoi

| Besoin | Choix retenu | Pourquoi | Alternative écartée |
|---|---|---|---|
| Client HTTP (catalogue) | `httpx.Client` | Un seul GET sur un fichier JSON statique ; retries bornés et backoff déjà nécessaires (module 02/04) ; une cible unique ne justifie pas plus. | **Scrapy** : pensé pour crawler une arborescence de liens ; ici aucune pagination ni page de détail à suivre, une seule requête suffit. |
| Acquisition Top Deals | **Playwright** (navigateur) | Capture réseau complète pendant le rendu de `#/offers` (diagnostic) : aucun endpoint JSON n'existe pour cette table, elle est peuplée côté client sans appel réseau. Le navigateur est la seule option qui fonctionne ici. | Rejouer un appel HTTP équivalent : impossible, aucun endpoint public n'a été trouvé (voir `docs/architecture.md`). |
| Extraction du catalogue | Lecture directe de `data/products.json`, pas le DOM | Le fichier expose 30 fiches propres ; le DOM expose la même donnée mais avec un piège (31e élément `.product` = widget panier, voir Limites connues). | **Parser le DOM rendu** (locators Playwright) : fonctionnerait, mais expose au faux 31e "produit" et impose un navigateur pour une donnée déjà disponible en JSON. |
| Modèle de données | **Pydantic** (`BaseModel`) | Validation stricte native (types, `Literal` pour l'unité, `HttpUrl`), rejet journalisé d'un champ manquant ou invalide, sans enregistrement silencieusement incomplet. | **dataclass + validation manuelle** : aurait demandé de réécrire à la main les contrôles que Pydantic fournit déjà. |
| Vérification | **pytest** (12 tests) | Déjà pratiqué en TP, fixtures (`conftest.py`) réutilisables proprement entre plusieurs tests, rapports d'échec détaillés. | **Script `verif.py` autonome** : les deux comptent à égalité selon l'énoncé ; pytest a été préféré ici pour la lisibilité des fixtures partagées. |
| Format de sortie | **JSONL** (un objet par ligne) | Écriture au fil de l'eau, lisible ligne par ligne, cohérent avec le format retenu par le collecteur S30 du binôme. | **CSV** : ne distingue pas proprement une valeur absente d'une chaîne vide, et complique un futur champ liste. |
| Identifiant de déduplication | `sku` (`GK-{id}`) pour Product, `deal_id` (slug du nom) pour Deal | `sku` dérive du champ `id` du fichier JSON, stable et garanti unique. `deal_id` est construit par slug faute d'identifiant exposé par la table Top Deals. | Position dans la liste (index) : casserait silencieusement si le site réordonne le catalogue sans changer les `id`. |

Le détail des décisions de conception les plus structurantes (fichier JSON plutôt que DOM
pour le catalogue, deux objets métier distincts `Product`/`Deal`) et l'ancrage justifié des
deux champs les plus importants sont dans [`docs/architecture.md`](docs/architecture.md).

## Structure du dépôt

```
src/greenkart_scraper/   Code du collecteur (config, acquisition, extraction, contracts,
                         normalize, storage, http_client, logging_conf, cli)
tests/                   Suite pytest (12 tests) + fixtures enregistrées (sans réseau)
samples/                 Échantillon de sortie (5 produits + 5 offres), versé dans le dépôt
docs/                    Diagnostic avec preuves, architecture détaillée, usage de l'IA
data/                    Sortie complète d'une collecte réelle (non versionné, généré localement)
../commun/               Package partagé avec le collecteur S30 (retry HTTP, storage, .env)
../eleves/, ../MATRICE_CIBLES_ELEVES.html    Supports fournis par le formateur (racine du dépôt)
```

## Format de sortie

JSONL, un objet par ligne.

`Product` : `sku, name, unit, quantity_step, price, currency, category, image_url, url,
scraped_at, source`.

```json
{"sku": "GK-001", "name": "Brocolli", "unit": "kg", "quantity_step": 1, "price": "120", "currency": "INR", "category": "vegetables", "image_url": "https://rahulshettyacademy.com/seleniumPractise/images/broccoli.jpg", "url": "https://rahulshettyacademy.com/seleniumPractise/#/", "scraped_at": "2026-07-30T12:25:53.378055Z", "source": "api"}
```

`Deal` : `deal_id, name, price, discount_price, currency, page, url, scraped_at, source`.

```json
{"deal_id": "wheat", "name": "Wheat", "price": "67", "discount_price": "28", "currency": "INR", "page": 1, "url": "https://rahulshettyacademy.com/seleniumPractise/#/offers", "scraped_at": "2026-07-30T12:25:57.555968Z", "source": "browser"}
```

Échantillon complet : [`samples/sample_output.json`](samples/sample_output.json).

## Limites connues

1. `quantity_step` et `currency` sont des constantes documentées (voir
   `docs/architecture.md`), pas des valeurs extraites : le site ne les expose dans aucune
   des deux sources de données utilisées.
2. Le catalogue est collecté via le fichier `data/products.json` plutôt que depuis le DOM :
   plus rapide et plus sûr (voir le piège du 31e élément `.product` documenté dans
   `docs/architecture.md`), mais si ce fichier disparaissait un jour au profit d'un rendu
   purement DOM, l'extracteur du catalogue devrait être réécrit en Playwright, sur le même
   modèle que celui de la table Top Deals.
3. Aucune page de détail produit n'existe sur cette cible : rien à suivre au-delà du fichier
   catalogue et de la table d'offres.
4. La table Top Deals ne porte aucun identifiant propre : `deal_id` est un slug du nom
   (règle documentée dans `contracts.py`), à surveiller si deux offres partageaient un jour
   le même nom.

## Usage responsable appliqué

- `robots.txt` lu avant toute collecte (`Disallow: /AutomationPractice/`, chemin hors
  périmètre ; voir `docs/architecture.md`).
- Un seul client HTTP réutilisé, `User-Agent` identifiant avec contact, délai configurable
  entre requêtes.
- Retries bornés (`GK_MAX_RETRIES`, défaut 3) et uniquement sur les statuts transitoires
  (408/429/5xx) ; un 4xx définitif n'est jamais rejoué.
- Aucune authentification, aucune donnée personnelle, aucune action irréversible (le panier
  de démonstration n'est jamais validé).
- Volume plafonné : 30 produits + 19 offres, sous le maximum de 31 indiqué par la fiche de
  cible.

## Usage de l'IA

Voir [`docs/AI_USAGE.md`](docs/AI_USAGE.md).
