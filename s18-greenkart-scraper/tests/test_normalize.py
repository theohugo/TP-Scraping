"""Controle de verification n.2 : les normalisations (unite, prix)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from greenkart_scraper.normalize import parse_name_and_unit, parse_price, slugify


def test_parse_name_and_unit_kg():
    assert parse_name_and_unit("Brocolli - 1 Kg") == ("Brocolli", "kg")


def test_parse_name_and_unit_quarter_kg():
    assert parse_name_and_unit("Raspberry - 1/4 Kg") == ("Raspberry", "quarter_kg")


def test_parse_name_and_unit_no_suffix_defaults_to_piece():
    assert parse_name_and_unit("Capsicum") == ("Capsicum", "piece")


def test_parse_price_from_int():
    assert parse_price(120) == Decimal("120")


def test_parse_price_from_str():
    assert parse_price("48") == Decimal("48")


def test_parse_price_invalid_raises():
    with pytest.raises(ValueError):
        parse_price("gratuit")


def test_slugify_removes_accents_and_spaces():
    assert slugify("Dragon fruit") == "dragon-fruit"
