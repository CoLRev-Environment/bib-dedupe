#! /usr/bin/env python
"""Debug for dedupe"""
import pprint

import pandas as pd

from bib_dedupe.bib_dedupe import prep


def debug() -> None:
    try:
        df_blocks = pd.read_csv("blocks_FN_list.csv")
    except (pd.errors.EmptyDataError, FileNotFoundError):
        df_blocks = pd.DataFrame()

    try:
        df_matches = pd.read_csv("matches_FN_list.csv")
    except pd.errors.EmptyDataError:
        df_matches = pd.DataFrame()

    try:
        df_matches_fp = pd.read_csv("matches_FP_list.csv")
    except pd.errors.EmptyDataError:
        df_matches_fp = pd.DataFrame()

    from bib_dedupe.dedupe_benchmark import DedupeBenchmarker
    from bib_dedupe.bib_dedupe import block, match
    from pathlib import Path

    dedupe_benchmark = DedupeBenchmarker(benchmark_path=Path.cwd())

    records_df = dedupe_benchmark.get_records_for_dedupe()
    records_df = prep(records_df)

    p_printer = pprint.PrettyPrinter(indent=4, width=140, compact=False)

    while True:
        id_pair = input("id_pair:")

        try:
            if "case" in df_blocks.columns and id_pair in df_blocks["case"].values:
                print(f"ID pair {id_pair} found in blocks_FN_list.csv")
            if "case" in df_matches.columns and id_pair in df_matches["case"].values:
                print(f"ID pair {id_pair} found in matches_FN_list.csv")
            if (
                "case" in df_matches_fp.columns
                and id_pair in df_matches_fp["case"].values
            ):
                print(f"ID pair {id_pair} found in matches_FP_list.csv")

            id1, id2 = id_pair.split(";")
            selected_prepared_records_df = records_df[
                records_df["ID"].apply(lambda x: id1 == x or id2 == x)
            ]

            if selected_prepared_records_df.empty:
                print("selected_prepared_records_df is empty. Continuing...")
                continue

            actual_blocked_df = block(records_df=selected_prepared_records_df)
            matches = match(actual_blocked_df, debug=True)
            p_printer.pprint(matches)
        except ValueError as exc:
            print(exc)
