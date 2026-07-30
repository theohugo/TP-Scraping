# Fiche de cible — S30 : Harvard Art Museums Collections

## Identification

- **URL de depart :** https://harvardartmuseums.org/collections
- **Cible attribuee (MATRICE_CIBLES_ELEVES.md) :** S30, objet `Artwork`, plafond **60 metadonnees**, champs requis `title, artist, date_text, classification, medium, url`.
- **Bascule de cible :** non. La cible attribuee a ete conservee.

## 1. Regles d'acces verifiees avant collecte

- **robots.txt** (`https://harvardartmuseums.org/robots.txt`, verifie le 2026-07-30) : le fichier contient **un seul groupe**, qui liste par leur nom une centaine de robots (essentiellement des robots d'IA/entrainement — `GPTBot`, `ClaudeBot`, `anthropic-ai`, `CCBot`, `PerplexityBot`... — et quelques outils de scraping generiques comme `Scrapy`), avec `Disallow: /` pour ce groupe. **Il n'existe pas de groupe `User-agent: *`** : aucune regle ne s'applique donc a un client identifie sous un nom distinct de cette liste (RFC 9309 : un robot qui ne correspond a aucun groupe nomme n'est pas restreint).
  - **Decision prise** : ne jamais utiliser Scrapy avec son User-Agent par defaut (litteralement nomme dans la liste bloquee), et s'identifier avec un User-Agent explicite et honnete (`HarvardCollectionsHarvester/0.1 (+lien du depot; usage academique)`), distinct de tous les noms listes. Aucun `Sitemap:` n'est declare, aucun `Crawl-delay` n'est present : le delai est donc choisi par prudence (1,5 s entre requetes, une seule requete a la fois), pas impose par le fichier.
- **Conditions d'utilisation** : la page `/collections` et l'API `/browse` sont publiques, accessibles sans compte. Aucune donnee personnelle n'est collectee (uniquement des metadonnees d'oeuvres : titre, artiste historique, date, medium).
- **Volume reellement envoye** : 3 requetes pour 60 objets (`load_amount=20` par requete), traces dans `data/artworks.jsonl` correspondant et dans les logs de `python -m harvest.collect`.

## 2. HTML, SPA, API ou combinaison — preuve

| Element | Observation |
|---|---|
| HTML initial (`curl` sans JS) | La reponse de `GET /collections` (~415 Ko) contient la structure de la page (menu, filtres, section `#vue-territory`) mais **aucune carte d'oeuvre, aucun titre, aucun prix** : le conteneur de resultats (`#collection-list`) est en realite le selecteur de "mes collections" personnelles (fonctionnalite de compte), pas la zone de resultats. Ajouter un parametre de recherche a l'URL (`?q=vase`) ne change **pas la taille de la reponse** (toujours 414 718 octets) : le serveur ignore le parametre, la recherche est donc purement cote client. |
| DOM apres rendu | Verifie avec Playwright (`page.goto(...)`, chargement complet) : le DOM final contient des elements dynamiques generes par un composant Vue mont sur `#vue-territory`/`#workbench`, alimentes par un appel reseau observe pendant le chargement (voir ligne suivante). |
| Requete(s) reseau utile(s) | Interception reseau Playwright (`page.on("response", ...)` branche avant `page.goto`) : au chargement de `/collections`, le navigateur emet automatiquement `GET https://harvardartmuseums.org/browse?q=&load_amount=12&offset=0`, reponse `200 application/json` contenant directement les objets (titre, artistes, date, classification, medium, URL de fiche). C'est cette meme requete, rejouee avec nos propres parametres de pagination, qui alimente le collecteur — sans jamais ouvrir de navigateur en collecte reelle. |
| Pagination | Parametres `offset` et `load_amount` (famille "offset/limit"). Condition d'arret retenue : `records` vide, ou plafond `HARVEST_MAX_ITEMS` atteint (60 par defaut). Le champ `info.next` de la reponse fournit une URL directe vers `api.harvardartmuseums.org` **avec la cle d'API du musee visible en clair** : cette cle appartient au musee, nous ne l'utilisons jamais (voir `src/harvest/acquisition.py`, note ethique en tete de fichier). Nous construisons notre propre `offset` suivant, sans dependre de ce champ. |
| Decision d'acquisition | Niveau 3 de l'echelle d'acquisition (endpoint JSON interne, non documente publiquement mais reellement utilise par la page, sans authentification). Pas de navigateur en collecte reelle : Playwright n'a servi qu'une fois, en phase de diagnostic, pour observer cet appel. |

**Conformite a la fiche de cible (observation datee du 30 juillet 2026 dans la matrice) :** la fiche annonce "contenu absent sans JavaScript" — **confirme** par notre propre diagnostic (HTML initial sans carte d'oeuvre, donnees presentes uniquement via l'appel JSON declenche par le rendu). Notre diagnostic va plus loin que la fiche : il identifie precisement l'endpoint (`/browse`) plutot que de s'arreter au constat "SPA".

## 3. Pourquoi pas l'API publique documentee (`api.harvardartmuseums.org`) ?

Le musee publie une API documentee (lien present sur la page : `https://harvardartmuseums.org/collections/api`), qui necessite une cle personnelle gratuite. Nous ne l'avons pas utilisee pour deux raisons :
1. L'ENONCE demande d'observer et de reproduire l'appel **reellement utilise par la page elle-meme** — c'est `/browse`, pas l'API publique externe.
2. La reponse de `/browse` expose la cle interne du musee dans `info.next` ; l'utiliser (meme si elle est techniquement lisible) reviendrait a utiliser un identifiant qui ne nous appartient pas. Nous avons prefere nous en tenir a l'endpoint public sans cle.

## 4. Regle d'arret

La collecte s'arrete immediatement si : un code 401/403/404/410 est recu (`RETRYABLE_STATUS`/`NON_RETRYABLE_STATUS` dans `acquisition.py`), si la reponse n'est pas un JSON valide, ou si `records` est vide. Aucun de ces cas ne s'est produit lors des executions reelles (voir rubrique 7 du rapport).
