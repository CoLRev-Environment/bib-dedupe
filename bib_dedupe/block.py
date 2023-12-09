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
    {Fields.DOI},
    {"first_author", Fields.YEAR},
    {"short_title", Fields.PAGES},
    {"short_title", "first_author"},
    # TODO : remove short_title (just abstract should be sufficient)
    {"short_title", Fields.ABSTRACT},
    {"short_title", Fields.VOLUME},
    {"short_title", "short_container_title"},
    {"first_author", "short_container_title"},
    {"short_title", Fields.YEAR},
    {Fields.YEAR, Fields.VOLUME, Fields.NUMBER},
    {Fields.YEAR, Fields.VOLUME, Fields.PAGES},
    {Fields.YEAR, Fields.NUMBER, Fields.PAGES},
    {
        "short_container_title",
        Fields.VOLUME,
        Fields.NUMBER,
    },
    {
        "short_container_title",
        Fields.VOLUME,
        Fields.YEAR,
    },
    {
        "short_container_title",
        Fields.VOLUME,
        Fields.PAGES,
    },
    {
        "short_container_title",
        Fields.YEAR,
        Fields.PAGES,
    },
    # TODO : conferences, books, ...
]


def get_short_container_title(ct_array: np.array) -> np.array:
    return np.array(
        ["".join(item[0] for item in ct.split() if item.isalpha()) for ct in ct_array]
    )


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

    non_empty_df = records_df.loc[
        records_df[list(block_fields)].ne("").all(axis=1)
    ].copy()
    non_empty_df = non_empty_df.assign(
        block_hash=non_empty_df[list(block_fields)].apply(
            lambda x: hash(tuple(x)), axis=1
        )
    )
    if non_empty_df.empty:
        return pd.DataFrame()

    pairs = (
        non_empty_df.groupby("block_hash", group_keys=True)["ID"]
        .apply(lambda x: pd.DataFrame(list(combinations(x, 2)), columns=["ID1", "ID2"]))
        .reset_index(drop=True)
    )
    pairs["block_rule"] = "-".join(block_fields)

    if not set(block_fields).intersection({"short_title", Fields.DOI}):
        pairs["require_title_overlap"] = True
    else:
        pairs["require_title_overlap"] = False

    print(f"Blocked {str(pairs.shape[0]).rjust(8)} pairs with {block_fields}")

    return pairs


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
        return pd.DataFrame()
    pairs = create_pairs_for_block_fields(records_df, block_fields)
    return pairs


def block(records_df: pd.DataFrame) -> pd.DataFrame:
    print("Block started at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    start_time = time.time()

    pairs_df = pd.DataFrame(columns=["ID1", "ID2"])
    # For blocking:
    records_df = records_df.assign(
        first_author=records_df[Fields.AUTHOR].str.split().str[0],
        short_title=records_df[Fields.TITLE].apply(lambda x: " ".join(x.split()[:10])),
        short_container_title=get_short_container_title(
            records_df[Fields.CONTAINER_TITLE].values
        ),
    )

    pool = multiprocessing.Pool()
    results = pool.starmap(
        calculate_pairs, [(records_df, field) for field in block_fields_list]
    )
    pool.close()
    pool.join()

    pairs_df = pd.concat(results, ignore_index=True).drop_duplicates(
        subset=["ID1", "ID2"]
    )

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

    print(pairs_df.shape[0])

    # Don't require title_overlap (words) for identical titles
    # and titles not containing a space
    pairs_df.loc[
        (pairs_df["title_1"] == pairs_df["title_2"])
        | (~pairs_df["title_1"].str.contains(" "))
        | (~pairs_df["title_2"].str.contains(" ")),
        "require_title_overlap",
    ] = False

    pairs_df = pairs_df[
        ~(
            (pairs_df["require_title_overlap"])
            & (
                pairs_df.apply(
                    lambda x: len(
                        set(str(x["title_1"]).split()) & set(str(x["title_2"]).split())
                    )
                    / (
                        # Take min because some titles have their translation appended
                        min(
                            len(str(x["title_1"]).split())
                            + 1,  # avoid division-by-zero
                            len(str(x["title_2"]).split())
                            + 1,  # avoid division-by-zero
                        )
                    )
                    < 0.5
                    if (len(str(x["title_1"])) + len(str(x["title_2"]))) != 0
                    else True,
                    axis=1,
                )
            )
        )
    ]

    print(f"Blocked {pairs_df.shape[0]} pairs")

    end_time = time.time()
    print(f"Block completed after: {end_time - start_time:.2f} seconds")
    return pairs_df
