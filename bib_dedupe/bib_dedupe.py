#! /usr/bin/env python
"""Default deduplication module for CoLRev"""
from __future__ import annotations

import typing

import pandas as pd

import bib_dedupe.block
import bib_dedupe.match
import bib_dedupe.merge
import bib_dedupe.prep
import bib_dedupe.sim


class BibDeduper:
    """BibDeduper class"""

    def __init__(self, *, debug: bool = False):
        self.debug = debug

    def get_records_for_dedupe(self, *, records_df: pd.DataFrame) -> pd.DataFrame:
        """Get (pre-processed) records for dedupe"""

        return bib_dedupe.prep.get_records_for_dedupe(records_df)

    def block(self, records_df: pd.DataFrame) -> pd.DataFrame:
        """
        This method is used to block pairs for deduplication.

        Parameters:
        records_df (pd.DataFrame): The dataframe containing the records to be deduplicated.

        Returns:
        pd.DataFrame: The dataframe containing the blocked pairs for deduplication.
        """

        pairs_df = bib_dedupe.block.block(records_df)

        return pairs_df

    # TODO : rename:
    # flake8: noqa: E501
    # pylint: disable=line-too-long
    def match(
        self, pairs_df: pd.DataFrame, *, merge_updated_papers: bool = True
    ) -> dict:
        """
        Identifies the true matches from the given pairs.

        The pairs are compared based on various fields and their similarity scores.
        The fields used for comparison are: Pages, Volume, Title, Abstract, Author, ISBN, Container Title, Number.
        The similarity scores for these fields are calculated using the fuzz.token_sort_ratio method.
        The pairs that satisfy certain conditions based on these similarity scores are considered as true matches.

        Args:
            pairs (pd.DataFrame): The DataFrame containing the pairs to be compared.
            merge_updated_papers (bool, optional): Flag to indicate whether to merge updated papers. Defaults to True.

        Returns:
        DataFrame: The DataFrame containing the true matches.
        """

        return bib_dedupe.match.match(
            pairs_df, merge_updated_papers=merge_updated_papers, debug=self.debug
        )

    def merge(
        self, records_df: pd.DataFrame, *, matches: typing.Optional[dict] = None
    ) -> pd.DataFrame:
        """
        This function returns a DataFrame after merging the records.

        Args:
            records_df (pd.DataFrame): The DataFrame containing the records to be merged.
            matches (dict): A dictionary containing the matches.

        Returns:
            pd.DataFrame: The merged DataFrame.
        """

        if not matches:
            actual_blocked_df = self.block(records_df=records_df)
            matches = self.match(actual_blocked_df)

        return bib_dedupe.merge.merge(records_df, matches=matches)


def merge(
    records_df: pd.DataFrame, *, matches: typing.Optional[dict] = None
) -> pd.DataFrame:
    deduper = BibDeduper()
    # Block records
    blocked_df = deduper.block(records_df=records_df)
    # Identify matches
    matches = deduper.match(blocked_df)

    # Merge
    merged_df = deduper.merge(records_df, matches=matches)
    return merged_df
