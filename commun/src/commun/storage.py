"""Stockage generique : deduplication et export, sans dependre d'un modele precis.

Utilise par les deux collecteurs (S18 Product/Deal, S30 Artwork) : la logique de
deduplication par cle et d'ecriture JSONL est strictement identique des deux cotes,
seule la cle de deduplication et le modele Pydantic changent d'un projet a l'autre.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Protocol, TypeVar


class _DumpableModel(Protocol):
    def model_dump_json(self) -> str: ...
    def model_dump(self, mode: str) -> dict: ...


T = TypeVar("T", bound=_DumpableModel)


def dedupe(items: list[T], key: Callable[[T], object]) -> tuple[list[T], int]:
    """Retire les doublons selon `key(item)`. Retourne (items_uniques, nb_doublons).

    Garde la premiere occurrence rencontree ; ne modifie jamais un objet, se contente
    de filtrer la liste.
    """
    seen: set = set()
    unique: list[T] = []
    duplicates = 0
    for item in items:
        item_key = key(item)
        if item_key in seen:
            duplicates += 1
            continue
        seen.add(item_key)
        unique.append(item)
    return unique, duplicates


def write_jsonl(items: list[T], path: Path) -> int:
    """Ecrit un objet JSON par ligne (un modele Pydantic par ligne). Retourne le nombre de lignes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as stream:
        for item in items:
            stream.write(item.model_dump_json() + "\n")
            count += 1
    return count


def write_json_sample(items: list[T], path: Path, *, limit: int = 10) -> int:
    """Ecrit un echantillon (tableau JSON indente) des `limit` premiers objets."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sample = items[:limit]
    payload = [json.loads(item.model_dump_json()) for item in sample]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(sample)
