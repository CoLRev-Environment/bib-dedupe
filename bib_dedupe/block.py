#! /usr/bin/env python
"""Block for dedupe."""
import multiprocessing
import time
from datetime import datetime
from itertools import combinations

import pandas as pd

from bib_dedupe import verbose_print
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR_FIRST
from bib_dedupe.constants.fields import CONTAINER_TITLE_SHORT
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import SEARCH_SET
from bib_dedupe.constants.fields import TITLE_SHORT
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR

block_fields_list = [
    {AUTHOR_FIRST, YEAR},
    {AUTHOR_FIRST, CONTAINER_TITLE_SHORT},
    {TITLE_SHORT, PAGES},
    {TITLE_SHORT, AUTHOR_FIRST},
    {TITLE_SHORT, VOLUME},
    {TITLE_SHORT, CONTAINER_TITLE_SHORT},
    {TITLE_SHORT, YEAR},
    {
        CONTAINER_TITLE_SHORT,
        VOLUME,
        NUMBER,
    },
    {
        CONTAINER_TITLE_SHORT,
        VOLUME,
        YEAR,
    },
    {
        CONTAINER_TITLE_SHORT,
        VOLUME,
        PAGES,
    },
    {
        CONTAINER_TITLE_SHORT,
        YEAR,
        PAGES,
    },
    {YEAR, VOLUME, NUMBER},
    {YEAR, VOLUME, PAGES},
    {YEAR, NUMBER, PAGES},
    {DOI},
    {ABSTRACT},
]


def create_pairs_for_block_fields(
    records_df: pd.DataFrame, block_fields: set
) -> pd.DataFrame:
    """
    Create pairs for block fields.

    This function creates pairs of records for the given block fields.
    It only considers records where all block fields are non-empty.

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

    pairs["require_title_overlap"] = False
    if not block_fields.intersection({TITLE_SHORT, DOI, PAGES}):
        pairs["require_title_overlap"] = True

    verbose_print.print(
        f"Blocked {str(f'{pairs.shape[0]:,}').rjust(8)} pairs with {block_fields}"
    )

    return pairs


def calculate_pairs(records_df: pd.DataFrame, block_fields: set) -> pd.DataFrame:
    """
    Calculate pairs for deduplication.

    This function calculates pairs of records for deduplication based on the given block fields.

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


def reduce_distinct_sets(pairs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce distinct sets.

    This function reduces the pairs dataframe. It removes pairs where
    both records are from the same search set.

    Parameters:
    pairs_df (pd.DataFrame): The dataframe containing the pairs.

    Returns:
    pd.DataFrame: The dataframe after reduction.
    """
    if f"{SEARCH_SET}_1" not in pairs_df.columns:
        return pairs_df

    pairs_df = pairs_df[
        ~(
            (pairs_df[f"{SEARCH_SET}_1"] == pairs_df[f"{SEARCH_SET}_2"])
            & (pairs_df[f"{SEARCH_SET}_1"] != "")
        )
    ]
    return pairs_df


def reduce_non_overlapping_titles(pairs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce non-overlapping titles.

    This function reduces the pairs dataframe by removing pairs where the titles do not overlap.

    Parameters:
    pairs_df (pd.DataFrame): The dataframe containing the pairs.

    Returns:
    pd.DataFrame: The dataframe after reduction.
    """
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
    return pairs_df


def block(records_df: pd.DataFrame, cpu: int = -1) -> pd.DataFrame:
    """
    Perform blocking operation on the given dataframe.

    This function performs blocking operation on the given dataframe to prepare it for deduplication.
    It calculates pairs of records for deduplication based on a predefined list of block fields.
    It then reduces the pairs dataframe by removing pairs where the titles
    do not overlap or both records are from the same search set.
    Parameters:
    records_df (pd.DataFrame): The dataframe containing the records.

    Returns:
    pd.DataFrame: The dataframe after blocking operation.
    """
    INSTRUCTION = "(please run prep(records_df) and pass the prepared df)"
    assert (
        "author_full" in records_df.columns
    ), f"Column 'author_full' not found in records_df {INSTRUCTION}"
    assert (
        "container_title" in records_df.columns
    ), f"Column 'container_title' not found in records_df {INSTRUCTION}"

    verbose_print.print(
        "Block started at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    start_time = time.time()

    pairs_df = pd.DataFrame(columns=["ID1", "ID2", "require_title_overlap"])
    pairs_df = pairs_df.astype({"ID1": str, "ID2": str, "require_title_overlap": bool})
    if cpu == 1:
        for field in block_fields_list:
            pairs_df = pd.concat(
                [pairs_df, calculate_pairs(records_df, field)],
                ignore_index=True,
            )

    else:
        pool = multiprocessing.Pool()
        results = pool.starmap(
            calculate_pairs, [(records_df, field) for field in block_fields_list]
        )
        pool.close()
        pool.join()

        pairs_df = pd.concat(results, ignore_index=True)

    # title overlap is only required when there is no blocked pair that requires it.
    pairs_df["require_title_overlap"] = pairs_df.groupby(["ID1", "ID2"])[
        "require_title_overlap"
    ].transform("all")
    pairs_df = pairs_df.drop_duplicates(subset=["ID1", "ID2"])

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

    verbose_print.print(f"Blocked {str(f'{pairs_df.shape[0]:,}').rjust(8)} pairs")

    pairs_df = reduce_non_overlapping_titles(pairs_df)
    pairs_df = reduce_distinct_sets(pairs_df)

    verbose_print.print(f"Blocked pairs reduced to {pairs_df.shape[0]:,} pairs")
    end_time = time.time()
    verbose_print.print(f"Block completed after: {end_time - start_time:.2f} seconds")
    return pairs_df
