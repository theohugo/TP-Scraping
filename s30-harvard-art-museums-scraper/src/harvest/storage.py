"""Export des Artwork collectes et deduplication par identifiant stable.

La deduplication generique et l'export JSONL/echantillon sont strictement
identiques a ceux du collecteur S18 du binome (aucune dependance a un champ
propre a `Artwork`) : ils vivent desormais dans le package partage `commun`
(`commun.storage`). Ce module se contente d'adapter `dedupe` a la cle
`object_id` et de reexporter le reste, pour que `collect.py` et
`verif/verif.py` n'aient besoin d'aucune modification.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from commun.storage import dedupe, write_json_sample, write_jsonl

from .models import Artwork

__all__ = ["CollectionReport", "dedupe_artworks", "write_jsonl", "write_json_sample"]


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
    return dedupe(artworks, key=lambda artwork: artwork.object_id)
