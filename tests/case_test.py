import json
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Set

import pandas as pd
import pytest

import bib_dedupe.cluster
from bib_dedupe.bib_dedupe import block
from bib_dedupe.bib_dedupe import match
from bib_dedupe.bib_dedupe import prep

# flake8: noqa


def _make_records_df(rec1: Dict[str, Any], rec2: Dict[str, Any]) -> pd.DataFrame:
    """Create a tiny records DataFrame with two BibTeX-style records."""
    rec1_full = {"record_id": "r1", **rec1}
    rec2_full = {"record_id": "r2", **rec2}
    return pd.DataFrame([rec1_full, rec2_full])


def _in_same_cluster(
    duplicate_id_sets: Iterable[Iterable[str]], a: str, b: str
) -> bool:
    """Return True if ids `a` and `b` appear together in at least one duplicate cluster."""
    target: Set[str] = {a, b}
    for group in duplicate_id_sets:
        if target.issubset(set(group)):
            return True
    return False


CASES_PATH = Path(__file__).parent / "test_cases.json"


def load_cases() -> list:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = data["cases"]
    # Each item here corresponds to one test invocation
    return [
        pytest.param(
            c["record_a"], c["record_b"], c["expected_duplicate"], id=c.get("id")
        )
        for c in cases
    ]


@pytest.mark.parametrize("record_a,record_b,expected_duplicate", load_cases())
def test_dedupe(record_a: dict, record_b: dict, expected_duplicate: bool) -> None:
    """Check if two BibTeX-like records are deduplicated as expected."""
    records_df = _make_records_df(record_a, record_b)

    prep_df = prep(records_df)
    pairs_df = block(records_df=prep_df)
    pairs_df.to_csv("EXPORT.csv")
    matched_df = match(pairs_df, verbosity_level=2)
    print(matched_df)

    duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)
    print(duplicate_id_sets)

    actual_match = _in_same_cluster(duplicate_id_sets, record_a["ID"], record_b["ID"])
    if actual_match == expected_duplicate:
        Path("EXPORT.csv").unlink()

    assert actual_match == expected_duplicate
