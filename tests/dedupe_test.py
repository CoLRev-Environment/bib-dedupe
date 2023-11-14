#!/usr/bin/env python
"""Test the dedupe standard package"""
from pathlib import Path

import colrev.ops.dedupe_benchmark

import bib_dedupe.bib_dedupe


def dedupe_dataset(dir: Path) -> None:
    dedupe_instance = bib_dedupe.bib_dedupe.BibDeduper()

    dedupe_benchmark = colrev.ops.dedupe_benchmark.DedupeBenchmarker(
        #
        # benchmark_path=helpers.test_data_path / Path("dedupe_package"),
        benchmark_path=dir,
        colrev_project_path=Path.cwd(),
    )

    # Blocking
    actual_blocked_df = dedupe_instance.block_pairs_for_deduplication(
        records_df=dedupe_benchmark.get_records_for_dedupe()
    )
    matches = dedupe_instance.identify_true_matches(actual_blocked_df)

    results = dedupe_benchmark.compare(
        predicted=matches["duplicate_origin_sets"], blocked_df=actual_blocked_df
    )

    assert results["matches"]["FP"] == 0

    # TODO : switch to origins (instead of IDs)
    # TODO : remove fields form test-records (anonymize origins)

    # TODO : maybe_pairs

    # print(true_matches)
    # raise FileNotFoundError


# @pytest.mark.slow
def test_dedupe(helpers) -> None:  # type: ignore
    """Test the dedupe standard package"""

    # Workaround because parameterize happens before fixtures are available
    for dir in [d for d in helpers.test_data_path.iterdir() if d.is_dir()]:
        dedupe_dataset(Path(dir))
