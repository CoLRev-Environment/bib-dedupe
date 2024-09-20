from datetime import datetime
from pathlib import Path

import bib_dedupe.cluster
from bib_dedupe.bib_dedupe import block
from bib_dedupe.bib_dedupe import match
from bib_dedupe.bib_dedupe import merge
from bib_dedupe.bib_dedupe import prep
from bib_dedupe.dedupe_benchmark import DedupeBenchmarker


def test_full() -> None:
    benchmark_path = Path("tests/data")

    print(f"Dataset: {benchmark_path}")

    dedupe_benchmark = DedupeBenchmarker(benchmark_path=benchmark_path)

    records_df = dedupe_benchmark.get_records_for_dedupe()
    records_df = prep(records_df)

    # Bib-dedupe
    timestamp = datetime.now()
    actual_blocked_df = block(records_df=records_df)
    matched_df = match(actual_blocked_df)
    duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)
    print(duplicate_id_sets)
    merged_df = merge(records_df, duplicate_id_sets=duplicate_id_sets)

    result = dedupe_benchmark.compare_dedupe_id(
        records_df=records_df, merged_df=merged_df, timestamp=timestamp
    )

    assert not any(
        [x for x in duplicate_id_sets if "id_0000728" in x and "id_0000728B" in x]
    ), "Cannot merge records from same set (id_0000728,id_0000728B)"
    assert result["TP"] == 3
    assert result["FP"] == 0
    assert result["FN"] == 0
    assert result["TN"] == 6
