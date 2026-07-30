"""Script de controle : rejoue l'extraction sur une page enregistree, sans reseau.

Usage (depuis la racine du depot) :
    python verif/verif.py

Trois controles, chacun affiche OK ou ECHEC :
  1. nombre d'objets extraits d'une page de resultats enregistree ;
  2. une normalisation (bornes de date, avec repli sur texte libre) ;
  3. la deduplication par identifiant stable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from harvest.extraction import build_artwork, parse_date_bounds  # noqa: E402
from harvest.models import Artwork  # noqa: E402
from harvest.storage import dedupe_artworks  # noqa: E402

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "browse_page_sample.json"


def check_extraction_count() -> tuple[bool, list[Artwork]]:
    """La page enregistree contient 7 enregistrements bruts : 6 valides, 1 incomplet (titre absent)."""
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    records = payload["records"]
    artworks = [build_artwork(record) for record in records]
    valid = [artwork for artwork in artworks if artwork is not None]
    expected_seen = 7
    expected_valid = 6
    ok = len(records) == expected_seen and len(valid) == expected_valid
    print(
        f"[1] extraction sur page enregistree : {len(records)} vus, {len(valid)} valides "
        f"(attendu {expected_seen} vus, {expected_valid} valides) -> {'OK' if ok else 'ECHEC'}"
    )
    return ok, valid


def check_date_normalization() -> bool:
    """parse_date_bounds doit : (a) lire un repli BCE depuis le texte libre quand les bornes
    numeriques sont absentes, et (b) rejeter des bornes incoherentes plutot que les garder."""
    fallback_begin, fallback_end = parse_date_bounds("about 450 BCE", None, None)
    case_a_ok = fallback_begin == -450 and fallback_end == -450

    inconsistent_begin, inconsistent_end = parse_date_bounds("texte sans importance", 1900, 1800)
    case_b_ok = inconsistent_begin is None and inconsistent_end is None

    ok = case_a_ok and case_b_ok
    print(
        f"[2] normalisation de date : repli texte -> ({fallback_begin}, {fallback_end}) attendu (-450, -450) ; "
        f"bornes incoherentes -> ({inconsistent_begin}, {inconsistent_end}) attendu (None, None) "
        f"-> {'OK' if ok else 'ECHEC'}"
    )
    return ok


def check_deduplication(valid_artworks: list[Artwork]) -> bool:
    """Sur les 6 artworks valides, un est un doublon volontaire du premier (meme object_id)."""
    unique, duplicates = dedupe_artworks(valid_artworks)
    ok = len(unique) == 5 and duplicates == 1
    print(
        f"[3] deduplication par object_id : {len(unique)} uniques, {duplicates} doublon(s) "
        f"(attendu 5 uniques, 1 doublon) -> {'OK' if ok else 'ECHEC'}"
    )
    return ok


def main() -> int:
    ok1, valid_artworks = check_extraction_count()
    ok2 = check_date_normalization()
    ok3 = check_deduplication(valid_artworks)

    all_ok = ok1 and ok2 and ok3
    print()
    print("Resultat global :", "OK" if all_ok else "ECHEC")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
