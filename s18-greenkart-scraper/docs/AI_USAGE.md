# Usage de l'IA — TP GreenKart (S18)

## Outil utilisé

Claude Code (Anthropic, agent en ligne de commande), sur toute la durée du projet.

## Usage principal : synthèse du cours et guidage d'architecture

- Avant de commencer le TP, analyse des modules et labs de la formation *Web Scraping
  moderne et industrialisation* pour en extraire la méthodologie (échelle d'acquisition,
  ancrage des sélecteurs, séparation des responsabilités, contrat de données, formats de
  sortie), utilisée comme référence pendant toute la conception.
- Guidage sur l'architecture retenue pour la cible S18 : découpage en six responsabilités,
  choix des deux objets métier `Product` / `Deal`, stratégie de vérification sans réseau —
  cohérents avec la méthode vue en cours.

## Deux exemples de demandes

1. « Analyse la méthodologie du cours puis aide-moi à structurer le projet S18 en respectant
   les responsabilités vues en cours. » → a produit le squelette de projet et le plan
   d'architecture repris dans [`docs/architecture.md`](architecture.md).
2. « Vérifie s'il existe un endpoint JSON derrière la page Top Deals avant de décider s'il
   faut un navigateur. » → a débouché sur le diagnostic réseau documenté dans
   `docs/architecture.md` (capture réseau Playwright ne montrant aucune réponse JSON
   exploitable), qui justifie le choix d'un navigateur pour cette seule partie de la collecte.

## Autres tâches réalisées avec l'IA

Au-delà du résumé de cours et du guidage d'architecture, l'IA a aussi participé à l'écriture
du code (`src/greenkart_scraper/*.py`), des tests et de la documentation, ainsi qu'à
l'exécution réelle de la collecte et de `pytest`.

## Ce qui a été vérifié

- Chaque commande du README a été exécutée réellement contre la cible en ligne, pas
  seulement relue : 30 produits et 19 offres obtenus, 0 rejet, 0 doublon, `pytest` : 12/12.
- Le diagnostic du fichier `data/products.json` et l'absence d'endpoint pour `#/offers`
  proviennent de requêtes et de captures réseau réellement exécutées (voir
  `docs/architecture.md`), pas d'une supposition sur la structure habituelle de ce type de
  site.
- Le piège du 31e élément `.product` (widget panier) a été constaté en comparant le nombre
  de `.product-name` et de `.product-price` rendus dans le DOM, pas supposé a priori.

## Proposition corrigée ou refusée

Piste initialement envisagée : extraire le catalogue directement depuis le DOM rendu
(Playwright), comme pour la table Top Deals. Corrigée après avoir constaté que la page rend
31 éléments `.product` alors que le catalogue réel ne contient que 30 produits : le 31e est
le widget panier (« Total price »), qui réutilise les mêmes classes CSS et n'est pas un
produit. Remplacée par la lecture directe de `data/products.json` (30 entrées propres), qui
évite structurellement ce piège.
