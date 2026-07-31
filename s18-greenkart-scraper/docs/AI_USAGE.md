# Usage de l'IA — TP GreenKart (S18)

## Outils utilises

Claude Code (Anthropic, agent en ligne de commande avec acces shell/fichiers),
sur toute la duree du projet.

## Taches confiees

- Analyse du contenu des dossiers `cours/` et `labs/` de la formation, pour
  en extraire la methodologie (echelle d'acquisition, ancrage des
  selecteurs, separation des responsabilites, contrat de donnees, formats
  de sortie) avant de commencer le TP.
- Diagnostic de la cible reelle S18 : lecture de `robots.txt`, inspection du
  HTML initial (`curl`), puis rendu et capture reseau via un vrai navigateur
  Chromium pilote par Playwright (installe et execute directement en ligne
  de commande, pas via une extension navigateur) pour verifier l'existence
  ou l'absence d'un endpoint JSON derriere la page `#/offers`.
- Conception de l'architecture (six responsabilites, deux objets metier
  `Product`/`Deal`) et redaction de l'intégralite du code, des tests et de
  la documentation de ce depot.

## Deux exemples de demandes significatives

1. « Analyse en detail les dossiers cours et labs pour adopter la meme
   methodologie que celle vue en cours, puis fais le TP » — a produit
   l'analyse de la formation puis, une fois la cible S18 communiquee, tout
   le contenu de ce depot.
2. « Verifie si un endpoint JSON existe derriere la page Top Deals avant de
   decider s'il faut un navigateur » — a debouche sur le diagnostic reseau
   documente dans `docs/architecture.md` (capture Playwright ne montrant
   aucune reponse JSON exploitable, seulement des pixels publicitaires), qui
   justifie factuellement le choix d'un navigateur pour cette seule partie
   de la collecte.

## Ce qui a ete verifie

- Chaque commande du README (installation, collecte limitee, collecte
  complete, `pytest`) a ete executee reellement contre la cible en ligne
  pendant le developpement, pas seulement relue : 30 produits et 19 offres
  obtenus, 0 rejet, 0 doublon, `pytest` : 12/12.
- Le diagnostic du fichier `data/products.json` et l'absence d'endpoint pour
  `#/offers` proviennent de requetes et de captures reseau reellement
  executees (voir `docs/architecture.md`), pas d'une supposition sur la
  structure habituelle de ce type de site.
- Le piege du 31e element `.product` (widget panier) a ete constate en
  comparant le nombre de `.product-name` et de `.product-price` rendus dans
  le DOM, pas suppose a priori.

## Proposition corrigee ou refusee

*A completer par l'etudiant avant la remise.* Ce document est redige au fil
de la construction du projet avec l'IA ; il ne remplace pas votre propre
relecture. Avant de rendre ce TP :

1. Relisez le code de `src/greenkart_scraper/` ligne par ligne et assurez-
   vous de pouvoir l'expliquer et le modifier sans aide, y compris les
   points signales dans "Limites connues" du README.
2. Si vous corrigez, simplifiez ou refusez une partie de ce que l'IA a
   produit, notez-le ici avec la raison — c'est ce que la grille de
   notation demande explicitement, et c'est aussi la meilleure preparation
   aux 5 questions orales.
3. Si vous ne changez rien apres relecture, notez-le aussi : « relu
   integralement le <date>, aucune correction necessaire » est une reponse
   valable et honnete.

## Declaration

Si aucun usage d'IA n'avait eu lieu, la case correspondante de la trame
aurait suffi ; ici l'usage est reel et important (conception + code
initial), ce qui est autorise par l'enonce et n'est pas penalisant s'il est
declare et verifie — c'est l'objet de ce fichier.
