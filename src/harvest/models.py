"""Contrat Artwork : l'objet metier collecte depuis Harvard Art Museums Collections."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl, field_validator


class Artwork(BaseModel):
    """Une oeuvre du catalogue, normalisee et prete pour l'export.

    object_id est l'identifiant stable : c'est la cle primaire interne du musee,
    presente dans chaque enregistrement et dans l'URL de la fiche. Elle ne change
    pas d'une collecte a l'autre, contrairement a une position de page.
    """

    object_id: int
    object_number: str | None
    title: str
    artists: list[str]
    date_text: str | None
    date_begin: int | None
    date_end: int | None
    classification: str
    medium: str | None
    url: HttpUrl
    scraped_at: datetime
    source: Literal["http"]

    @field_validator("title", "classification")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("champ obligatoire vide")
        return value.strip()
