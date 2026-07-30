"""Controles de verification n.1 et n.3 : nombre d'objets extraits d'une page
enregistree, et deduplication / rejet d'un objet incomplet.

Ces tests ne font aucun appel reseau : ils rejouent l'extraction sur les
fixtures de tests/fixtures/, enregistrees le 2026-07-30 (voir conftest.py).
"""

from __future__ import annotations

from greenkart_scraper.extraction import build_deal, build_product
from greenkart_scraper.storage import dedupe


def test_build_product_count_matches_recorded_catalog(raw_products):
    """Controle n.1 (catalogue) : 30 produits valides sur la page enregistree."""
    products = [build_product(raw) for raw in raw_products]
    assert len(raw_products) == 30
    assert all(p is not None for p in products)
    assert len(products) == 30


def test_build_deal_count_matches_recorded_offers(raw_offers):
    """Controle n.1 (offres) : 19 lignes valides sur les 4 pages enregistrees."""
    deals = [build_deal(raw) for raw in raw_offers]
    assert all(d is not None for d in deals)
    assert len(deals) == 19


def test_build_product_rejects_incomplete_record(raw_products):
    """Controle n.3 : un produit sans prix est rejete, pas silencieusement vide."""
    broken = dict(raw_products[0])
    del broken["price"]
    assert build_product(broken) is None


def test_build_product_rejects_unparsable_price(raw_products):
    broken = dict(raw_products[0])
    broken["price"] = "gratuit"
    assert build_product(broken) is None


def test_dedupe_by_sku_drops_duplicate_products(raw_products):
    """Controle n.3 : la deduplication retire un doublon de SKU."""
    products = [build_product(raw) for raw in raw_products]
    duplicated = products + [products[0]]
    unique, duplicate_count = dedupe(duplicated, key=lambda p: p.sku)
    assert duplicate_count == 1
    assert len(unique) == len(products)
