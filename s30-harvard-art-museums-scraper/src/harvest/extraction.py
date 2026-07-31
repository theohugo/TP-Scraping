"""Transforme un enregistrement JSON brut de l'API en objet Artwork valide.

Trois normalisations sont appliquees, documentees dans le rapport (rubrique 3) :
1. artistes  : la liste imbriquee "people" est reduite a des noms uniques,
   ordonnes par displayorder, en ne gardant que les roles de creation
   ("Artist", "Attributed to", "School of", ...) et en ignorant les roles
   de possession/donation qui existent aussi dans ce champ.
2. dates     : les bornes numeriques "datebegin"/"dateend" fournies par la
   source sont validees (bornes coherentes) ; si elles sont absentes alors que
   le texte libre "dated" existe, une extraction de secours par expression
   reguliere recupere une premiere annee plausible (avec signe negatif si
   "BCE"/"BC" apparait dans le texte).
3. URL       : mise en forme canonique (schema https, hote en minuscules,
   sans parametre de suivi), pour garantir un identifiant de fiche stable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import re

from pydantic import ValidationError

from .acquisition import log_event
from .models import Artwork

_CREATION_ROLES = {
    "artist",
    "attributed to",
    "school of",
    "possibly by",
    "after",
    "manner of",
    "workshop of",
    "circle of",
    "formerly attributed to",
}
_YEAR_PATTERN = re.compile(r"(\d{1,4})\s*(BCE|BC)?", re.IGNORECASE)


def extract_artists(people: list[dict[str, Any]] | None) -> list[str]:
    """Reduit le champ "people" a des noms d'auteurs uniques, dans l'ordre d'affichage."""
    if not people:
        return []
    creators = [
        person
        for person in people
        if str(person.get("role", "")).strip().casefold() in _CREATION_ROLES
    ]
    creators.sort(key=lambda person: person.get("displayorder") or 0)
    names: list[str] = []
    for person in creators:
        name = (person.get("displayname") or person.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
    return names


def parse_date_bounds(
    date_text: str | None, date_begin: int | None, date_end: int | None
) -> tuple[int | None, int | None]:
    """Valide les bornes fournies par la source, ou tente un repli par regex sur le texte libre."""
    if date_begin is not None and date_end is not None:
        if date_begin <= date_end:
            return date_begin, date_end
        log_event("date_bounds_inconsistent", date_begin=date_begin, date_end=date_end)
        return None, None
    if not date_text:
        return None, None
    match = _YEAR_PATTERN.search(date_text)
    if not match:
        return None, None
    year = int(match.group(1))
    if match.group(2):
        year = -year
    return year, year


def canonical_url(raw_url: str) -> str:
    """Force https, hote en minuscules, et retire tout parametre de requete."""
    parts = urlsplit(raw_url)
    scheme = "https"
    netloc = parts.netloc.lower().removeprefix("www.")
    return urlunsplit((scheme, netloc, parts.path, "", ""))


def build_artwork(record: dict[str, Any], *, source: str = "http") -> Artwork | None:
    """Normalise un enregistrement brut en Artwork, ou None si un champ obligatoire manque."""
    date_begin, date_end = parse_date_bounds(
        record.get("dated"), record.get("datebegin"), record.get("dateend")
    )
    try:
        raw_url = record.get("url")
        if not raw_url:
            raise ValueError("champ url absent de l'enregistrement")
        return Artwork(
            object_id=record["objectid"],
            object_number=(str(record["objectnumber"]).strip() if record.get("objectnumber") else None),
            title=record.get("title") or "",
            artists=extract_artists(record.get("people")),
            date_text=(record.get("dated") or "").strip() or None,
            date_begin=date_begin,
            date_end=date_end,
            classification=record.get("classification") or "",
            medium=(record.get("medium") or "").strip() or None,
            url=canonical_url(raw_url),
            scraped_at=datetime.now(UTC),
            source=source,
        )
    except (KeyError, TypeError, ValueError, ValidationError) as error:
        log_event(
            "item_rejected",
            object_id=record.get("objectid"),
            reason=str(error),
        )
        return None
