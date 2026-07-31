"""Client HTTP respectueux pour l'endpoint /browse de harvardartmuseums.org.

Cet endpoint est celui que la page https://harvardartmuseums.org/collections
appelle elle-meme en JavaScript pour afficher ses resultats (observe via
interception reseau Playwright, voir docs/cible.md). Il est public, ne demande
aucune authentification et ne transporte aucun secret de notre part.

Note ethique : la reponse de cet endpoint contient un champ "info.next" qui
expose une cle de l'API publique interne du musee (api.harvardartmuseums.org).
Cette cle appartient au musee, pas a nous : nous ne l'utilisons jamais, meme si
elle est techniquement lisible. Nous rejouons uniquement l'appel /browse tel
que la page elle-meme l'utilise, sans jamais toucher a cette cle.

La boucle de retry (statuts transitoires, backoff, Retry-After) vit desormais
dans le package partage `commun` (`commun.http_client`, utilise aussi par le
collecteur S18 du binome) : ce module se contente d'appeler ce moteur commun
avec un callback qui reproduit exactement les evenements deja journalises ici
(page_fetched, blocked, retry_scheduled, giving_up...), et de parser le JSON de
la reponse. `collect.py` n'a besoin d'aucune modification : meme signature,
meme contrat de retour (`dict | None`).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from commun.http_client import NON_RETRYABLE_STATUS, RETRYABLE_STATUS, fetch_with_retry as _fetch_with_retry

LOGGER = logging.getLogger("harvest")


def configure_logging() -> None:
    """Sortie JSON, une ligne par evenement (meme convention que les TP precedents)."""
    if LOGGER.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


def log_event(event: str, **payload: Any) -> None:
    configure_logging()
    LOGGER.info(json.dumps({"event": event, **payload}, ensure_ascii=False))


def build_client(base_url: str, user_agent: str) -> httpx.Client:
    return httpx.Client(
        base_url=base_url,
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_connections=1),
        headers={"User-Agent": user_agent, "Accept": "application/json"},
        follow_redirects=True,
    )


_EVENT_NAMES = {
    "request_error": "request_error",
    "fetched": "page_fetched",
    "retryable_status": "page_fetched",
    "blocked": "blocked",
    "retry_scheduled": "retry_scheduled",
    "giving_up": "giving_up",
}


def fetch_browse_page(
    client: httpx.Client,
    *,
    offset: int,
    load_amount: int,
    max_retries: int = 3,
    delay_s: float = 1.5,
) -> dict[str, Any] | None:
    """Recupere une page de resultats JSON, avec reprises bornees sur erreurs temporaires."""
    params = {"q": "", "offset": offset, "load_amount": load_amount}

    def on_event(event: str, payload: dict) -> None:
        name = _EVENT_NAMES.get(event)
        if name is not None:
            log_event(name, offset=offset, **payload)

    response = _fetch_with_retry(
        client,
        "/browse",
        params=params,
        max_retries=max_retries,
        delay_before_s=delay_s,
        on_event=on_event,
    )
    if response is None:
        return None
    try:
        return response.json()
    except json.JSONDecodeError as error:
        log_event("bad_json", offset=offset, error=str(error))
        return None
