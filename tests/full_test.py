from itertools import combinations
from pathlib import Path

import pandas as pd

import bib_dedupe.cluster
from bib_dedupe.bib_dedupe import block
from bib_dedupe.bib_dedupe import match
from bib_dedupe.bib_dedupe import prep


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


def _pairs_from_groups(groups: set[frozenset[str]]) -> set[frozenset[str]]:
    """Expand groups into unordered 2-item pairs."""
    pairs: set[frozenset[str]] = set()
    for g in groups:
        for a, b in combinations(g, 2):
            pairs.add(frozenset((a, b)))
    return pairs


# TODO : replace by core once ready?
def test_full_benchmark() -> None:
    benchmark_dir = Path("tests/ldd-full-benchmark")
    for benchmark_path in sorted(
        p for p in benchmark_dir.iterdir() if p.is_dir() and p.name != ".git"
    ):
        # if benchmark_path.name not in ["srsrs", "depression"]:
        #      continue

        print(f"Dataset: {benchmark_path}")
        if benchmark_path.name == "depression":
            # Load all matching parts (e.g., records_pre_merged_part1.csv, part2.csv)
            part_paths = sorted(benchmark_path.glob("records_pre_merged_part*.csv"))
            if not part_paths:
                raise FileNotFoundError(
                    "No part files found for 'depression' in " f"{benchmark_path}"
                )
            records_df = pd.concat(
                (pd.read_csv(p) for p in part_paths), ignore_index=True
            )

        else:
            records_df = pd.read_csv(benchmark_path / "records_pre_merged.csv")
        records_df = prep(records_df)
        actual_blocked_df = block(records_df=records_df)
        matched_df = match(actual_blocked_df)

        # Get connected components and keep only duplicate groups (>1)
        duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)
        detected_groups = _normalize_groups(g for g in duplicate_id_sets if len(g) > 1)

        expected_groups = _load_expected_groups_from_csv(
            benchmark_path / "merged_record_ids.csv"
        )

        # Compare on pairs to catch only false positives
        detected_pairs = _pairs_from_groups(detected_groups)
        expected_pairs = _pairs_from_groups(expected_groups)

        false_positives = detected_pairs - expected_pairs
        if false_positives:
            # Optional: show which detected groups contain the offending pairs
            fp_examples = sorted([tuple(sorted(p)) for p in false_positives])[:20]
            raise AssertionError(
                "False positives: merged IDs not in the same expected group.\n"
                f"Count: {len(false_positives)}\n"
                f"Examples (up to 20): {fp_examples}"
            )

        # If you still want visibility into misses without failing:
        # false_negatives = expected_pairs - detected_pairs
        # print(f"Missed pairs (not failing): {len(false_negatives)}")
