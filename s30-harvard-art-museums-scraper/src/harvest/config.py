"""Configuration du collecteur, chargee depuis l'environnement (aucun secret requis)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    """Parametres de collecte, tous surchargeables par variable d'environnement."""

    base_url: str
    load_amount: int
    max_items: int
    delay_s: float
    max_retries: int
    output_dir: str
    user_agent: str

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        source = env if env is not None else os.environ
        return cls(
            base_url=source.get("HARVEST_BASE_URL", "https://harvardartmuseums.org"),
            load_amount=int(source.get("HARVEST_LOAD_AMOUNT", "20")),
            max_items=int(source.get("HARVEST_MAX_ITEMS", "60")),
            delay_s=float(source.get("HARVEST_DELAY_S", "1.5")),
            max_retries=int(source.get("HARVEST_MAX_RETRIES", "3")),
            output_dir=source.get("HARVEST_OUTPUT_DIR", "data"),
            user_agent=source.get(
                "HARVEST_USER_AGENT",
                "HarvardCollectionsHarvester/0.1 "
                "(+https://github.com/theohugo/TP-Scraping; TP scraping IPSSI, usage academique)",
            ),
        )
