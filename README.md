# TP Scraping — travail de groupe (binome)

Travail de groupe de la formation *Web Scraping moderne et industrialisation* (IPSSI,
formateur Adrien Vossough), realise en binome : chacun garde sa cible individuelle, avec un
depot commun et des fonctions reellement partagees factorisees dans `commun/`.

- **TALEB Amine** — cible **S18, GreenKart** (Rahul Shetty Academy) :
  [`s18-greenkart-scraper/`](s18-greenkart-scraper)
- **RAGUIN Hugo** — cible **S30, Harvard Art Museums Collections** :
  [`s30-harvard-art-museums-scraper/`](s30-harvard-art-museums-scraper)
- **Package partage** entre les deux collecteurs (retry HTTP, deduplication/export JSONL,
  chargement du `.env`) : [`commun/`](commun)

## Structure du depot

```
TP-Scraping/
  s18-greenkart-scraper/            Collecteur S18 (Amine) — voir son README pour les commandes exactes
  s30-harvard-art-museums-scraper/  Collecteur S30 (Hugo) — voir son README pour les commandes exactes
  commun/                           Package partage par les deux collecteurs (voir son README)
  eleves/, MATRICE_CIBLES_ELEVES.html    Supports fournis par le formateur (inchanges)
```

Chaque collecteur (`s18-greenkart-scraper/`, `s30-harvard-art-museums-scraper/`) reste un
projet Python complet et independant : son propre `README.md`, ses propres dependances
(`requirements.txt`/`pyproject.toml`), ses propres tests/verification, sa propre
documentation de cible (`docs/`). La seule dependance croisee est explicite et volontaire :
les deux installent `commun/` en mode editable (`pip install -e ../commun`), qui factorise
uniquement ce qui etait strictement identique entre les deux projets — voir
[`commun/README.md`](commun/README.md) pour le detail exact de ce qui est partage et
pourquoi.

## Ce qui a change avec la fusion

Ce depot contenait a l'origine uniquement le travail individuel de Hugo (cible S30) a la
racine. Le formateur a autorise le travail en binome (chacun gardant sa propre cible) ; le
depot a ete reorganise en trois dossiers pour accueillir aussi le travail d'Amine (cible
S18), avec factorisation du code reellement duplique entre les deux projets :

- `s30-harvard-art-museums-scraper/` correspond exactement au contenu qui etait a la racine
  du depot (deplace, pas modifie sur le fond ; seuls `acquisition.py`, `storage.py` et
  `collect.py` ont ete adaptes pour deleguer au package `commun/`, sans changer leur
  signature ni leur comportement observable).
- `s18-greenkart-scraper/` reprend a l'identique le projet individuel d'Amine, avec la meme
  adaptation minimale (`http_client.py`, `storage.py`, `config.py`).
- Aucune modification du modele de donnees, de l'extraction, des normalisations ou de la CLI
  de l'un ou l'autre projet.
