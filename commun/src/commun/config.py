"""Chargement optionnel d'un fichier .env, partage par les deux collecteurs.

Format KEY=VALUE, une variable par ligne ; les lignes vides et les commentaires
(#) sont ignores. N'ecrase jamais une variable deja presente dans l'environnement
(os.environ.setdefault) : les variables d'environnement reelles restent prioritaires
sur le fichier .env.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: str | Path = ".env") -> None:
    """Charge un fichier .env (KEY=VALUE) dans os.environ s'il existe."""
    env_path = Path(path)
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))
