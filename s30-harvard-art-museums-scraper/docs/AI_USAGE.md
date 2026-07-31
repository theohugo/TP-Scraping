# Usage de l'IA — TP Harvard Art Museums (S30)

## Outil utilisé

Claude Code (Anthropic, agent en ligne de commande), sur toute la durée du projet.

## Usage principal : synthèse du cours et guidage d'architecture

- Avant de commencer le TP, synthèse des 8 modules de la formation *Web Scraping moderne et
  industrialisation* (échelle d'acquisition, ancrage des sélecteurs, séparation des
  responsabilités, contrat de données, formats de sortie, usage responsable), utilisée comme
  référence méthodologique pendant toute la conception.
- Guidage sur l'architecture à adopter pour la cible S30 : découpage en responsabilités
  (config / acquisition / extraction / modèle / stockage), choix du modèle de données
  `Artwork`, stratégie de vérification sans réseau — cohérents avec la méthode vue en cours.

## Deux exemples de demandes

1. « Résume la méthodologie du cours et aide-moi à structurer le projet S30 en respectant les
   responsabilités vues en cours. » → a produit le squelette de projet et le plan
   d'architecture repris dans [`docs/architecture.md`](architecture.md).
2. « Le `robots.txt` de la cible bloque nommément Scrapy : compare les options d'acquisition
   possibles. » → a mené à la comparaison documentée dans le README (`httpx` sur l'endpoint
   `/browse` plutôt que Scrapy ou Playwright en continu).

## Autres tâches réalisées avec l'IA

Au-delà du résumé de cours et du guidage d'architecture, l'IA a aussi participé à l'écriture
du code (`src/harvest/*.py`), du script de vérification et de la documentation, ainsi qu'à
l'exécution réelle de la collecte et de `verif/verif.py`.

## Ce qui a été vérifié

- Collecte exécutée en conditions réelles (pas seulement relue) : 60 objets vus, 60 exportés,
  0 rejeté, 0 doublon.
- `python verif/verif.py` exécuté, `OK` sur les trois contrôles, sans réseau.
- `robots.txt` récupéré et lu intégralement (pas seulement supposé) avant d'écrire
  [`docs/cible.md`](cible.md).

## Proposition corrigée ou refusée

Piste initialement envisagée : utiliser **Scrapy** pour l'acquisition, un framework vu en
cours. Écartée après lecture du `robots.txt` de la cible, qui bloque nommément ce framework
par son User-Agent par défaut — l'utiliser aurait été exactement le contournement que
l'énoncé interdit. Remplacée par `httpx` sur l'endpoint `/browse` identifié lors du
diagnostic (détail dans le README, table « Choix techniques, et pourquoi »).
