"""Extraction : transforme un enregistrement brut en objet valide du contrat.

Separee de l'acquisition (module01/02) : ce module ne fait aucun appel
reseau, il ne sait meme pas d'ou vient le dictionnaire qu'on lui donne.
C'est ce qui le rend testable sans reseau (tests/test_extraction.py) et
reutilisable a l'identique sur une page enregistree.
"""

from __future__ import annotations

import logging

from pydantic import ValidationError

from greenkart_scraper.config import CATALOG_PAGE_URL
from greenkart_scraper.contracts import Deal, Product, utc_now
from greenkart_scraper.normalize import (
    parse_name_and_unit,
    parse_price,
    resolve_url,
    slugify,
)

logger = logging.getLogger("greenkart_scraper")


def build_product(raw: dict) -> Product | None:
    """Construit un Product valide depuis une entree brute de products.json.

    Retourne None et journalise le rejet si un champ obligatoire est absent
    ou invalide - jamais un enregistrement silencieusement incomplet.
    """
    try:
        raw_name = raw["name"]
        name, unit = parse_name_and_unit(raw_name)
        return Product(
            sku=f"GK-{int(raw['id']):03d}",
            name=name,
            unit=unit,
            quantity_step=1,
            price=parse_price(raw["price"]),
            category=raw["category"],
            image_url=resolve_url(CATALOG_PAGE_URL, raw["image"]),
            url=CATALOG_PAGE_URL,
            scraped_at=utc_now(),
            source="api",
        )
    except (KeyError, ValueError, ValidationError) as error:
        logger.warning("rejet produit %r: %s", raw.get("name", raw), error)
        return None


def build_deal(raw: dict) -> Deal | None:
    """Construit un Deal valide depuis une ligne brute de la table Top Deals."""
    try:
        name = raw["name"].strip()
        return Deal(
            deal_id=slugify(name),
            name=name,
            price=parse_price(raw["price"]),
            discount_price=parse_price(raw["discount_price"]),
            page=int(raw["page"]),
            url="https://rahulshettyacademy.com/seleniumPractise/#/offers",
            scraped_at=utc_now(),
            source="browser",
        )
    except (KeyError, ValueError, ValidationError) as error:
        logger.warning("rejet offre %r: %s", raw.get("name", raw), error)
        return None
