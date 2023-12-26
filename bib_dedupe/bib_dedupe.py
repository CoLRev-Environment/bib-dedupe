#! /usr/bin/env python
"""Bib-dedupe module"""
from __future__ import annotations

import typing

import pandas as pd

import bib_dedupe.block
import bib_dedupe.match
import bib_dedupe.maybe_cases
import bib_dedupe.merge
import bib_dedupe.prep
import bib_dedupe.sim


def prep(records_df: pd.DataFrame) -> pd.DataFrame:
    """Get (pre-processed) records for dedupe"""

    return bib_dedupe.prep.prep(records_df)


def block(records_df: pd.DataFrame) -> pd.DataFrame:
    """
    This function is used to block pairs for deduplication.

    Parameters:
    records_df (pd.DataFrame): The dataframe containing the records to be deduplicated.

    Returns:
    pd.DataFrame: The dataframe containing the blocked pairs for deduplication.
    """

    pairs_df = bib_dedupe.block.block(records_df)

    return pairs_df


def match(pairs_df: pd.DataFrame, *, debug: bool = False) -> pd.DataFrame:
    """
    Identifies the true matches from the given pairs.

    The pairs are compared based on various fields and their similarity scores.
    The fields used for comparison are: Pages, Volume, Title, Abstract, Author, ISBN, Container Title, Number.
    The similarity scores for these fields are calculated using the fuzz.token_sort_ratio function.
    The pairs that satisfy certain conditions based on these similarity scores are considered as true matches.

    Args:
        pairs (pd.DataFrame): The DataFrame containing the pairs to be compared.

    Returns:
    DataFrame: The DataFrame containing the true matches.
    """

    return bib_dedupe.match.match(pairs_df, debug=debug)


def export_maybe(matched_df: pd.DataFrame, records_df: pd.DataFrame) -> None:
    """
    This function is used to export maybe cases for deduplication.

    Parameters:
    matched_df (pd.DataFrame): The dataframe containing the matched pairs.
    records_df (pd.DataFrame): The dataframe containing the records.
    """

    bib_dedupe.maybe_cases.export_maybe(matched_df, records_df)


def import_maybe_decisions(matched_df: pd.DataFrame) -> pd.DataFrame:
    """
    This function is used to import decisions for maybe cases.

    Parameters:
    matched_df (pd.DataFrame): The dataframe containing the matches.

    Returns:
    pd.DataFrame: The dataframe containing the updated matches.
    """

    return bib_dedupe.maybe_cases.import_maybe_decisions(matched_df)


def merge(
    records_df: pd.DataFrame,
    *,
    duplicate_id_sets: typing.Optional[list] = None,
) -> pd.DataFrame:
    """
    This function returns a DataFrame after merging the records.

    Args:
        records_df (pd.DataFrame): The DataFrame containing the records to be merged.
        matches (dict): A dictionary containing the matches.

    Returns:
        pd.DataFrame: The merged DataFrame.
    """

    if not duplicate_id_sets:
        blocked_df = block(records_df=records_df)
        matched_df = match(blocked_df)
        duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)

    return bib_dedupe.merge.merge(records_df, duplicate_id_sets=duplicate_id_sets)
