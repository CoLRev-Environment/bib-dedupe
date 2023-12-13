#! /usr/bin/env python
"""Debug for dedupe"""
import typing

import pandas as pd


# TODO : pass columns that should be combined (with a separator - ; / , / LIST)
def merge(
    records_df: pd.DataFrame, *, duplicate_id_sets: typing.Optional[list] = None
) -> pd.DataFrame:
    if duplicate_id_sets is not None:
        to_drop = [o for ol in duplicate_id_sets for o in ol[1:]]
    else:
        raise NotImplementedError
    merged_df = records_df[~records_df["ID"].isin(to_drop)]
    return merged_df
