"""Client HTTP partage : un seul client reutilise, delais explicites,
retries bornes aux codes reellement transitoires (module 02/04 du cours).
"""

from __future__ import annotations

import logging
import random
import time

import httpx

logger = logging.getLogger("greenkart_scraper")

USER_AGENT = "GreenkartTPScraper/1.0 (TP individuel formation scraping; contact: aminetaleb18@gmail.com)"
TIMEOUT = httpx.Timeout(10.0, connect=5.0)
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


def build_client() -> httpx.Client:
    """Client HTTP unique pour toute la session de collecte."""
    return httpx.Client(
        timeout=TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )


def fetch_with_retry(client: httpx.Client, url: str, max_retries: int) -> httpx.Response:
    """GET avec un nombre borne de tentatives sur les statuts transitoires.

    Backoff exponentiel plafonne avec jitter (module04-antibot-robustesse,
    chapitre throttling). Un 4xx definitif (404, 403...) leve immediatement :
    on ne rejoue jamais une erreur qui ne changera pas au prochain essai.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            response = client.get(url)
        except httpx.TransportError as exc:
            if attempt > max_retries:
                raise
            logger.warning("erreur transport (essai %d/%d): %s", attempt, max_retries, exc)
        else:
            if response.status_code not in RETRYABLE_STATUS:
                response.raise_for_status()
                return response
            if attempt > max_retries:
                response.raise_for_status()
            logger.warning(
                "statut %d transitoire (essai %d/%d) sur %s",
                response.status_code,
                attempt,
                max_retries,
                url,
            )
        wait = min(0.5 * (2 ** (attempt - 1)), 10.0) + random.uniform(0, 0.3)
        time.sleep(wait)
