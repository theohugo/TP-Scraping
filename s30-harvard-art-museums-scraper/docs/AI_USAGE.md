# Usage de l'IA


## Outils utilises

- Claude Code (Anthropic, modele Sonnet 5), en ligne de commande.

## Usage principal : plan et methode

- En amont du TP, synthese des 8 modules du cours (`.claude/skills/scraping-ipssi/` dans le
  depot du cours), utilisee comme reference methodologique pendant toute la conception.
- Diagnostic de la cible S30 (voir `docs/cible.md`) : lecture de `robots.txt`, HTML initial
  (`curl`), interception reseau Playwright pour localiser l'endpoint `/browse` reellement
  utilise par la page -> a fixe le plan (HTTP direct sur l'endpoint plutot que Playwright
  permanent).
- Definition du plan de projet attendu par `ENONCE_TP.html` : structure de depot, modele de
  donnees avec regle d'absence, normalisations a justifier, strategie de verification sans
  reseau.

## Autres taches confiees

- Ecriture du code (`src/harvest/*.py`), du script de verification, et de la documentation.
- Execution reelle de la collecte (60 objets) et de `verif/verif.py`.

## Ce qui a ete verifie

- Collecte executee en conditions reelles (pas seulement relue) : 60 objets vus, 60 exportes,
  0 rejete, 0 doublon.
- `python verif/verif.py` execute, `OK` sur les trois controles, sans reseau.
- `robots.txt` recupere et lu integralement (pas seulement suppose) avant d'ecrire
  `docs/cible.md`.


## Si aucune IA n'avait ete utilisee

Sans objet : de l'IA a ete utilisee pour ce projet, comme indique ci-dessus.
