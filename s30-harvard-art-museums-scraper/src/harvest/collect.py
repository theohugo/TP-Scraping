"""Point d'entree : collecte bornee du catalogue Harvard Art Museums Collections.

Usage :
    python -m harvest.collect --max-items 20
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from commun.config import load_env_file

from .acquisition import build_client, fetch_browse_page, log_event
from .config import Settings
from .extraction import build_artwork
from .storage import CollectionReport, dedupe_artworks, write_json_sample, write_jsonl


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-items", type=int, default=None, help="Plafond d'objets a collecter (defaut: config)")
    parser.add_argument("--delay-s", type=float, default=None, help="Delai minimum entre deux requetes, en secondes")
    parser.add_argument("--output-dir", type=str, default=None, help="Dossier de sortie (JSONL + traces)")
    return parser.parse_args(argv)


def run(settings: Settings) -> CollectionReport:
    report = CollectionReport()
    output_dir = Path(settings.output_dir)

    with build_client(settings.base_url, settings.user_agent) as client:
        offset = 0
        while report.seen < settings.max_items:
            remaining = settings.max_items - report.seen
            load_amount = min(settings.load_amount, remaining)
            payload = fetch_browse_page(
                client,
                offset=offset,
                load_amount=load_amount,
                max_retries=settings.max_retries,
                delay_s=settings.delay_s,
            )
            if payload is None:
                log_event("collection_stopped", reason="acquisition_failed", offset=offset)
                break

            records = payload.get("records", [])
            if not records:
                log_event("collection_stopped", reason="no_more_records", offset=offset)
                break

            for record in records:
                report.seen += 1
                artwork = build_artwork(record)
                if artwork is None:
                    report.rejected += 1
                    if not record.get("title") or not record.get("classification") or not record.get("url"):
                        report.missing_required_fields += 1
                    continue
                report.artworks.append(artwork)

            offset += len(records)

    unique_artworks, duplicates = dedupe_artworks(report.artworks)
    report.artworks = unique_artworks
    report.duplicates = duplicates
    report.exported = len(unique_artworks)

    exported_count = write_jsonl(unique_artworks, output_dir / "artworks.jsonl")
    log_event("collection_finished", exported=exported_count, **report.as_dict())
    return report


def main(argv: list[str] | None = None) -> CollectionReport:
    args = parse_args(argv)
    load_env_file()
    settings = Settings.from_env()
    if args.max_items is not None:
        settings.max_items = args.max_items
    if args.delay_s is not None:
        settings.delay_s = args.delay_s
    if args.output_dir is not None:
        settings.output_dir = args.output_dir

    report = run(settings)

    sample_path = Path("samples/sample_output.json")
    write_json_sample(report.artworks, sample_path, limit=10)

    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
