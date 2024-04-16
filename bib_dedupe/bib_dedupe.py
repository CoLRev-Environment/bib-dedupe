#! /usr/bin/env python
"""Module for deduplicating bibliographic records"""
from __future__ import annotations

import os
import typing

import pandas as pd
import requests

import bib_dedupe.block
import bib_dedupe.match
import bib_dedupe.maybe_cases
import bib_dedupe.merge
import bib_dedupe.prep
import bib_dedupe.sim
from bib_dedupe import verbose_print


def prep(
    records_df: pd.DataFrame,
    *,
    verbosity_level: typing.Optional[int] = None,
    cpu: int = -1,
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
    return bib_dedupe.prep.prep(records_df, cpu=cpu)


def block(
    records_df: pd.DataFrame,
    *,
    verbosity_level: typing.Optional[int] = None,
    cpu: int = -1,
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

    pairs_df = bib_dedupe.block.block(records_df, cpu=cpu)

    return pairs_df


def match(
    pairs_df: pd.DataFrame,
    *,
    verbosity_level: typing.Optional[int] = None,
    cpu: int = -1,
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

    return bib_dedupe.match.match(pairs_df, cpu=cpu)


def export_maybe(
    records_df: pd.DataFrame,
    *,
    matched_df: pd.DataFrame,
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
    matched_df: typing.Optional[pd.DataFrame] = None,
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

    if matched_df:
        duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)

    if not duplicate_id_sets:
        prep_df = prep(records_df)
        blocked_df = block(records_df=prep_df)
        matched_df = match(blocked_df)
        duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)

    return bib_dedupe.merge.merge(records_df, duplicate_id_sets=duplicate_id_sets)


def _download_file_from_github(url: str, local_path: str) -> None:
    raw_url = url.replace("github.com", "raw.githubusercontent.com").replace(
        "/blob", ""
    )
    response = requests.get(raw_url, stream=True)
    with open(local_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)


def load_example_data(dataset: str) -> pd.DataFrame:
    """
    Retrieves the dataset from GitHub and loads the records as a DataFrame.

    Args:
        dataset (str): The name of the dataset (e.g., stroke, cardiac, depression).

    Returns:
        pd.DataFrame: The loaded records dataframe.
    """

    local_path = f"{dataset}.csv"
    url = f"https://github.com/CoLRev-Environment/bib-dedupe/blob/main/data/{dataset}/records_pre_merged.csv"

    if not os.path.exists(local_path):
        _download_file_from_github(url, local_path)

    try:
        df = pd.read_csv(local_path)
    except FileNotFoundError:
        raise ValueError(f"Dataset '{dataset}' not found.")
    return df
