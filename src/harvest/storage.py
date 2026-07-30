"""Export des Artwork collectes et deduplication par identifiant stable."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .models import Artwork


@dataclass(slots=True)
class CollectionReport:
    """Compteurs de la collecte, tels qu'attendus par la rubrique 7 du rapport."""

    seen: int = 0
    exported: int = 0
    rejected: int = 0
    duplicates: int = 0
    missing_required_fields: int = 0
    artworks: list[Artwork] = field(default_factory=list)

    def as_dict(self) -> dict[str, int]:
        return {
            "vus": self.seen,
            "exportes": self.exported,
            "rejetes": self.rejected,
            "doublons": self.duplicates,
            "champs_obligatoires_manquants": self.missing_required_fields,
        }


def dedupe_artworks(artworks: list[Artwork]) -> tuple[list[Artwork], int]:
    """Deduplique par object_id (identifiant stable), garde la premiere occurrence."""
    seen_ids: set[int] = set()
    unique: list[Artwork] = []
    duplicates = 0
    for artwork in artworks:
        if artwork.object_id in seen_ids:
            duplicates += 1
            continue
        seen_ids.add(artwork.object_id)
        unique.append(artwork)
    return unique, duplicates


def write_jsonl(artworks: list[Artwork], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for artwork in artworks:
            handle.write(artwork.model_dump_json() + "\n")
    return len(artworks)


def write_json_sample(artworks: list[Artwork], path: Path, *, limit: int = 10) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample = artworks[:limit]
    payload = [json.loads(artwork.model_dump_json()) for artwork in sample]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(sample)
