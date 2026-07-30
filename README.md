# TP Scraping — Hugo Raguin (S30 : Harvard Art Museums Collections)

TP individuel "Web Scraping moderne et industrialisation" (IPSSI, formateur Adrien Vossough) —
cible attribuee **S30 : Harvard Art Museums Collections**.

Ce depot contient aussi les supports fournis par le formateur (`eleves/`,
`MATRICE_CIBLES_ELEVES.html`) ; le projet de collecte lui-meme est decrit ci-dessous.

## Cible et perimetre

- URL de depart : https://harvardartmuseums.org/collections
- Objet collecte : `Artwork` (oeuvre du catalogue) — titre, artiste(s), date, classification,
  medium, URL de fiche.
- Volume : plafonne a 60 objets (plafond indique dans `MATRICE_CIBLES_ELEVES.md`, pas un
  objectif).
- Diagnostic complet, avec preuves : [`docs/cible.md`](docs/cible.md).

## Prerequis

- Python 3.12+
- Une connexion reseau pour la collecte reelle (la verification, elle, n'en a pas besoin)

## Installation

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows ; sous Linux/Mac : source .venv/bin/activate
pip install -r requirements.txt
```

Copiez `config.example` en `.env` si vous voulez modifier un parametre (aucune valeur du
fichier n'est un secret : la cible ne demande aucune authentification).

## Lancer une collecte limitee

```bash
PYTHONPATH=src python -m harvest.collect --max-items 20 --delay-s 1.5
```

Produit `data/artworks.jsonl` (un objet JSON valide par ligne) et met a jour
`samples/sample_output.json` (10 premiers objets, verse dans le depot).

## Executer la verification (sans reseau)

```bash
python verif/verif.py
```

Rejoue l'extraction sur une page de resultats enregistree (`verif/fixtures/browse_page_sample.json`)
et affiche `OK`/`ECHEC` sur trois controles : nombre d'objets extraits, normalisation de
date (repli sur texte libre + rejet de bornes incoherentes), deduplication par identifiant
stable.

## Architecture (detail : [`docs/architecture.md`](docs/architecture.md))

```
config.py (parametres) -> acquisition.py (appel /browse, retries) -> extraction.py (JSON -> Artwork)
    -> storage.py (dedup + export JSONL/JSON) ; chaque etape journalise en JSON sur stdout
```

Six responsabilites separees (config / acquisition / extraction+normalisation / modele et
validation / export / journalisation), sans framework d'orchestration : une seule cible, une
collecte bornee, un script suffit.

## Format de sortie

`data/artworks.jsonl` — un objet `Artwork` par ligne :

```json
{"object_id": 303387, "object_number": "1931.162.A", "title": "Lion", "artists": [], "date_text": "1500-1350 BCE", "date_begin": -1500, "date_end": -1350, "classification": "Sculpture", "medium": "Glazed terracotta", "url": "https://harvardartmuseums.org/collections/object/303387", "scraped_at": "2026-07-30T12:25:28.411380Z", "source": "http"}
```

## Limites connues

1. Le catalogue de reference (~250 000 objets) evolue en continu : les `object_id` collectes
   restent valides, mais un objet peut etre republie/retire entre deux collectes.
2. Le champ `people` (artistes) ne distingue pas encore tous les roles curatoriaux possibles
   (voir `_CREATION_ROLES` dans `extraction.py`) ; un role non liste serait silencieusement
   exclu de la liste d'artistes plutot que signale.
3. Le repli de date par expression reguliere (`parse_date_bounds`) ne gere qu'une premiere
   annee a 1-4 chiffres avec marqueur BCE/BC ; un format de date exotique du texte libre
   pourrait ne pas etre reconnu (retour `None, None`, jamais une valeur fausse).

## Usage responsable applique

- `robots.txt` lu integralement avant la premiere requete (voir `docs/cible.md` §1) : le
  fichier ne couvre, par son absence de groupe `*`, aucun client identifie distinctement —
  mais l'User-Agent du projet est neanmoins explicite et honnete, et ne se fait jamais passer
  pour un des robots listes.
- Une seule requete a la fois, delai minimum de 1,5 s entre deux appels (`HARVEST_DELAY_S`).
- Aucune authentification, aucune action irreversible, aucune donnee personnelle collectee.
- La cle d'API interne du musee, visible dans les reponses de l'endpoint utilise, n'est
  jamais lue ni transmise (voir note ethique dans `src/harvest/acquisition.py`).
- Voir [`docs/AI_USAGE.md`](docs/AI_USAGE.md) pour l'usage de l'IA sur ce projet.
