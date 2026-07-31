# TP Scraping — travail de groupe

Formation *Web Scraping moderne et industrialisation* (IPSSI, formateur Adrien Vossough).
Travail de groupe : **TALEB Amine** et **RAGUIN Hugo**, chacun sur sa propre cible.

## Contenu du depot

| Dossier | Cible | Auteur | Documentation |
|---|---|---|---|
| [`s18-greenkart-scraper/`](s18-greenkart-scraper) | S18 — GreenKart (Rahul Shetty Academy) | TALEB Amine | [README](s18-greenkart-scraper/README.md) |
| [`s30-harvard-art-museums-scraper/`](s30-harvard-art-museums-scraper) | S30 — Harvard Art Museums Collections | RAGUIN Hugo | [README](s30-harvard-art-museums-scraper/README.md) |
| [`commun/`](commun) | Package partage par les deux collecteurs (retry HTTP, deduplication/export JSONL, chargement `.env`) | — | [README](commun/README.md) |
| `eleves/`, `MATRICE_CIBLES_ELEVES.html` | Supports fournis par le formateur | — | — |

## Structure

```
TP-Scraping/
  s18-greenkart-scraper/            Collecteur S18 — projet Python complet et independant
  s30-harvard-art-museums-scraper/  Collecteur S30 — projet Python complet et independant
  commun/                           Package partage (installe en editable par les deux projets)
  eleves/, MATRICE_CIBLES_ELEVES.html
```

Chaque collecteur a son propre `README.md`, ses propres dependances
(`requirements.txt`/`pyproject.toml`), ses propres tests/verification et sa propre
documentation de cible (`docs/`). Les deux installent `commun/` en mode editable
(`pip install -e ../commun`) — detail de ce qui est partage : [`commun/README.md`](commun/README.md).

## Demarrage rapide

Voir le README de chaque projet pour les commandes exactes d'installation, de collecte
limitee et de verification. En resume :

```powershell
cd s18-greenkart-scraper   # ou s30-harvard-art-museums-scraper
.venv\Scripts\Activate.ps1
pip install -e ../commun
pip install -e ".[dev]"    # ou : pip install -r requirements.txt
```
