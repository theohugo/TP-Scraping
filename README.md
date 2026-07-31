# TP Scraping — travail de groupe

Formation **Web Scraping moderne et industrialisation** — IPSSI.
Formateur : **Romain VASSEUR**.

Travail de groupe (binôme) : **TALEB Amine** et **RAGUIN Hugo**, chacun sur sa propre cible
attribuée.

## Contenu du dépôt

| Dossier | Cible | Auteur | Documentation |
|---|---|---|---|
| [`s18-greenkart-scraper/`](s18-greenkart-scraper) | S18 — GreenKart (Rahul Shetty Academy) | TALEB Amine | [README](s18-greenkart-scraper/README.md) |
| [`s30-harvard-art-museums-scraper/`](s30-harvard-art-museums-scraper) | S30 — Harvard Art Museums Collections | RAGUIN Hugo | [README](s30-harvard-art-museums-scraper/README.md) |
| [`commun/`](commun) | Package partagé par les deux collecteurs (retry HTTP, déduplication/export JSONL, chargement `.env`) | TALEB Amine, RAGUIN Hugo | [README](commun/README.md) |
| `eleves/`, `MATRICE_CIBLES_ELEVES.html` | Supports fournis par le formateur | — | — |

## Structure

```
TP-Scraping/
  s18-greenkart-scraper/            Collecteur S18 — projet Python complet et indépendant
  s30-harvard-art-museums-scraper/  Collecteur S30 — projet Python complet et indépendant
  commun/                           Package partagé (installé en editable par les deux projets)
  eleves/, MATRICE_CIBLES_ELEVES.html
```

Chaque collecteur a son propre `README.md`, ses propres dépendances
(`requirements.txt`/`pyproject.toml`), ses propres tests/vérification et sa propre
documentation de cible (`docs/`). Les deux installent `commun/` en mode editable
(`pip install -e ../commun`) — détail de ce qui est partagé : [`commun/README.md`](commun/README.md).

## Démarrage rapide

Voir le README de chaque projet pour les commandes exactes d'installation, de collecte
limitée et de vérification. En résumé :

```powershell
cd s18-greenkart-scraper   # ou s30-harvard-art-museums-scraper
.venv\Scripts\Activate.ps1
pip install -e ../commun
pip install -e ".[dev]"    # ou : pip install -r requirements.txt
```
