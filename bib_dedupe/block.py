#! /usr/bin/env python
"""Block for dedupe"""
import multiprocessing
import time
from datetime import datetime
from itertools import combinations

import numpy as np
import pandas as pd

from bib_dedupe.constants import Fields


# container_title instead of journal
block_fields_list = [
    # Redundant with [Fields.AUTHOR, Fields.YEAR]:
    # [Fields.AUTHOR, Fields.YEAR, Fields.PAGES],
    # Note: the original "ISBN" blocking rule was very inefficient
    ["doi_hash"],
    [Fields.URL],
    ["first_author", Fields.YEAR],
    ["short_title", Fields.PAGES],
    ["short_title", "first_author"],
    ["short_title", Fields.ABSTRACT],
    ["short_title", Fields.VOLUME],
    ["short_title", "short_container_title"],
    ["first_author", "short_container_title"],
    ["short_title", Fields.YEAR],
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


def get_short_container_title(ct_array: np.array) -> np.array:
    return np.array(
        ["".join(item[0] for item in ct.split() if item.isalpha()) for ct in ct_array]
    )


def block(records_df: pd.DataFrame) -> pd.DataFrame:
    print("Block started at", datetime.now())
    start_time = time.time()

    pairs_df = pd.DataFrame(columns=["ID1", "ID2"])

    # For blocking:
    records_df["first_author"] = records_df[Fields.AUTHOR].str.split().str[0]
    records_df["short_title"] = records_df[Fields.TITLE].apply(
        lambda x: " ".join(x.split()[:10])
    )
    records_df["short_container_title"] = get_short_container_title(
        records_df[Fields.CONTAINER_TITLE].values
    )

    pool = multiprocessing.Pool()
    results = pool.starmap(
        calculate_pairs, [(records_df, field) for field in block_fields_list]
    )
    pool.close()
    pool.join()

    pairs_df = pd.concat(results, ignore_index=True).drop_duplicates()

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

    end_time = time.time()
    print(f"Block completed after: {end_time - start_time:.2f} seconds")
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
    non_empty_rows = records_df[
        records_df[block_fields].apply(lambda x: x != "").all(axis=1)
    ]
    # Speedup with hashes is two-fold (compared to the code in comments below)
    non_empty_rows = non_empty_rows.assign(
        block_hash=non_empty_rows[block_fields].apply(lambda x: hash(tuple(x)), axis=1)
    )
    grouped = (
        non_empty_rows.groupby("block_hash", group_keys=False)["ID"]
        .apply(lambda x: pd.DataFrame(list(combinations(x, 2)), columns=["ID1", "ID2"]))
        .reset_index(drop=True)
    )

    # non_empty_rows = records_df[block_fields].apply(lambda x: x != "").all(axis=1)
    # grouped = (
    #     records_df[non_empty_rows]
    #     .groupby(list(block_fields), group_keys=True)["ID"]
    #     .apply(lambda x: pd.DataFrame(list(combinations(x, 2)), columns=["ID1", "ID2"]))
    #     .reset_index(drop=True)
    # )
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
