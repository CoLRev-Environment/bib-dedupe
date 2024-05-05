"""Create benchmark dataset from colrev project"""
from pathlib import Path

import evaluation

from bib_dedupe.dedupe_benchmark import DedupeBenchmarker

# Create benchmark dataset from history

dedupe_benchmark = DedupeBenchmarker(
    colrev_project_path=Path(".../dec-proc-ex-colrev"),
    benchmark_path=Path("../tests/data/digital_work"),
    regenerate_benchmark_from_history=True,
)

# Export for pytests

evaluation.export_for_pytest(
    records_df=dedupe_benchmark.records_pre_merged_df,
    true_merged_ids=dedupe_benchmark.true_merged_ids,
    benchmark_path=Path("../tests/data/wagner2021"),
)
