"""Client HTTP partage : un seul client reutilise, delais explicites,
retries bornes aux codes reellement transitoires (module 02/04 du cours).

La boucle de retry elle-meme vit desormais dans le package partage `commun`
(`commun.http_client`, utilise aussi par le collecteur S30 du binome) : ce module
ne fait plus qu'adapter ce moteur commun au contrat deja en place ici (lever une
exception bruyante sur echec definitif, plutot que retourner `None`), pour que
`acquisition.py` n'ait besoin d'aucune modification.
"""

from __future__ import annotations

import logging

import httpx

from commun.http_client import RETRYABLE_STATUS, fetch_with_retry as _fetch_with_retry

logger = logging.getLogger("greenkart_scraper")

USER_AGENT = "GreenkartTPScraper/1.0 (TP individuel formation scraping; contact: aminetaleb18@gmail.com)"
TIMEOUT = httpx.Timeout(10.0, connect=5.0)

__all__ = ["RETRYABLE_STATUS", "build_client", "fetch_with_retry"]


def build_client() -> httpx.Client:
    """Client HTTP unique pour toute la session de collecte."""
    return httpx.Client(
        timeout=TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )


def _log_event(event: str, payload: dict) -> None:
    # "fetched" = requete reussie du premier coup : pas un evenement anormal,
    # on ne le journalise pas (comme avant la fusion). Tout le reste (erreur
    # transport, statut transitoire, backoff, abandon) reste un WARNING.
    if event == "fetched":
        return
    logger.warning("%s: %s", event, payload)


def fetch_with_retry(client: httpx.Client, url: str, max_retries: int) -> httpx.Response:
    """GET avec un nombre borne de tentatives sur les statuts transitoires.

    Un 4xx definitif (404, 403...) ou un budget de tentatives epuise leve une
    exception : on ne rejoue jamais une erreur qui ne changera pas au prochain
    essai, et on ne produit jamais un enregistrement silencieusement incomplet.
    """
    response = _fetch_with_retry(client, url, max_retries=max_retries, on_event=_log_event)
    if response is None:
        raise RuntimeError(f"echec definitif de la requete sur {url} (voir logs pour le detail)")
    response.raise_for_status()
    return response
