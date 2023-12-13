from datetime import datetime
from pathlib import Path

import bib_dedupe.cluster
from bib_dedupe.bib_dedupe import BibDeduper
from bib_dedupe.dedupe_benchmark import DedupeBenchmarker


def test_full() -> None:
    benchmark_path = Path("tests/data")

    print(f"Dataset: {benchmark_path}")

    merge_updated_papers = True

    dedupe_benchmark = DedupeBenchmarker(
        benchmark_path=benchmark_path, merge_updated_papers=merge_updated_papers
    )

    records_df = dedupe_benchmark.get_records_for_dedupe()

    # Bib-dedupe
    dedupe_instance = BibDeduper()
    timestamp = datetime.now()
    actual_blocked_df = dedupe_instance.block(records_df=records_df)
    matched_df = dedupe_instance.match(
        actual_blocked_df, merge_updated_papers=merge_updated_papers
    )
    duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)
    print(duplicate_id_sets)
    merged_df = dedupe_instance.merge(records_df, duplicate_id_sets=duplicate_id_sets)

    result = dedupe_benchmark.compare_dedupe_id(
        records_df=records_df, merged_df=merged_df, timestamp=timestamp
    )

    assert result["TP"] == 2
    assert result["FP"] == 0
    assert result["FN"] == 0
    assert result["TN"] == 4
