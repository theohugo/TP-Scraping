# Usage de l'IA

> **A lire avant de rendre :** ce fichier a ete redige avec Claude Code pendant la construction
> du projet. Les parties factuelles (outils, taches) sont exactes. Les parties marquees
> `[HUGO : ...]` doivent etre completees ou confirmees personnellement apres relecture du
> code — la declaration de fin de rapport ("je peux expliquer et modifier le code remis")
> porte sur toi, pas sur l'outil.

## Outils utilises

- Claude Code (Anthropic, modele Sonnet 5), en ligne de commande.

## Taches confiees

- Diagnostic de la cible S30 : lecture de `robots.txt`, recuperation du HTML initial (`curl`),
  puis interception reseau avec Playwright pour identifier l'appel JSON reellement declenche
  par la page `/collections` (voir `docs/cible.md`).
- Ecriture du code (`src/harvest/*.py`), du script de verification (`verif/verif.py` et sa
  page enregistree), et de la documentation (`README.md`, `docs/architecture.md`,
  `docs/cible.md`).
- Execution reelle de la collecte (60 objets) et du script de verification, pour produire
  `data/artworks.jsonl`, `samples/sample_output.json` et confirmer que les trois controles
  passent.
- Construction, en amont de ce TP, d'une synthese des 8 modules du cours (`.claude/skills/
  scraping-ipssi/` dans le depot du cours) utilisee comme reference methodologique pendant
  la conception de ce projet.

## Deux demandes significatives

1. « Diagnostique la cible S30 (Harvard Art Museums Collections) : trouve ou se trouvent
   reellement les donnees, sans supposer qu'il faut un navigateur avant de l'avoir prouve. »
   -> a mene a la decouverte de l'endpoint `/browse`, moins couteux qu'un pilotage Playwright
   permanent.
2. « Construis le projet complet attendu par ENONCE_TP.html : structure de depot, modele de
   donnees avec regle d'absence, trois normalisations justifiees, script de verification sans
   reseau, documentation. »

## Verifications reellement effectuees (par l'IA, pendant la construction)

- La collecte a ete executee en conditions reelles contre le site (pas seulement relue) :
  60 objets vus, 60 exportes, 0 rejete, 0 doublon (traces dans les logs et dans
  `data/artworks.jsonl`, non versionne).
- `python verif/verif.py` a ete execute et affiche `OK` sur les trois controles, sans reseau.
- Le fichier `robots.txt` a ete recupere et lu integralement (pas seulement suppose) avant
  d'ecrire `docs/cible.md`.

## Une proposition envisagee et ecartee (par l'IA, a documenter/valider par Hugo)

En inspectant la reponse de `/browse`, le champ `info.next` expose une URL vers l'API
publique du musee (`api.harvardartmuseums.org`) **avec une cle d'API valide en clair**. Il
aurait ete plus simple d'utiliser directement cette cle pour interroger l'API documentee.
Cette option a ete ecartee : la cle appartient au musee, pas au projet, et l'utiliser sans
autorisation ne semblait pas defendable — meme techniquement accessible. Le projet se limite
donc a rejouer l'appel `/browse` tel que la page elle-meme l'utilise, sans jamais lire ni
transporter cette cle.

`[HUGO : apres relecture du code (src/harvest/acquisition.py, note en tete de fichier, et
docs/cible.md section 3), confirmes-tu cette decision, ou l'aurais-tu prise differemment ?
Si tu as toi-meme corrige ou refuse une autre proposition en relisant le code, remplace cet
exemple par le tien — c'est ce qui est evalue ici, pas la decision de l'IA.]`

## Si aucune IA n'avait ete utilisee

Sans objet : de l'IA a ete utilisee pour ce projet, comme indique ci-dessus.
