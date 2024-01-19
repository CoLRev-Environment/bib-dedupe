#! /usr/bin/env python
"""Module for deduplicating bibliographic records"""
from __future__ import annotations

import typing

import pandas as pd

import bib_dedupe.block
import bib_dedupe.match
import bib_dedupe.maybe_cases
import bib_dedupe.merge
import bib_dedupe.prep
import bib_dedupe.sim
from bib_dedupe import verbose_print


def prep(
    records_df: pd.DataFrame, *, verbosity_level: typing.Optional[int] = None
) -> pd.DataFrame:
    """Preprocesses records for deduplication.

    Args:
        records_df (pd.DataFrame): The dataframe containing the records to be preprocessed.
        verbosity_level (int, optional): Level of verbosity for logging. Defaults to None.

    Returns:
        pd.DataFrame: The preprocessed records dataframe.
    """
    if verbosity_level is not None:
        verbose_print.verbosity_level = verbosity_level
    return bib_dedupe.prep.prep(records_df)


def block(
    records_df: pd.DataFrame, *, verbosity_level: typing.Optional[int] = None
) -> pd.DataFrame:
    """
    Blocks pairs of records for deduplication.

    Args:
        records_df (pd.DataFrame): The dataframe containing the records to be deduplicated.
        verbosity_level (int, optional): Level of verbosity for logging. Defaults to None.

    Returns:
        pd.DataFrame: The dataframe containing the blocked pairs for deduplication.
    """
    if verbosity_level is not None:
        verbose_print.verbosity_level = verbosity_level

    pairs_df = bib_dedupe.block.block(records_df)

    return pairs_df


def match(
    pairs_df: pd.DataFrame, *, verbosity_level: typing.Optional[int] = None
) -> pd.DataFrame:
    """
    Identifies true/maybe matches from the given pairs based on similarity scores.

    Args:
        pairs_df (pd.DataFrame): The DataFrame containing the pairs to be compared.
        verbosity_level (int, optional): Level of verbosity for logging. Defaults to None.
        debug (bool, optional): If True, enables debug mode. Defaults to False.

    Returns:
        pd.DataFrame: The DataFrame containing the true/maybe matches.
    """
    if verbosity_level is not None:
        verbose_print.verbosity_level = verbosity_level

    return bib_dedupe.match.match(pairs_df)


def export_maybe(
    matched_df: pd.DataFrame,
    records_df: pd.DataFrame,
    *,
    verbosity_level: typing.Optional[int] = None,
) -> None:
    """
    Exports 'maybe' cases for manual review during deduplication.

    Args:
        matched_df (pd.DataFrame): The dataframe containing the matched pairs.
        records_df (pd.DataFrame): The dataframe containing the records.
        verbosity_level (int, optional): Level of verbosity for logging. Defaults to None.
    """
    if verbosity_level is not None:
        verbose_print.verbosity_level = verbosity_level

    bib_dedupe.maybe_cases.export_maybe(matched_df, records_df)


def import_maybe(
    matched_df: pd.DataFrame, *, verbosity_level: typing.Optional[int] = None
) -> pd.DataFrame:
    """
    Imports decisions for 'maybe' cases after manual review.

    Args:
        matched_df (pd.DataFrame): The dataframe containing the matches.
        verbosity_level (int, optional): Level of verbosity for logging. Defaults to None.

    Returns:
        pd.DataFrame: The dataframe containing the updated matches.
    """
    if verbosity_level is not None:
        verbose_print.verbosity_level = verbosity_level

    return bib_dedupe.maybe_cases.import_maybe(matched_df)


def cluster(
    matched_df: pd.DataFrame, *, verbosity_level: typing.Optional[int] = None
) -> list:
    """
    Clusters the matched data for deduplication.

    Args:
        matched_df (pd.DataFrame): The dataframe containing the matches.
        verbosity_level (int, optional): Level of verbosity for logging. Defaults to None.

    Returns:
        list: The list of clusters.
    """
    if verbosity_level is not None:
        verbose_print.verbosity_level = verbosity_level

    return bib_dedupe.cluster.get_connected_components(matched_df)


def merge(
    records_df: pd.DataFrame,
    *,
    duplicate_id_sets: typing.Optional[list] = None,
    verbosity_level: typing.Optional[int] = None,
) -> pd.DataFrame:
    """
    Merges duplicate records in the given dataframe.

    Args:
        records_df (pd.DataFrame): The DataFrame containing the records to be merged.
        duplicate_id_sets (list, optional): List of sets containing duplicate
        record IDs. If None, the function will perform deduplication process
        to identify duplicates. Defaults to None.
        verbosity_level (int, optional): Level of verbosity for logging. Defaults to None.

    Returns:
        pd.DataFrame: The merged DataFrame.
    """
    if verbosity_level is not None:
        verbose_print.verbosity_level = verbosity_level

    if not duplicate_id_sets:
        prep_df = prep(records_df)
        blocked_df = block(records_df=prep_df)
        matched_df = match(blocked_df)
        duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)

    return bib_dedupe.merge.merge(records_df, duplicate_id_sets=duplicate_id_sets)
