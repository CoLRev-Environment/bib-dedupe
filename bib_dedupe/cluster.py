#! /usr/bin/env python
"""Cluster for dedupe"""
import pandas as pd

import bib_dedupe.util


# def get_connected_components(id_sets: list) -> list:
#     return bib_dedupe.util.connected_components(id_sets=id_sets)


def get_connected_components(
    duplicates_df: pd.DataFrame, label: str = "duplicate"
) -> list:
    if duplicates_df.empty:
        return []

    duplicates_df = duplicates_df[duplicates_df["duplicate_label"] == label]
    id_sets = duplicates_df[["ID_1", "ID_2"]].values.tolist()

    return bib_dedupe.util.connected_components(id_sets=id_sets)
