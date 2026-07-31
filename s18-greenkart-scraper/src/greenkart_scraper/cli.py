"""Point d'entree : orchestre acquisition -> extraction -> export pour les
deux jeux de donnees (catalogue + Top Deals), et imprime un resume verifiable.

Usage limite (pour un test rapide sans tout re-collecter) :
    python -m greenkart_scraper.cli --catalog-limit 5 --max-offers-pages 1
"""

from __future__ import annotations

import argparse
import logging
import sys

from greenkart_scraper.acquisition import fetch_catalog_raw, fetch_offers_raw
from greenkart_scraper.config import Settings, load_env_file
from greenkart_scraper.extraction import build_deal, build_product
from greenkart_scraper.http_client import build_client
from greenkart_scraper.logging_conf import configure_logging
from greenkart_scraper.storage import dedupe, write_jsonl

logger = logging.getLogger("greenkart_scraper")


def run(settings: Settings, catalog_limit: int | None, skip_offers: bool) -> dict[str, int]:
    settings.ensure_output_dir()
    summary: dict[str, int] = {}

    with build_client() as client:
        raw_catalog = fetch_catalog_raw(client, settings)
    if catalog_limit is not None:
        raw_catalog = raw_catalog[:catalog_limit]

    products = [build_product(raw) for raw in raw_catalog]
    products_ok = [p for p in products if p is not None]
    products_unique, catalog_dupes = dedupe(products_ok, key=lambda p: p.sku)
    catalog_written = write_jsonl(products_unique, settings.output_dir / "products.jsonl")

    summary.update(
        catalog_seen=len(raw_catalog),
        catalog_rejected=len(raw_catalog) - len(products_ok),
        catalog_duplicates=catalog_dupes,
        catalog_exported=catalog_written,
    )
    logger.info(
        "catalogue: vus=%d exportes=%d rejetes=%d doublons=%d",
        summary["catalog_seen"],
        summary["catalog_exported"],
        summary["catalog_rejected"],
        summary["catalog_duplicates"],
    )

    if skip_offers:
        summary.update(offers_seen=0, offers_rejected=0, offers_duplicates=0, offers_exported=0)
        return summary

    raw_offers = fetch_offers_raw(settings)
    deals = [build_deal(raw) for raw in raw_offers]
    deals_ok = [d for d in deals if d is not None]
    deals_unique, offers_dupes = dedupe(deals_ok, key=lambda d: d.deal_id)
    offers_written = write_jsonl(deals_unique, settings.output_dir / "offers.jsonl")

    summary.update(
        offers_seen=len(raw_offers),
        offers_rejected=len(raw_offers) - len(deals_ok),
        offers_duplicates=offers_dupes,
        offers_exported=offers_written,
    )
    logger.info(
        "offres: vus=%d exportes=%d rejetes=%d doublons=%d",
        summary["offers_seen"],
        summary["offers_exported"],
        summary["offers_rejected"],
        summary["offers_duplicates"],
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collecteur GreenKart (TP S18).")
    parser.add_argument(
        "--catalog-limit",
        type=int,
        default=None,
        help="Limite le nombre d'articles du catalogue traites (collecte rapide de test).",
    )
    parser.add_argument(
        "--max-offers-pages",
        type=int,
        default=None,
        help="Plafond de pages parcourues sur la table Top Deals.",
    )
    parser.add_argument(
        "--no-offers",
        action="store_true",
        help="Ne pas collecter la table Top Deals (catalogue seul).",
    )
    parser.add_argument("--output-dir", type=str, default=None, help="Dossier de sortie JSONL.")
    args = parser.parse_args(argv)

    load_env_file()
    configure_logging()
    settings = Settings.from_env()
    if args.max_offers_pages is not None:
        settings.max_offers_pages = args.max_offers_pages
    if args.output_dir is not None:
        settings.output_dir = settings.output_dir.__class__(args.output_dir)

    summary = run(settings, catalog_limit=args.catalog_limit, skip_offers=args.no_offers)
    print("resume:", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
