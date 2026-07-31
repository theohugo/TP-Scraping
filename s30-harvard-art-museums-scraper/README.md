# Harvard Art Museums scraper — cible S30

Travail de groupe (binome) de la formation "Web Scraping moderne et industrialisation"
(IPSSI, formateur Adrien Vossough) : **RAGUIN Hugo** (cible S30, ce dossier) et
**TALEB Amine** (cible S18,
[`../s18-greenkart-scraper`](../s18-greenkart-scraper)). Le detail du binome et des
fonctions partagees entre les deux collecteurs est dans [`../README.md`](../README.md) et
[`../commun/README.md`](../commun/README.md).

Cible attribuee a Hugo : **S30, Harvard Art Museums Collections**.

Les supports fournis par le formateur (`eleves/`, `MATRICE_CIBLES_ELEVES.html`) sont a la
racine du depot (`../eleves`, `../MATRICE_CIBLES_ELEVES.html`) ; le projet de collecte
lui-meme (`src/`, `verif/`, `docs/`) est decrit ci-dessous.

## Demarrage rapide

Toutes les commandes ci-dessous sont a executer depuis **ce dossier**
(`s30-harvard-art-museums-scraper/`).

```bash
# 1. Environnement
python -m venv .venv
.venv/Scripts/activate          # Windows ; sous Linux/Mac : source .venv/bin/activate
pip install -e ../commun        # package partage avec le collecteur S18 du binome
pip install -r requirements.txt

# 2. Collecte limitee (reseau requis)
PYTHONPATH=src python -m harvest.collect --max-items 20 --delay-s 1.5

# 3. Verification (aucun reseau requis)
python verif/verif.py
```

La collecte ecrit `data/artworks.jsonl` (non versionne) et met a jour
`samples/sample_output.json` (10 objets, versionne). La verification rejoue l'extraction sur
une page enregistree (`verif/fixtures/browse_page_sample.json`) et affiche `OK`/`ECHEC` sur
trois controles.

`config.example` documente les parametres modifiables (volume, delai, tentatives...) ; aucun
n'est un secret, la cible ne demande aucune authentification. Copiez-le en `.env` si besoin.

## Comment ca marche

La cible (`https://harvardartmuseums.org/collections`) est une SPA : le HTML initial ne
contient aucune oeuvre, seulement la coquille de la page. Le diagnostic complet (preuves a
l'appui : requetes `curl`, comparaison HTML/DOM, interception reseau Playwright) est dans
[`docs/cible.md`](docs/cible.md) ; en resume, la page appelle elle-meme au chargement un
endpoint JSON interne, `GET /browse?q=&offset=...&load_amount=...`, qui renvoie directement
tous les champs necessaires (titre, artiste(s), date, classification, medium, URL de fiche).
Le projet rejoue cet appel directement en HTTP, sans jamais ouvrir de navigateur pendant une
collecte reelle — Playwright n'a servi qu'une fois, pour le diagnostic.

Le flux de traitement, fichier par fichier :

```
config.py          Lit les parametres (HARVEST_*) depuis l'environnement.
      |
acquisition.py      Appelle /browse avec offset/load_amount ; retries bornes sur 429/5xx,
      |              respecte Retry-After, backoff exponentiel + gigue ; ne rejoue jamais
      |              un 401/403/404/410. Journalise chaque requete (log_event).
      v
extraction.py       Transforme un enregistrement JSON brut en objet Artwork : normalise les
      |              artistes (people -> liste de noms), les dates (bornes numeriques ou
      |              repli regex sur texte libre), l'URL (forme canonique). Un champ
      |              obligatoire absent (title, classification, url, object_id) fait rejeter
      |              l'objet -- proprement, journalise, sans planter la collecte.
      v
models.py           Le contrat Pydantic Artwork : valide les types, rejette un titre ou une
      |              classification vides.
      v
storage.py          Deduplique par object_id (identifiant stable du musee), puis exporte en
                     JSONL (data/artworks.jsonl) et un echantillon JSON (samples/).
```

`collect.py` orchestre les quatre etapes dans une boucle bornee (`while vus < max_items`) et
affiche un rapport final (vus / exportes / rejetes / doublons / champs manquants).

Depuis la fusion avec le collecteur S18 du binome, `acquisition.py` et `storage.py`
delegent la boucle de retry HTTP et la deduplication/export JSONL generiques au package
partage [`../commun`](../commun) (strictement identiques entre les deux projets) ; le reste
de ce flux (modele `Artwork`, normalisations, pagination `/browse`) reste propre a ce
projet. Voir [`../commun/README.md`](../commun/README.md) pour le detail.

## Choix techniques, et pourquoi

| Besoin | Choix retenu | Pourquoi | Alternative ecartee |
|---|---|---|---|
| Client HTTP | `httpx.Client` | Simple, deja pratique en TP module 02 ; timeouts et pool de connexions explicites ; une seule cible ne justifie pas plus. | **Scrapy** : inutile pour une cible unique sans arborescence de liens a crawler, et surtout *nommement bloque* par le `robots.txt` de la cible (voir `docs/cible.md` §1) — l'utiliser avec son User-Agent par defaut aurait ete exactement ce que l'enonce interdit. |
| Extraction | Fonctions Python pures (`extraction.py`) | La source est deja du JSON structure et type : aucun DOM a parser. | **BeautifulSoup / Parsel** : conçus pour extraire d'un arbre HTML ; sans objet, puisqu'il n'y a pas de HTML a lire ici. |
| Modele de donnees | **Pydantic** (`BaseModel`) | Validation stricte native (types, champ vide rejete) avec des messages d'erreur exploitables directement dans les logs. | **dataclass + validation manuelle** : aurait demande de reecrire a la main tout ce que Pydantic fournit deja. |
| Verification | Script autonome `verif.py` (assertions + `print OK/ECHEC`) | Aucune dependance supplementaire ; lisible et rejouable en une seule commande, sans reseau. | **pytest** : les deux comptent a egalite selon l'enonce ; un script simple evite d'ajouter une dependance de test pour seulement 3 controles. |
| Format de sortie | **JSONL** (un objet par ligne) | Ecriture au fil de l'eau, format recommande en cours pour une zone STAGING, lisible ligne par ligne. | **CSV** : ne peut pas representer proprement une liste (`artists`) ni distinguer `None` d'une chaine vide. |
| Navigateur | Playwright utilise **une seule fois**, en diagnostic, jamais en collecte reelle | Le cout d'un navigateur est un ordre de grandeur superieur (memoire, temps) a un simple appel HTTP, pour un resultat identique une fois l'endpoint reel identifie. | Piloter Playwright en continu pour chaque page : aurait fonctionne, mais inutilement lent et fragile. |
| Identifiant de deduplication | `object_id` (entier interne du musee) | Garanti unique et present, deja utilise dans l'URL de la fiche. | `object_number` (numero d'inventaire, ex. `1931.162.A`) : peut etre partage par plusieurs objets d'un meme lot (suffixes `.A`/`.B`), donc moins fiable comme cle. |

Le detail des deux decisions de conception les plus structurantes (avec leurs compromis
assumes) et l'ancrage justifie des deux champs les plus importants sont dans
[`docs/architecture.md`](docs/architecture.md).

## Structure du depot

```
src/harvest/        Code du collecteur (config, acquisition, extraction, models, storage, collect)
verif/               Script de verification + page de resultats enregistree (sans reseau)
samples/             Echantillon de sortie (10 objets), verse dans le depot
docs/                Fiche de cible avec preuves, architecture detaillee, usage de l'IA
data/                Sortie complete d'une collecte reelle (non versionne, genere localement)
../commun/           Package partage avec le collecteur S18 (retry HTTP, storage, .env)
../eleves/, ../MATRICE_CIBLES_ELEVES.html    Supports fournis par le formateur (racine du depot)
```

## Format de sortie

`data/artworks.jsonl` — un objet `Artwork` par ligne :

```json
{"object_id": 303387, "object_number": "1931.162.A", "title": "Lion", "artists": [], "date_text": "1500-1350 BCE", "date_begin": -1500, "date_end": -1350, "classification": "Sculpture", "medium": "Glazed terracotta", "url": "https://harvardartmuseums.org/collections/object/303387", "scraped_at": "2026-07-30T12:25:28.411380Z", "source": "http"}
```

## Limites connues

1. Le catalogue source (~250 000 objets) evolue en continu : un `object_id` collecte reste
   valide, mais l'objet correspondant peut etre republie ou retire entre deux collectes.
2. Le champ `people` (artistes) ne distingue pas encore tous les roles curatoriaux possibles
   (voir `_CREATION_ROLES` dans `extraction.py`) ; un role absent de la liste serait
   silencieusement exclu plutot que signale.
3. Le repli de date par expression reguliere (`parse_date_bounds`) ne reconnait qu'une
   premiere annee a 1-4 chiffres avec marqueur BCE/BC ; un format de date exotique renverrait
   `None, None` plutot qu'une valeur fausse, mais resterait non couvert.

## Usage responsable applique

- `robots.txt` lu integralement avant la premiere requete (voir `docs/cible.md` §1) : le
  fichier ne couvre, par son absence de groupe `*`, aucun client identifie distinctement --
  mais l'User-Agent du projet reste explicite et honnete, et ne se fait jamais passer pour un
  des robots listes.
- Une seule requete a la fois, delai minimum de 1,5 s entre deux appels (`HARVEST_DELAY_S`).
- Aucune authentification, aucune action irreversible, aucune donnee personnelle collectee.
- La cle d'API interne du musee, visible dans les reponses de l'endpoint utilise, n'est
  jamais lue ni transmise (voir note ethique dans `src/harvest/acquisition.py`).
- Voir [`docs/AI_USAGE.md`](docs/AI_USAGE.md) pour l'usage de l'IA sur ce projet.
