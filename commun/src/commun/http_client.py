"""Moteur de retry HTTP partage entre les deux collecteurs.

Les deux projets (S18 catalogue GreenKart, S30 endpoint /browse Harvard Art Museums)
avaient chacun leur propre boucle de retry sur statuts transitoires (408/429/5xx),
avec backoff exponentiel et gigue : la logique etait dupliquee presque a l'identique.

Ce module ne decide jamais, a la place de l'appelant, de ce qu'il faut faire d'un
echec : il retourne `None` sur un statut definitif (4xx hors ceux consideres
transitoires), sur un budget de tentatives epuise, ou sur une erreur de transport
persistante - libre a chaque collecteur de lever une exception ou de continuer,
selon son propre contrat (voir greenkart_scraper/http_client.py et
harvest/acquisition.py, qui adaptent chacun ce moteur a leur comportement existant).

Un callback optionnel `on_event(nom, payload)` permet a chaque appelant de journaliser
a sa maniere (logs texte horodates cote S18, evenements JSON structures cote S30) sans
dupliquer la boucle elle-meme.
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable

import httpx

RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})
NON_RETRYABLE_STATUS = frozenset({400, 401, 403, 404, 410})

EventCallback = Callable[[str, dict[str, Any]], None]


def parse_retry_after(value: str | None) -> float | None:
    """Interprete l'en-tete Retry-After (secondes) s'il est present et valide."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def fetch_with_retry(
    client: httpx.Client,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
    delay_before_s: float = 0.0,
    max_backoff_s: float = 10.0,
    on_event: EventCallback | None = None,
) -> httpx.Response | None:
    """GET avec un nombre borne de tentatives sur les statuts transitoires.

    Retourne la reponse HTTP des qu'un statut n'est ni transitoire ni definitif
    (typiquement un succes), ou `None` si :
    - un statut definitif (`NON_RETRYABLE_STATUS`) est recu ;
    - le budget de tentatives (`max_retries`) est epuise ;
    - une erreur de transport persiste jusqu'a epuisement du budget.

    `delay_before_s` est un delai de politesse applique avant chaque tentative
    (y compris la premiere), independant du backoff sur erreur. Le backoff respecte
    l'en-tete `Retry-After` quand il est present, sinon un exponentiel plafonne a
    `max_backoff_s`, avec une gigue aleatoire de 0 a 30 %.
    """

    def emit(event: str, **payload: Any) -> None:
        if on_event is not None:
            on_event(event, payload)

    response: httpx.Response | None = None
    for attempt in range(max_retries + 1):
        if delay_before_s:
            time.sleep(delay_before_s)
        started = time.perf_counter()
        try:
            response = client.get(url, params=params)
        except httpx.TransportError as error:
            emit("request_error", attempt=attempt + 1, error=str(error))
            response = None
        else:
            duration_ms = round((time.perf_counter() - started) * 1000)
            if response.status_code in NON_RETRYABLE_STATUS:
                emit("blocked", status=response.status_code, attempt=attempt + 1, duration_ms=duration_ms)
                return None
            if response.status_code not in RETRYABLE_STATUS:
                emit(
                    "fetched",
                    status=response.status_code,
                    url=str(response.url),
                    attempt=attempt + 1,
                    duration_ms=duration_ms,
                )
                return response
            emit("retryable_status", status=response.status_code, attempt=attempt + 1, duration_ms=duration_ms)

        if attempt == max_retries:
            emit("giving_up", attempts=attempt + 1)
            return None

        retry_after = parse_retry_after(response.headers.get("Retry-After")) if response is not None else None
        backoff_s = retry_after if retry_after is not None else min(2**attempt, max_backoff_s)
        backoff_s += random.uniform(0.0, 0.3 * backoff_s)
        emit("retry_scheduled", attempt=attempt + 1, delay_s=round(backoff_s, 3))
        time.sleep(backoff_s)
    return None
