"""Acquisition : recuperer les octets bruts, rien de plus.

Deux canaux, deux niveaux de l'echelle d'acquisition (module01) :
- `fetch_catalog_raw` : niveau 1 (dataset publie) - un GET sur
  data/products.json, decouvert en lisant le bundle JS de l'application
  (voir docs/architecture.md, section diagnostic). Aucun navigateur requis.
- `fetch_offers_raw` : niveau 5 (navigateur), seul niveau qui fonctionne ici.
  Le diagnostic (capture reseau lors du rendu de la page /#/offers) n'a
  trouve aucun endpoint JSON exploitable : la table est peuplee par React a
  partir de donnees embarquees dans le bundle, sans appel reseau. Le
  navigateur est donc un dernier recours ici, pas un choix de confort.
"""

from __future__ import annotations

import logging

import httpx
from playwright.sync_api import sync_playwright

from greenkart_scraper.config import CATALOG_URL, OFFERS_PAGE_URL, Settings
from greenkart_scraper.http_client import fetch_with_retry

logger = logging.getLogger("greenkart_scraper")

# Garde-fous du parcours de la table "Top Deals" (module02 pagination /
# module04 pieges de crawler) : budget de pages dur, jamais de boucle non
# bornee meme si le lien "Next" ne se desactivait jamais.
_NEXT_LINK_SELECTOR = "a[aria-label='Next']"
_ROW_SELECTOR = "table tbody tr"


def fetch_catalog_raw(client: httpx.Client, settings: Settings) -> list[dict]:
    """Recupere le catalogue complet en un seul GET. Retourne la liste brute."""
    response = fetch_with_retry(client, CATALOG_URL, settings.max_retries)
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError(f"reponse inattendue de {CATALOG_URL}: pas une liste JSON")
    logger.info("catalogue: %d entrees brutes recues", len(payload))
    return payload


def fetch_offers_raw(settings: Settings) -> list[dict]:
    """Parcourt la table "Top Deals" page par page et retourne les lignes brutes.

    Garde-fous : budget dur `settings.max_offers_pages`, arret des que le
    lien "Next" n'existe plus ou que son <li> parent porte la classe
    "disabled" (observe sur la cible : la derniere page est la page 4).
    """
    rows: list[dict] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(OFFERS_PAGE_URL, wait_until="networkidle", timeout=30_000)

        for page_number in range(1, settings.max_offers_pages + 1):
            table_rows = page.locator(_ROW_SELECTOR)
            count = table_rows.count()
            if count == 0:
                logger.warning("aucune ligne trouvee sur la page %d, arret", page_number)
                break
            for i in range(count):
                cells = table_rows.nth(i).locator("td")
                rows.append(
                    {
                        "name": cells.nth(0).inner_text(),
                        "price": cells.nth(1).inner_text(),
                        "discount_price": cells.nth(2).inner_text(),
                        "page": page_number,
                    }
                )
            logger.info("offres: page %d, %d lignes lues", page_number, count)

            next_link = page.locator(_NEXT_LINK_SELECTOR)
            if next_link.count() == 0:
                break
            parent_classes = next_link.first.evaluate(
                "el => el.closest('li') ? el.closest('li').className : ''"
            )
            if "disabled" in parent_classes:
                break
            next_link.first.click()
            page.wait_for_timeout(400)
        else:
            logger.warning(
                "budget de pages (%d) atteint sur la table Top Deals : "
                "collecte peut-etre incomplete",
                settings.max_offers_pages,
            )
        browser.close()
    logger.info("offres: %d lignes brutes recues au total", len(rows))
    return rows
