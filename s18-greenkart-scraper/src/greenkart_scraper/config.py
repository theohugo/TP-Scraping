"""Configuration : tout vient de l'environnement, rien n'est ecrit en dur.

Responsabilite "configuration" de l'architecture (docs/architecture.md).
Copier config.example en .env pour ajuster le debit ou les plafonds sans
toucher au code.

Le chargement du fichier .env est desormais assure par le package partage
`commun` (`commun.config.load_env_file`), identique a celui utilise par le
collecteur S30 du binome. Reexporte ici pour que `cli.py` n'ait besoin d'aucune
modification.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from commun.config import load_env_file

ENV_PREFIX = "GK_"

CATALOG_URL = "https://rahulshettyacademy.com/seleniumPractise/data/products.json"
CATALOG_PAGE_URL = "https://rahulshettyacademy.com/seleniumPractise/#/"
OFFERS_PAGE_URL = "https://rahulshettyacademy.com/seleniumPractise/#/offers"

__all__ = ["ENV_PREFIX", "CATALOG_URL", "CATALOG_PAGE_URL", "OFFERS_PAGE_URL", "load_env_file", "Settings"]


def _get(name: str, default: str) -> str:
    return os.environ.get(ENV_PREFIX + name, default)


@dataclass(slots=True)
class Settings:
    """Parametres d'execution du collecteur."""

    request_delay_s: float = 0.5
    max_retries: int = 3
    max_offers_pages: int = 10
    output_dir: Path = Path("data")

    @classmethod
    def from_env(cls) -> Settings:
        defaults = cls()
        return cls(
            request_delay_s=float(_get("REQUEST_DELAY_S", str(defaults.request_delay_s))),
            max_retries=int(_get("MAX_RETRIES", str(defaults.max_retries))),
            max_offers_pages=int(_get("MAX_OFFERS_PAGES", str(defaults.max_offers_pages))),
            output_dir=Path(_get("OUTPUT_DIR", str(defaults.output_dir))),
        )

    def ensure_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
