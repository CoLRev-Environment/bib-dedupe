#! /usr/bin/env python
"""Debug for dedupe"""
import pandas as pd


# TODO : pass columns that should be combined (with a separator - ; / , / LIST)
def merge(records_df: pd.DataFrame, matches: dict) -> pd.DataFrame:
    to_drop = [o for ol in matches["duplicate_id_sets"] for o in ol[1:]]
    merged_df = records_df[~records_df["ID"].isin(to_drop)]
    return merged_df
