from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def raw_products() -> list[dict]:
    """Copie enregistree de https://.../seleniumPractise/data/products.json.

    Recuperee le 2026-07-30 (voir docs/architecture.md). Permet de rejouer
    l'extraction sans reseau, comme demande par la consigne de verification.
    """
    return json.loads((FIXTURES_DIR / "products_raw.json").read_text(encoding="utf-8"))


@pytest.fixture
def raw_offers() -> list[dict]:
    """Lignes enregistrees de la table Top Deals (4 pages, capturees le 2026-07-30)."""
    return json.loads((FIXTURES_DIR / "offers_raw.json").read_text(encoding="utf-8"))
