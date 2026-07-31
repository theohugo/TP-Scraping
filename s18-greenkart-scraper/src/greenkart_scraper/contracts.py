"""Contrats de donnees du collecteur GreenKart (cible TP S18).

Deux objets metier :
- `Product` : le catalogue principal (30 articles, endpoint JSON statique).
- `Deal`    : les offres de la page "Top Deals" (exigence complementaire de la
  fiche de cible S18), obtenues par navigateur car aucun endpoint JSON n'a
  ete trouve pour cette table (voir docs/architecture.md, section diagnostic).

Les deux modeles sont valides a la construction : un champ manquant ou
incoherent leve une erreur Pydantic plutot que de produire un enregistrement
silencieusement incomplet.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, HttpUrl


def utc_now() -> datetime:
    """Horodatage courant, toujours en UTC et timezone-aware."""
    return datetime.now(UTC)


class Product(BaseModel):
    """Un article du catalogue GreenKart (fruits, legumes, fruits secs).

    Regle d'identifiant : `sku` = "GK-{id:03d}" ou `id` est le champ entier
    fourni par la source (data/products.json). Ce champ est le seul
    identifiant stable expose par le site ; il est prefixe pour eviter toute
    collision avec un autre catalogue si les jeux de donnees sont un jour
    fusionnes.
    """

    sku: str
    name: str
    unit: Literal["kg", "quarter_kg", "piece"]
    quantity_step: int
    price: Decimal
    currency: str = "INR"
    category: str
    image_url: HttpUrl
    url: HttpUrl
    scraped_at: datetime
    source: Literal["http", "browser", "api", "llm"]


class Deal(BaseModel):
    """Une ligne de la table "Top Deals" (page /#/offers).

    Regle d'identifiant : la table source n'expose aucun identifiant propre
    (ni id, ni SKU). `deal_id` est donc construit par slug du nom - regle
    documentee, a distinguer d'un vrai identifiant metier. Les 19 lignes
    observees portent des noms tous distincts (voir docs/architecture.md) ;
    en cas de collision future, le doublon serait rejete par la
    deduplication plutot que d'ecraser silencieusement une ligne.
    """

    deal_id: str
    name: str
    price: Decimal
    discount_price: Decimal
    currency: str = "INR"
    page: int
    url: HttpUrl
    scraped_at: datetime
    source: Literal["http", "browser", "api", "llm"]
