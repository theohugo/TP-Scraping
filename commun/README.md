# commun — package partage entre les deux collecteurs du binome

Travail de groupe (binome) de la formation *Web Scraping moderne et industrialisation* :
**TALEB Amine** (cible S18, [`../s18-greenkart-scraper`](../s18-greenkart-scraper)) et
**RAGUIN Hugo** (cible S30, [`../s30-harvard-art-museums-scraper`](../s30-harvard-art-museums-scraper)).
Vue d'ensemble du binome : [`../README.md`](../README.md).

## Pourquoi ce dossier existe

En comparant les deux collecteurs (legumes GreenKart vs metadonnees d'oeuvres Harvard Art
Museums), deux morceaux de code se sont averes strictement identiques dans leur logique,
independamment du modele de donnees ou de la cible :

1. **Le retry HTTP** : les deux projets rejouaient une requete GET un nombre borne de fois
   sur les statuts transitoires (408/429/5xx), avec backoff exponentiel et gigue, sans
   jamais rejouer un statut definitif (401/403/404/410...).
2. **La deduplication et l'export JSONL** : les deux projets deduplicaient une liste
   d'objets Pydantic par une cle (SKU, deal_id ou object_id) et exportaient un objet JSON
   par ligne, plus un echantillon.
3. **Le chargement d'un fichier `.env`** : implemente cote S18 seulement ; en le deplacant
   ici, le collecteur S30 en beneficie aussi (son `config.example` disait deja "copiez en
   .env", sans que rien ne le charge reellement — corrige au passage).

Ce qui **reste volontairement separe** dans chaque projet : les modeles de donnees
(`Product`/`Deal` vs `Artwork`), l'extraction et les normalisations (aucun rapport entre un
prix de legume et une date d'oeuvre d'art), l'acquisition specifique (fichier JSON +
Playwright pour S18, endpoint `/browse` paginé pour S30), la journalisation (S18 = logs
texte horodates, S30 = evenements JSON structures : deux styles deja testes, aucune raison
de forcer l'un sur l'autre) et les deux CLI.

## Contenu

| Module | Fonctions | Utilise par |
|---|---|---|
| `http_client.py` | `fetch_with_retry(client, url, *, params, max_retries, delay_before_s, max_backoff_s, on_event)`, `RETRYABLE_STATUS`, `NON_RETRYABLE_STATUS`, `parse_retry_after` | `s18-greenkart-scraper/src/greenkart_scraper/http_client.py`, `s30-harvard-art-museums-scraper/src/harvest/acquisition.py` |
| `storage.py` | `dedupe(items, key)`, `write_jsonl(items, path)`, `write_json_sample(items, path, limit=10)` | `s18-greenkart-scraper/src/greenkart_scraper/storage.py`, `s30-harvard-art-museums-scraper/src/harvest/storage.py` |
| `config.py` | `load_env_file(path=".env")` | `s18-greenkart-scraper/src/greenkart_scraper/config.py`, `s30-harvard-art-museums-scraper/src/harvest/collect.py` |

`fetch_with_retry` ne decide jamais, a la place de l'appelant, de la conduite a tenir sur
un echec : il retourne la reponse HTTP en cas de succes, ou `None` sur un statut definitif,
un budget de tentatives epuise, ou une erreur de transport persistante. Chaque projet
adapte ensuite ce `None` a son propre contrat deja en place :
- cote S18, `fetch_with_retry` (dans `greenkart_scraper/http_client.py`) leve une exception
  si la reponse est `None` — un echec definitif doit produire un signal bruyant, jamais un
  catalogue silencieusement incomplet ;
- cote S30, `fetch_browse_page` (dans `harvest/acquisition.py`) retourne `None` et
  journalise un evenement — la boucle de collecte (`collect.py`) s'arrete alors proprement,
  sans planter.

Le callback optionnel `on_event(nom, payload)` de `fetch_with_retry` permet a chaque projet
de garder sa propre convention de journalisation (texte horodate cote S18, JSON structure
cote S30) sans dupliquer la boucle de retry elle-meme.

## Installation

Ce package n'est pas publie sur PyPI : il s'installe en mode editable, depuis chacun des
deux projets qui en dependent.

```bash
# Depuis s18-greenkart-scraper/ ou s30-harvard-art-museums-scraper/
pip install -e ../commun
```

## Verification

`commun` n'a pas sa propre suite de tests dediee : sa logique est couverte indirectement
par les verifications de chacun des deux projets (`pytest` cote S18, `python verif/verif.py`
cote S30), qui exercent `dedupe`/`write_jsonl` via leurs propres modeles (`Product`/`Deal`,
`Artwork`). Voir le README de chaque projet pour les commandes exactes.
