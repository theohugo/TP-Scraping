# Architecture — GreenKart scraper (cible S18)

## Diagnostic de la cible (refait le 2026-07-30, methode module01)

Cible attribuee : **S18 — GreenKart, Rahul Shetty Academy**
(`https://rahulshettyacademy.com/seleniumPractise/`).

### robots.txt

```
User-agent: *
Allow: /
Disallow: /AutomationPractice/

Sitemap: https://rahulshettyacademy.com/sitemap.xml
```

`/AutomationPractice/` est hors perimetre (chemin different). Aucun
`Crawl-delay` declare. Le chemin collecte (`/seleniumPractise/...`) est
autorise.

### HTML initial vs DOM vs reseau

```
curl -s https://rahulshettyacademy.com/seleniumPractise/ | wc -c   # 1359
curl -s https://rahulshettyacademy.com/seleniumPractise/ | grep -c product  # 0
```

Le document initial est une coquille React (`<div id="root"></div>` + deux
bundles JS) : confirme, conforme a la fiche de cible ("contenu absent sans
JavaScript"). Deux sources de donnees distinctes ont ete identifiees en
lisant le bundle JS puis en observant le rendu :

| Donnee | Source reelle | Preuve |
| --- | --- | --- |
| Catalogue (30 articles) | `GET /seleniumPractise/data/products.json`, un fichier JSON statique appele par le composant principal via `axios.get(window.location.origin + window.location.pathname + "data/products.json")` (trouve en lisant le bundle `main.*.js`) | `curl` direct renvoie 200 + JSON, sans navigateur |
| Table "Top Deals" (page `#/offers`) | Aucune. Capture reseau complete (Playwright, `page.on("response")`) lors du rendu de `#/offers` : seuls des pixels publicitaires (Google Ads, LinkedIn) apparaissent, aucune reponse JSON portant les lignes de la table | Script de capture, voir historique de developpement |

**Decision d'acquisition** : le catalogue est collecte au **niveau 1** de
l'echelle du cours (dataset publie, decouvert autrement que par une page de
documentation, mais un fichier statique reste un fichier statique). La table
Top Deals est collectee au **niveau 5** (navigateur), seul niveau qui
fonctionne ici : aucun repli HTTP n'existe, ce qui a ete verifie par preuve
(capture reseau vide) et non suppose.

### Piege de selecteur decouvert

Le rendu DOM de la page principale expose **31** elements portant la classe
`.product` (le nombre annonce par `MATRICE_CIBLES_ELEVES.md`), mais un seul
d'entre eux n'a pas de `.product-name` :

```html
<div class="showPriceWrapper product">No. Of Items:<br><span class="total-item">0</span>...</div>
```

C'est le recapitulatif du panier (widget "Total price"), qui reutilise les
classes `product` / `product-price` pour son style. Un extracteur qui viserait
`.product` sur le DOM produirait donc un 31e "produit" incomplet. **C'est
precisement pourquoi ce projet n'extrait jamais depuis le DOM du catalogue** :
en passant par `data/products.json` (30 entrees propres, sans ce widget), le
probleme ne se pose plus. C'est l'argument concret retenu pour le choix
"API/fichier plutot que DOM" (voir "Decisions" plus bas).

Consequence sur le compte-rendu : la fiche de cible annonce 31 produits ; le
diagnostic reproductible en donne 30. La divergence est documentee, pas
corrigee a la main.

### Unite, quantite et devise

- Le nom brut embarque l'unite de vente : `"Brocolli - 1 Kg"`,
  `"Raspberry - 1/4 Kg"`, ou aucun suffixe (`"Capsicum"`). Normalise en
  `unit` (`kg` / `quarter_kg` / `piece`) par `normalize.parse_name_and_unit`.
- L'incrementation du controle "+" sur la fiche produit a ete testee
  manuellement (Playwright, 2 clics consecutifs : 1 -> 2 -> 3) : elle vaut
  toujours **+1**, sur tous les articles verifies. Aucune valeur differente
  n'est exposee par la source : `quantity_step` est donc une constante
  documentee (`DEFAULT_QUANTITY_STEP = 1`), pas un champ extrait.
- La devise (Roupie indienne, `₹`) n'apparait dans aucune des deux sources de
  donnees : elle est injectee par une regle CSS `::before` sur
  `.product-price` (verifie via `getComputedStyle(el, '::before').content`).
  `currency = "INR"` est donc une constante documentee, pas une valeur
  observee dans le flux de donnees. La table Top Deals n'affiche aucun
  symbole de devise du tout ; on retient la meme hypothese (INR, meme site)
  faute d'indication contraire.

## Flux de donnees (six responsabilites)

```
                    +------------------+
                    |   config.py      |  (delai, retries, plafonds, dossier de sortie)
                    +---------+--------+
                              |
        +---------------------+---------------------+
        |                                             |
        v                                             v
+---------------+                           +--------------------+
| acquisition.py |  GET products.json        | acquisition.py     |  Playwright, table Top Deals
| fetch_catalog_ |  (httpx + retry/backoff)  | fetch_offers_raw   |  (budget de pages, arret sur
| raw            |                           |                    |  lien "Next" disabled)
+-------+--------+                           +---------+----------+
        |                                              |
        v                                              v
+---------------+                           +--------------------+
| extraction.py  |  build_product()          | extraction.py      |  build_deal()
| -> Product     |  (Pydantic, rejet loggue) | -> Deal            |  (Pydantic, rejet loggue)
+-------+--------+                           +---------+----------+
        |                                              |
        v                                              v
+----------------------------+           +----------------------------+
| storage.py: dedupe(sku)     |           | storage.py: dedupe(deal_id) |
| write_jsonl -> products.jsonl|          | write_jsonl -> offers.jsonl |
+------------------------------+          +------------------------------+
                              |
                              v
                 logging_conf.py : traces horodatees
                 (vus / rejetes / doublons / exportes)
```

| Composant | Responsabilite | Entree | Sortie |
| --- | --- | --- | --- |
| `config.py` | configuration | variables d'environnement / `.env` | `Settings` |
| `acquisition.py` | acquisition | URL cible | liste de dictionnaires bruts |
| `extraction.py` | extraction + normalisation + validation | dictionnaire brut | `Product` / `Deal` ou `None` (rejet loggue) |
| `storage.py` | deduplication + export | liste d'objets valides | fichier `.jsonl` |
| `logging_conf.py` | journalisation | — | traces horodatees sur stdout |
| `cli.py` | orchestration | arguments CLI | resume (vus/exportes/rejetes/doublons) |

## Ancrage des deux champs les plus importants

| Champ | Ancrage retenu | Alternative ecartee | Si l'ancrage disparait |
| --- | --- | --- | --- |
| Identite du produit (`sku`) | Champ `id` du fichier `data/products.json`, prefixe `GK-` | Position dans la liste JSON (index) : casserait silencieusement si le site reordonne le catalogue sans changer les id | Le `KeyError` sur `raw["id"]` fait rejeter la fiche (loggue), elle n'est jamais silencieusement absente |
| Prix (`price`) | Champ `price` de `data/products.json`, deja numerique | Texte affiche dans `.product-price` (DOM) : necessiterait un navigateur pour une donnee deja disponible en JSON, et expose au faux-positif `.product` documente plus haut | `parse_price` leve `ValueError` sur toute valeur non numerique -> la fiche est rejetee, pas mise a zero |

## Decisions structurantes et alternative ecartee

**Decision 1 — fichier JSON plutot que DOM pour le catalogue.** Le rendu
React expose bien les 30 (+1 decoy) cartes produit dans le DOM, ce qui
aurait permis une extraction Playwright classique. Ecarte : cela impose un
navigateur pour une donnee deja disponible via un simple GET, et cela
expose au piege du 31e element `.product` (le widget panier). Le fichier
JSON est plus rapide, plus stable, et evite structurellement ce piege.

**Decision 2 — deux objets metier distincts (`Product` et `Deal`) plutot
qu'un schema unique.** Le catalogue et la table Top Deals n'ont pas les
memes champs (unite/categorie/image d'un cote, prix barre de l'autre) ni la
meme source (`api` vs `browser`). Forcer un schema commun aurait multiplie
les champs optionnels et rendu la validation Pydantic moins stricte. Le cout
est deux fichiers de sortie au lieu d'un ; assume et documente dans le
README.

## Repli en cas de blocage

Cette cible ne presente aucune protection (pas de CAPTCHA, pas de
rate-limiting observe, pas de 403). Le module `http_client.py` implemente
neanmoins un budget de tentatives et un backoff avec jitter sur les statuts
transitoires (408/429/5xx), conformement a la regle du cours : un 4xx
definitif (404, 403) n'est jamais rejoue.
