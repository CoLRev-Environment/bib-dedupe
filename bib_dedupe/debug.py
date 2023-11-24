#! /usr/bin/env python
"""Debug for dedupe"""
import pandas as pd


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

    from colrev.ops.dedupe_benchmark import DedupeBenchmarker
    from bib_dedupe.bib_dedupe import BibDeduper
    from pathlib import Path

    dedupe_benchmark = DedupeBenchmarker(
        benchmark_path=Path.cwd(),
    )
    records_df = dedupe_benchmark.get_records_for_dedupe()

    while True:
        origin_pair = input("origin_pair:")

        dedupe_instance = BibDeduper()
        dedupe_instance.debug = True  # to print details

        try:
            if "case" in df_blocks.columns and origin_pair in df_blocks["case"].values:
                print(f"Origin pair {origin_pair} found in blocks_FN_list.csv")
            if (
                "case" in df_matches.columns
                and origin_pair in df_matches["case"].values
            ):
                print(f"Origin pair {origin_pair} found in matches_FN_list.csv")
            if (
                "case" in df_matches_fp.columns
                and origin_pair in df_matches_fp["case"].values
            ):
                print(f"Origin pair {origin_pair} found in matches_FP_list.csv")

            origin1, origin2 = origin_pair.split(";")
            selected_prepared_records_df = records_df[
                records_df["colrev_origin"].apply(
                    lambda x: origin1 in x or origin2 in x
                )
            ]

            if selected_prepared_records_df.empty:
                print("selected_prepared_records_df is empty. Continuing...")
                continue

            actual_blocked_df = dedupe_instance.block_pairs_for_deduplication(
                records_df=selected_prepared_records_df
            )
            matches = dedupe_instance.identify_true_matches(actual_blocked_df)
            print(matches)
        except ValueError as exc:
            print(exc)
