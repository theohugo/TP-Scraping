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
"""

from __future__ import annotations

import json
import logging
import random
import time
from typing import Any

import httpx

RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})
NON_RETRYABLE_STATUS = frozenset({400, 401, 403, 404, 410})
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


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


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
    for attempt in range(max_retries + 1):
        time.sleep(delay_s)
        started = time.perf_counter()
        try:
            response = client.get("/browse", params=params)
        except httpx.TransportError as error:
            log_event("request_error", offset=offset, attempt=attempt + 1, error=str(error))
            response = None
        else:
            duration_ms = round((time.perf_counter() - started) * 1000)
            log_event(
                "page_fetched",
                url=str(response.url),
                status=response.status_code,
                duration_ms=duration_ms,
                attempt=attempt + 1,
            )
            if response.status_code in NON_RETRYABLE_STATUS:
                log_event("blocked", offset=offset, status=response.status_code)
                return None
            if response.status_code not in RETRYABLE_STATUS:
                try:
                    return response.json()
                except json.JSONDecodeError as error:
                    log_event("bad_json", offset=offset, error=str(error))
                    return None

        if attempt == max_retries:
            log_event("giving_up", offset=offset, attempts=attempt + 1)
            return None

        retry_after = _parse_retry_after(response.headers.get("Retry-After") if response else None)
        backoff_s = retry_after if retry_after is not None else float(2**attempt)
        backoff_s += random.uniform(0.0, 0.3 * backoff_s)
        log_event("retry_scheduled", offset=offset, attempt=attempt + 1, delay_s=round(backoff_s, 3))
        time.sleep(backoff_s)
    return None
