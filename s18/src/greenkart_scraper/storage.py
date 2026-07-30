"""Stockage : deduplication et export JSONL.

Un objet par ligne (module02, section formats) : une collecte interrompue
laisse un fichier exploitable, et la relecture se fait en flux.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, TypeVar


class _HasKey(Protocol):
    def model_dump(self, mode: str) -> dict: ...


T = TypeVar("T", bound=_HasKey)


def dedupe(items: list[T], key: callable) -> tuple[list[T], int]:
    """Retire les doublons selon `key(item)`. Retourne (items_uniques, nb_doublons)."""
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
    """Ecrit un objet JSON par ligne. Retourne le nombre de lignes ecrites."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as stream:
        for item in items:
            stream.write(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) + "\n")
            count += 1
    return count
