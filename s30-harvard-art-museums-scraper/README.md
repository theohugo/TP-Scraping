# Harvard Art Museums scraper — cible S30

Travail de groupe (binôme) de la formation "Web Scraping moderne et industrialisation"
(IPSSI, formateur Romain VASSEUR) : **RAGUIN Hugo** (cible S30, ce dossier) et
**TALEB Amine** (cible S18,
[`../s18-greenkart-scraper`](../s18-greenkart-scraper)). Le détail du binôme et des
fonctions partagées entre les deux collecteurs est dans [`../README.md`](../README.md) et
[`../commun/README.md`](../commun/README.md).

Cible attribuée à Hugo : **S30, Harvard Art Museums Collections**.

Les supports fournis par le formateur (`eleves/`, `MATRICE_CIBLES_ELEVES.html`) sont à la
racine du dépôt (`../eleves`, `../MATRICE_CIBLES_ELEVES.html`) ; le projet de collecte
lui-même (`src/`, `verif/`, `docs/`) est décrit ci-dessous.

## Démarrage rapide

Toutes les commandes ci-dessous sont à exécuter depuis **ce dossier**
(`s30-harvard-art-museums-scraper/`).

```bash
# 1. Environnement
python -m venv .venv
.venv/Scripts/activate          # Windows ; sous Linux/Mac : source .venv/bin/activate
pip install -e ../commun        # package partagé avec le collecteur S18 du binôme
pip install -r requirements.txt

# 2. Collecte limitée (réseau requis)
PYTHONPATH=src python -m harvest.collect --max-items 20 --delay-s 1.5

# 3. Vérification (aucun réseau requis)
python verif/verif.py
```

La collecte écrit `data/artworks.jsonl` (non versionné) et met à jour
`samples/sample_output.json` (10 objets, versionné). La vérification rejoue l'extraction sur
une page enregistrée (`verif/fixtures/browse_page_sample.json`) et affiche `OK`/`ECHEC` sur
trois contrôles.

`config.example` documente les paramètres modifiables (volume, délai, tentatives...) ; aucun
n'est un secret, la cible ne demande aucune authentification. Copiez-le en `.env` si besoin.

## Comment ça marche

La cible (`https://harvardartmuseums.org/collections`) est une SPA : le HTML initial ne
contient aucune œuvre, seulement la coquille de la page. Le diagnostic complet (preuves à
l'appui : requêtes `curl`, comparaison HTML/DOM, interception réseau Playwright) est dans
[`docs/cible.md`](docs/cible.md) ; en résumé, la page appelle elle-même au chargement un
endpoint JSON interne, `GET /browse?q=&offset=...&load_amount=...`, qui renvoie directement
tous les champs nécessaires (titre, artiste(s), date, classification, medium, URL de fiche).
Le projet rejoue cet appel directement en HTTP, sans jamais ouvrir de navigateur pendant une
collecte réelle — Playwright n'a servi qu'une fois, pour le diagnostic.

Le flux de traitement, fichier par fichier :

```
config.py          Lit les paramètres (HARVEST_*) depuis l'environnement.
      |
acquisition.py      Appelle /browse avec offset/load_amount ; retries bornés sur 429/5xx,
      |              respecte Retry-After, backoff exponentiel + gigue ; ne rejoue jamais
      |              un 401/403/404/410. Journalise chaque requête (log_event).
      v
extraction.py       Transforme un enregistrement JSON brut en objet Artwork : normalise les
      |              artistes (people -> liste de noms), les dates (bornes numériques ou
      |              repli regex sur texte libre), l'URL (forme canonique). Un champ
      |              obligatoire absent (title, classification, url, object_id) fait rejeter
      |              l'objet -- proprement, journalisé, sans planter la collecte.
      v
models.py           Le contrat Pydantic Artwork : valide les types, rejette un titre ou une
      |              classification vides.
      v
storage.py          Déduplique par object_id (identifiant stable du musée), puis exporte en
                     JSONL (data/artworks.jsonl) et un échantillon JSON (samples/).
```

`collect.py` orchestre les quatre étapes dans une boucle bornée (`while vus < max_items`) et
affiche un rapport final (vus / exportés / rejetés / doublons / champs manquants).

Depuis la fusion avec le collecteur S18 du binôme, `acquisition.py` et `storage.py`
délèguent la boucle de retry HTTP et la déduplication/export JSONL génériques au package
partagé [`../commun`](../commun) (strictement identiques entre les deux projets) ; le reste
de ce flux (modèle `Artwork`, normalisations, pagination `/browse`) reste propre à ce
projet. Voir [`../commun/README.md`](../commun/README.md) pour le détail.

## Choix techniques, et pourquoi

| Besoin | Choix retenu | Pourquoi | Alternative écartée |
|---|---|---|---|
| Client HTTP | `httpx.Client` | Simple, déjà pratiqué en TP module 02 ; timeouts et pool de connexions explicites ; une seule cible ne justifie pas plus. | **Scrapy** : inutile pour une cible unique sans arborescence de liens à crawler, et surtout *nommément bloqué* par le `robots.txt` de la cible (voir `docs/cible.md` §1) — l'utiliser avec son User-Agent par défaut aurait été exactement ce que l'énoncé interdit. |
| Extraction | Fonctions Python pures (`extraction.py`) | La source est déjà du JSON structuré et typé : aucun DOM à parser. | **BeautifulSoup / Parsel** : conçus pour extraire d'un arbre HTML ; sans objet, puisqu'il n'y a pas de HTML à lire ici. |
| Modèle de données | **Pydantic** (`BaseModel`) | Validation stricte native (types, champ vide rejeté) avec des messages d'erreur exploitables directement dans les logs. | **dataclass + validation manuelle** : aurait demandé de réécrire à la main tout ce que Pydantic fournit déjà. |
| Vérification | Script autonome `verif.py` (assertions + `print OK/ECHEC`) | Aucune dépendance supplémentaire ; lisible et rejouable en une seule commande, sans réseau. | **pytest** : les deux comptent à égalité selon l'énoncé ; un script simple évite d'ajouter une dépendance de test pour seulement 3 contrôles. |
| Format de sortie | **JSONL** (un objet par ligne) | Écriture au fil de l'eau, format recommandé en cours pour une zone STAGING, lisible ligne par ligne. | **CSV** : ne peut pas représenter proprement une liste (`artists`) ni distinguer `None` d'une chaîne vide. |
| Navigateur | Playwright utilisé **une seule fois**, en diagnostic, jamais en collecte réelle | Le coût d'un navigateur est un ordre de grandeur supérieur (mémoire, temps) à un simple appel HTTP, pour un résultat identique une fois l'endpoint réel identifié. | Piloter Playwright en continu pour chaque page : aurait fonctionné, mais inutilement lent et fragile. |
| Identifiant de déduplication | `object_id` (entier interne du musée) | Garanti unique et présent, déjà utilisé dans l'URL de la fiche. | `object_number` (numéro d'inventaire, ex. `1931.162.A`) : peut être partagé par plusieurs objets d'un même lot (suffixes `.A`/`.B`), donc moins fiable comme clé. |

Le détail des deux décisions de conception les plus structurantes (avec leurs compromis
assumés) et l'ancrage justifié des deux champs les plus importants sont dans
[`docs/architecture.md`](docs/architecture.md).

## Structure du dépôt

```
src/harvest/        Code du collecteur (config, acquisition, extraction, models, storage, collect)
verif/               Script de vérification + page de résultats enregistrée (sans réseau)
samples/             Échantillon de sortie (10 objets), versé dans le dépôt
docs/                Fiche de cible avec preuves, architecture détaillée, usage de l'IA
data/                Sortie complète d'une collecte réelle (non versionné, généré localement)
../commun/           Package partagé avec le collecteur S18 (retry HTTP, storage, .env)
../eleves/, ../MATRICE_CIBLES_ELEVES.html    Supports fournis par le formateur (racine du dépôt)
```

## Format de sortie

`data/artworks.jsonl` — un objet `Artwork` par ligne :

```json
{"object_id": 303387, "object_number": "1931.162.A", "title": "Lion", "artists": [], "date_text": "1500-1350 BCE", "date_begin": -1500, "date_end": -1350, "classification": "Sculpture", "medium": "Glazed terracotta", "url": "https://harvardartmuseums.org/collections/object/303387", "scraped_at": "2026-07-30T12:25:28.411380Z", "source": "http"}
```

## Limites connues

1. Le catalogue source (~250 000 objets) évolue en continu : un `object_id` collecté reste
   valide, mais l'objet correspondant peut être republié ou retiré entre deux collectes.
2. Le champ `people` (artistes) ne distingue pas encore tous les rôles curatoriaux possibles
   (voir `_CREATION_ROLES` dans `extraction.py`) ; un rôle absent de la liste serait
   silencieusement exclu plutôt que signalé.
3. Le repli de date par expression régulière (`parse_date_bounds`) ne reconnaît qu'une
   première année à 1-4 chiffres avec marqueur BCE/BC ; un format de date exotique renverrait
   `None, None` plutôt qu'une valeur fausse, mais resterait non couvert.

## Usage responsable appliqué

- `robots.txt` lu intégralement avant la première requête (voir `docs/cible.md` §1) : le
  fichier ne couvre, par son absence de groupe `*`, aucun client identifié distinctement --
  mais l'User-Agent du projet reste explicite et honnête, et ne se fait jamais passer pour un
  des robots listés.
- Une seule requête à la fois, délai minimum de 1,5 s entre deux appels (`HARVEST_DELAY_S`).
- Aucune authentification, aucune action irréversible, aucune donnée personnelle collectée.
- La clé d'API interne du musée, visible dans les réponses de l'endpoint utilisé, n'est
  jamais lue ni transmise (voir note éthique dans `src/harvest/acquisition.py`).
- Voir [`docs/AI_USAGE.md`](docs/AI_USAGE.md) pour l'usage de l'IA sur ce projet.
