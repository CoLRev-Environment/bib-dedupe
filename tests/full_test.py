from pathlib import Path
import pandas as pd

import bib_dedupe.cluster
from bib_dedupe.bib_dedupe import block, match, merge, prep


def _normalize_groups(groups) -> set[frozenset[str]]:
    """Convert an iterable of iterables to a set of frozensets of trimmed strings."""
    norm = set()
    for g in groups:
        # g may be a list/set/tuple of IDs
        parts = {str(x).strip() for x in g if str(x).strip()}
        if parts:
            norm.add(frozenset(parts))
    return norm


def _load_expected_groups_from_csv(csv_path: Path) -> set[frozenset[str]]:
    """
    Read tests/data/merged_record_ids.csv with a single column 'merged_ids',
    where each row is a semicolon-delimited group (e.g., 'id_a;id_b;id_c').
    Only groups with length > 1 are considered.
    """
    df = pd.read_csv(csv_path)
    if "merged_ids" not in df.columns:
        raise ValueError("CSV must contain a 'merged_ids' column.")

    expected_groups = []
    for s in df["merged_ids"].astype(str):
        parts = [p.strip() for p in s.split(";") if p.strip()]
        if len(parts) > 1:
            expected_groups.append(parts)

    return _normalize_groups(expected_groups)


def test_full() -> None:
    benchmark_path = Path("tests/data")
    print(f"Dataset: {benchmark_path}")

    records_df = pd.read_csv(benchmark_path / "records_pre_merged.csv")
    records_df = prep(records_df)
    actual_blocked_df = block(records_df=records_df)
    matched_df = match(actual_blocked_df)

    # Get connected components and keep only true duplicate groups (>1)
    duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)
    print("Detected duplicate groups:", duplicate_id_sets)

    detected_groups = _normalize_groups(
        g for g in duplicate_id_sets if len(g) > 1
    )

    expected_groups = _load_expected_groups_from_csv(
        benchmark_path / "merged_record_ids.csv"
    )

    # Direct set equality: order within groups and across groups does not matter
    assert detected_groups == expected_groups, (
        "Mismatch in duplicate groups.\n"
        f"Only-in-expected: {expected_groups - detected_groups}\n"
        f"Only-in-detected: {detected_groups - expected_groups}"
    )

