"""Stockage : deduplication et export JSONL.

Un objet par ligne (module02, section formats) : une collecte interrompue
laisse un fichier exploitable, et la relecture se fait en flux.

Cette logique est strictement generique (elle ne depend d'aucun champ propre a
`Product`/`Deal`) et donc identique a celle du collecteur S30 du binome : elle
vit desormais dans le package partage `commun` (`commun.storage`). Ce module se
contente de la reexporter pour que `cli.py`, `extraction.py` et les tests
n'aient besoin d'aucune modification.
"""

from __future__ import annotations

from commun.storage import dedupe, write_json_sample, write_jsonl

__all__ = ["dedupe", "write_jsonl", "write_json_sample"]
