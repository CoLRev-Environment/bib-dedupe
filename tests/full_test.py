from collections.abc import Iterable
from itertools import combinations
from pathlib import Path

import pandas as pd
import pytest

import bib_dedupe.cluster
from bib_dedupe.bib_dedupe import block
from bib_dedupe.bib_dedupe import match
from bib_dedupe.bib_dedupe import prep

ID_COL = "ID"

BENCHMARK_DIR = Path("tests/ldd-full-benchmark")

MAX_FP_CASES_TO_PRINT = 50
MAX_FP_DIAGNOSTICS = 20


def _normalize_groups(groups: Iterable[Iterable[str]]) -> set[frozenset[str]]:
    """Convert an iterable of iterables to a set of frozensets of trimmed strings."""
    norm = set()
    for g in groups:
        parts = {str(x).strip() for x in g if str(x).strip()}
        if parts:
            norm.add(frozenset(parts))
    return norm


def _load_expected_groups_from_csv(csv_path: Path) -> set[frozenset[str]]:
    """
    Read merged_record_ids.csv with a single column 'merged_ids',
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


def _pairs_from_groups(groups: set[frozenset[str]]) -> set[frozenset[str]]:
    """Expand groups into unordered 2-item pairs."""
    pairs: set[frozenset[str]] = set()
    for g in groups:
        for a, b in combinations(g, 2):
            pairs.add(frozenset((a, b)))
    return pairs


def _benchmark_paths() -> list[Path]:
    return sorted(p for p in BENCHMARK_DIR.iterdir() if p.is_dir() and p.name != ".git")


def _load_records_df(benchmark_path: Path) -> pd.DataFrame:
    if benchmark_path.name == "depression":
        part_paths = sorted(benchmark_path.glob("records_pre_merged_part*.csv"))
        if not part_paths:
            raise FileNotFoundError(
                f"No part files found for 'depression' in {benchmark_path}"
            )
        return pd.concat((pd.read_csv(p) for p in part_paths), ignore_index=True)

    return pd.read_csv(benchmark_path / "records_pre_merged.csv")


def _assert_id_column(records_df: pd.DataFrame) -> None:
    if ID_COL not in records_df.columns:
        raise KeyError(
            f"Expected an ID column '{ID_COL}' in records_df. "
            f"Available columns: {sorted(records_df.columns)}"
        )


def _rerun_pair_with_diagnostics(records_df: pd.DataFrame, a: str, b: str) -> None:
    """Run the pipeline on just the two records with verbosity_level=2."""
    _assert_id_column(records_df)

    subset = records_df[records_df[ID_COL].astype(str).isin([a, b])].copy()
    print("\n" + "=" * 80)
    print(f"DIAGNOSTICS for false-positive pair: ({a}, {b})")
    print(f"Selected rows: {len(subset)}")

    missing = {a, b} - set(subset[ID_COL].astype(str))
    if missing:
        print(f"WARNING: could not find IDs in records_df: {sorted(missing)}")
        print("=" * 80 + "\n")
        return

    # Rerun with high verbosity
    subset = prep(subset, verbosity_level=2)
    blocked = block(records_df=subset, verbosity_level=2)
    matched = match(blocked, verbosity_level=2)

    print("Matched rows (top):")
    try:
        print(matched.head(50).to_string(index=False))
    except Exception:
        print(matched.head(50))
    print("=" * 80 + "\n")


@pytest.mark.parametrize("benchmark_path", _benchmark_paths(), ids=lambda p: p.name)
def test_full_benchmark(benchmark_path: Path) -> None:
    print(f"Dataset: {benchmark_path}")

    try:
        records_df = _load_records_df(benchmark_path)
        _assert_id_column(records_df)

        records_df_prepped = prep(records_df, verbosity_level=0)
        actual_blocked_df = block(records_df=records_df_prepped, verbosity_level=0)
        matched_df = match(actual_blocked_df, verbosity_level=0)

        duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)
        detected_groups = _normalize_groups(g for g in duplicate_id_sets if len(g) > 1)

        expected_groups = _load_expected_groups_from_csv(
            benchmark_path / "merged_record_ids.csv"
        )

        detected_pairs = _pairs_from_groups(detected_groups)
        expected_pairs = _pairs_from_groups(expected_groups)

        false_positives = detected_pairs - expected_pairs
        if false_positives:
            fp_examples = sorted([tuple(sorted(p)) for p in false_positives])[:20]

            # rerun diagnostics for (up to) the first 20 false-positive pairs
            for a, b in fp_examples:
                _rerun_pair_with_diagnostics(records_df, a, b)

            raise AssertionError(
                "False positives: merged IDs not in the same expected group.\n"
                f"Count: {len(false_positives)}\n"
                f"Examples (up to 20): {fp_examples}\n"
                "Diagnostics printed above for the shown examples."
            )

    finally:
        # ---- always print summary stats ----
        fp_cases = sorted([tuple(sorted(p)) for p in false_positives])[
            :MAX_FP_CASES_TO_PRINT
        ]

        print("\n" + "-" * 80)
        print(f"SUMMARY for dataset: {benchmark_path.name}")
        print(f"Detected pairs: {len(detected_pairs)}")
        print(f"Expected pairs: {len(expected_pairs)}")
        print(f"False positives: {len(false_positives)}")

        if fp_cases:
            print(f"False-positive cases (up to {MAX_FP_CASES_TO_PRINT}):")
            for a, b in fp_cases:
                print(f"  - {a} <> {b}")
        else:
            print("False-positive cases: none")

        print("-" * 80 + "\n")
