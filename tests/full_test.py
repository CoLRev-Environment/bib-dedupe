from pathlib import Path

import pandas as pd

import bib_dedupe.cluster
from bib_dedupe.bib_dedupe import block
from bib_dedupe.bib_dedupe import match
from bib_dedupe.bib_dedupe import merge
from bib_dedupe.bib_dedupe import prep


def test_full() -> None:
    benchmark_path = Path("tests/data")

    print(f"Dataset: {benchmark_path}")

    records_df = pd.read_csv("tests/data/records_pre_merged.csv")
    records_df = prep(records_df)

    # Bib-dedupe
    actual_blocked_df = block(records_df=records_df)
    matched_df = match(actual_blocked_df)
    duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)
    print(duplicate_id_sets)
    merged_df = merge(records_df, duplicate_id_sets=duplicate_id_sets)

    expected = {
        "id_0021834": "id_0021834;id_0022176",
        "id_0001432": "id_0001432;id_0025776",
        "id_0029057": "id_0029057",
        "id_0028740": "id_0028740",
        "id_0000728": "id_0000728;id_0000728NEW",
        "id_0000728B": "id_0000728B",
    }
    got = dict(merged_df[["ID", "origin"]].itertuples(index=False, name=None))
    assert got == expected
