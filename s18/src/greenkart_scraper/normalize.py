"""Fonctions de normalisation reutilisees par les deux extracteurs.

Isolees dans leur propre module (responsabilite "normalisation et
validation" de l'architecture, voir docs/architecture.md) pour pouvoir etre
testees sans reseau : c'est exactement ce que testent
tests/test_normalize.py.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Literal
from urllib.parse import urljoin

# "Brocolli - 1 Kg" / "Raspberry - 1/4 Kg" / "Capsicum" (pas de suffixe).
# Observe sur les 30 fiches de data/products.json : seuls "1 Kg" et "1/4 Kg"
# apparaissent. Un troisieme cas (ni l'un ni l'autre) serait un signal que le
# catalogue a change de convention de nommage - traite comme une unite
# "piece" par defaut, jamais silencieusement ignore (le nom complet est
# conserve tel quel dans ce cas).
_UNIT_SUFFIX_RE = re.compile(r"^(?P<name>.+?)\s*-\s*(?P<qty>1(?:/4)?)\s*Kg$", re.IGNORECASE)

_UNIT_BY_QTY: dict[str, Literal["kg", "quarter_kg"]] = {
    "1": "kg",
    "1/4": "quarter_kg",
}

# Increment du bouton "+" observe sur la fiche produit : +1 a chaque clic,
# identique sur les 30 articles (verifie manuellement, voir
# docs/architecture.md). Aucune valeur differente n'est exposee par la
# source : ce n'est donc pas un champ extrait mais une constante documentee.
DEFAULT_QUANTITY_STEP = 1

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def parse_name_and_unit(raw_name: str) -> tuple[str, Literal["kg", "quarter_kg", "piece"]]:
    """Separe le nom affiche de l'unite de vente embarquee dans le libelle.

    "Brocolli - 1 Kg" -> ("Brocolli", "kg")
    "Raspberry - 1/4 Kg" -> ("Raspberry", "quarter_kg")
    "Capsicum" -> ("Capsicum", "piece")
    """
    match = _UNIT_SUFFIX_RE.match(raw_name.strip())
    if not match:
        return raw_name.strip(), "piece"
    name = match.group("name").strip()
    unit = _UNIT_BY_QTY[match.group("qty")]
    return name, unit


def parse_price(raw: str | int | float) -> Decimal:
    """Convertit un prix brut (entier JSON ou texte de cellule DOM) en Decimal.

    Leve ValueError si aucune valeur numerique exploitable n'est trouvee -
    un prix illisible doit faire echouer la validation du produit, jamais
    devenir un 0 silencieux.
    """
    text = str(raw).strip()
    cleaned = re.sub(r"[^0-9.]", "", text)
    if not cleaned:
        raise ValueError(f"prix illisible: {raw!r}")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"prix illisible: {raw!r}") from exc


def resolve_url(base: str, relative: str) -> str:
    """Resout une URL relative (ex. './images/tomato.jpg') contre l'URL de la page."""
    return urljoin(base, relative)


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def slugify(text: str) -> str:
    """Transforme un libelle en identifiant stable (ASCII, minuscules, tirets).

    Utilise pour `Deal.deal_id`, faute d'identifiant expose par la table
    "Top Deals" (voir contracts.py).
    """
    ascii_text = strip_accents(text).lower()
    slug = _SLUG_RE.sub("-", ascii_text).strip("-")
    return slug or "sans-nom"
