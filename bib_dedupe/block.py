#! /usr/bin/env python
"""Block for dedupe"""
import multiprocessing
from itertools import combinations

import pandas as pd
from colrev.constants import Fields


def block(records_df: pd.DataFrame) -> pd.DataFrame:
    pairs_df = pd.DataFrame(columns=["ID1", "ID2"])

    # container_title instead of journal
    block_fields_list = [
        # Redundant with [Fields.AUTHOR, Fields.YEAR]:
        # [Fields.AUTHOR, Fields.YEAR, Fields.PAGES],
        # Note: the original "ISBN" blocking rule was very inefficient
        [Fields.DOI],
        [Fields.URL],
        ["first_author", Fields.YEAR],
        [Fields.TITLE, Fields.PAGES],
        [Fields.TITLE, "first_author"],
        [Fields.TITLE, Fields.ABSTRACT],
        [Fields.TITLE, Fields.VOLUME],
        [Fields.TITLE, "short_container_title"],
        ["first_author", "short_container_title"],
        [Fields.TITLE, Fields.YEAR],
        [Fields.YEAR, Fields.VOLUME, Fields.NUMBER],
        [Fields.YEAR, Fields.VOLUME, Fields.PAGES],
        [Fields.YEAR, Fields.NUMBER, Fields.PAGES],
        [
            Fields.ISBN,
            Fields.VOLUME,
            Fields.NUMBER,
        ],
        [
            Fields.ISBN,
            Fields.VOLUME,
            Fields.YEAR,
        ],
        [
            Fields.ISBN,
            Fields.VOLUME,
            Fields.PAGES,
        ],
        [
            "short_container_title",
            Fields.VOLUME,
            Fields.NUMBER,
        ],
        [
            "short_container_title",
            Fields.VOLUME,
            Fields.YEAR,
        ],
        [
            "short_container_title",
            Fields.VOLUME,
            Fields.PAGES,
        ],
        # TODO : conferences, books, ...
    ]

    pool = multiprocessing.Pool()
    results = pool.starmap(
        calculate_pairs, [(records_df, field) for field in block_fields_list]
    )
    pool.close()
    pool.join()

    pairs_df = pd.concat(results, ignore_index=True)

    pairs_df = pairs_df.drop_duplicates()

    # Obtain metadata for matching pairs
    pairs_df = pd.merge(
        pairs_df,
        records_df.add_suffix("_1"),
        left_on="ID1",
        right_on="ID_1",
        how="left",
        suffixes=("", "_1"),
    )

    pairs_df = pd.merge(
        pairs_df,
        records_df.add_suffix("_2"),
        left_on="ID2",
        right_on="ID_2",
        how="left",
        suffixes=("", "_2"),
    )

    return pairs_df


def create_pairs_for_block_fields(
    records_df: pd.DataFrame, block_fields: list
) -> pd.DataFrame:
    """
    Create pairs for block fields.

    Parameters:
    records_df (pd.DataFrame): The dataframe containing the records.
    block_fields (list): The list of block fields.

    Returns:
    pd.DataFrame: The dataframe containing the blocked pairs.
    """
    # Pre-select rows where the block_fields columns are not ""
    non_empty_rows = records_df[block_fields].apply(lambda x: x != "").all(axis=1)
    grouped = (
        records_df[non_empty_rows]
        .groupby(list(block_fields), group_keys=True)["ID"]
        .apply(lambda x: pd.DataFrame(list(combinations(x, 2)), columns=["ID1", "ID2"]))
        .reset_index(drop=True)
    )
    print(f"Blocked {str(grouped.shape[0]).rjust(8)} pairs with {block_fields}")
    return grouped


def calculate_pairs(records_df: pd.DataFrame, block_fields: list) -> pd.DataFrame:
    """
    Calculate pairs for deduplication.

    Parameters:
    records_df (pd.DataFrame): The dataframe containing the records.
    block_fields (list): The list of block fields.

    Returns:
    pd.DataFrame: The dataframe containing the calculated pairs.
    """
    if not all(x in records_df.columns for x in block_fields):
        return pd.DataFrame(columns=["ID1", "ID2"])
    pairs = create_pairs_for_block_fields(records_df, block_fields)
    return pairs
