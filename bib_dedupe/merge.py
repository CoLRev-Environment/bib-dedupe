#! /usr/bin/env python
"""Debug for dedupe"""
import pandas as pd


def merge(records_df: pd.DataFrame, matches: dict) -> pd.DataFrame:
    to_drop = [o for ol in matches["duplicate_origin_sets"] for o in ol[1:]]
    merged_df = records_df[~records_df["colrev_origin"].isin(to_drop)]
    return merged_df
