#! /usr/bin/env python
"""Default deduplication module for CoLRev"""
from __future__ import annotations

import multiprocessing
import pprint
from collections import defaultdict
from itertools import combinations
from typing import List

import pandas as pd
from colrev.constants import Colors
from colrev.constants import Fields
from rapidfuzz import fuzz


# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods


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
    grouped = (
        records_df.groupby(list(block_fields), group_keys=True)["ID"]
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


class BibDeduper:
    """BibDeduper class"""

    def __init__(self, *, debug: bool = False):
        self.debug = debug
        self.p_printer = pprint.PrettyPrinter(indent=4, width=140, compact=False)

    @classmethod
    def __dfs(cls, node: str, graph: dict, visited: dict, component: list) -> None:
        visited[node] = True
        component.append(node)
        for neighbor in graph[node]:
            if not visited[neighbor]:
                cls.__dfs(neighbor, graph, visited, component)

    @classmethod
    def connected_components(cls, origin_sets: list) -> list:
        """
        Find the connected components in a graph.

        Args:
            origin_sets (list): A list of origin sets.

        Returns:
            list: A list of connected components.
        """
        graph = defaultdict(list)

        # Create an adjacency list
        for origin_set in origin_sets:
            for combination in combinations(origin_set, 2):
                graph[combination[0]].append(combination[1])
                graph[combination[1]].append(combination[0])

        visited = {node: False for node in graph}
        components = []

        for node in graph:
            if not visited[node]:
                component: List[str] = []
                cls.__dfs(node, graph, visited, component)
                components.append(sorted(component))

        return components

    def block_pairs_for_deduplication(self, records_df: pd.DataFrame) -> pd.DataFrame:
        """
        This method is used to block pairs for deduplication.

        Parameters:
        records_df (pd.DataFrame): The dataframe containing the records to be deduplicated.

        Returns:
        pd.DataFrame: The dataframe containing the blocked pairs for deduplication.
        """

        pairs_df = pd.DataFrame(columns=["ID1", "ID2"])

        # container_title instead of journal
        block_fields_list = [
            # TODO : remove redundant fields
            # Redundant with [Fields.AUTHOR, Fields.YEAR]:
            # [Fields.AUTHOR, Fields.YEAR, Fields.PAGES],
            [Fields.DOI],
            [Fields.URL],
            [Fields.ISBN],
            [Fields.AUTHOR, Fields.YEAR],
            [Fields.TITLE, Fields.PAGES],
            [Fields.TITLE, Fields.AUTHOR],
            [Fields.TITLE, Fields.ABSTRACT],
            [Fields.TITLE, Fields.VOLUME],
            [Fields.TITLE, Fields.CONTAINER_TITLE],
            [Fields.TITLE, Fields.YEAR],
            [Fields.YEAR, Fields.VOLUME, Fields.NUMBER],
            [Fields.YEAR, Fields.VOLUME, Fields.PAGES],
            [Fields.YEAR, Fields.NUMBER, Fields.PAGES],
            [
                Fields.CONTAINER_TITLE,
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

        self.__calc_similarities(pairs_df)

        return pairs_df

    def __calc_similarities(self, pairs_df: pd.DataFrame) -> pd.DataFrame:
        # Add similarities if both fields exist
        similarity_fields = [
            Fields.AUTHOR,
            Fields.TITLE,
            Fields.YEAR,
            Fields.VOLUME,
            Fields.PAGES,
            Fields.ABSTRACT,
            Fields.ISBN,
            Fields.DOI,
        ]
        for similarity_field in similarity_fields:
            # TODO : how to deal with NA?
            pairs_df[similarity_field] = pairs_df.apply(
                lambda row, sim_field=similarity_field: fuzz.token_sort_ratio(
                    str(row[f"{sim_field}_1"]), str(row[f"{sim_field}_2"])
                )
                / 100
                if row[f"{sim_field}_1"] is not None
                and row[f"{sim_field}_2"] is not None
                else 0,
                axis=1,
            )

        similarity_fields = [
            Fields.CONTAINER_TITLE,
            Fields.NUMBER,  # some journals have numbers like 3/4 (which can be abbreviated)
        ]
        for similarity_field in similarity_fields:
            # TODO : how to deal with NA?
            pairs_df[similarity_field] = pairs_df.apply(
                lambda row, sim_field=similarity_field: fuzz.partial_ratio(
                    str(row[f"{sim_field}_1"]), str(row[f"{sim_field}_2"])
                )
                / 100
                if row[f"{sim_field}_1"] is not None
                and row[f"{sim_field}_2"] is not None
                else 0,
                axis=1,
            )

        pairs_df["title_partial_ratio"] = pairs_df.apply(
            lambda row: fuzz.partial_ratio(str(row["title_1"]), str(row["title_2"]))
            / 100
            if row["title_1"] is not None and row["title_2"] is not None
            else 0,
            axis=1,
        )

    # flake8: noqa: E501
    # pylint: disable=line-too-long
    def identify_true_matches(self, pairs: pd.DataFrame) -> pd.DataFrame:
        """
        This method identifies the true matches from the given pairs.
        The pairs are compared based on various fields and their similarity scores.
        The fields used for comparison are: Pages, Volume, Title, Abstract, Author, ISBN, Container Title, Number.
        The similarity scores for these fields are calculated using the fuzz.token_sort_ratio method.
        The pairs that satisfy certain conditions based on these similarity scores are considered as true matches.

        Parameters:
        pairs (DataFrame): The DataFrame containing the pairs to be compared.

        Returns:
        DataFrame: The DataFrame containing the true matches.
        """

        # TODO : think: how do we measure similarity for missing values?

        # Queries are better for debugging (understanding which conditions do/do not apply)
        # https://jakevdp.github.io/PythonDataScienceHandbook/03.12-performance-eval-and-query.html
        # pylint: disable=line-too-long
        queries = [
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9 & {Fields.ISBN} > 0.99)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.DOI} > 0.99)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.8 & {Fields.CONTAINER_TITLE} > 0.65 & {Fields.VOLUME} > 0.85 & {Fields.ABSTRACT} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.65 & {Fields.VOLUME} > 0.85 & {Fields.ABSTRACT} > 0.8)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.75 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.8)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.75 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.8)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.75 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.8)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.7 & {Fields.ABSTRACT} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.NUMBER} > 0.9 & {Fields.PAGES} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.VOLUME} > 0.9 & {Fields.PAGES} > 0.9)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.9 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8)",
            f"({Fields.AUTHOR} > 0.8 & {Fields.TITLE} > 0.99 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.DOI} > 0.99)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.9 & {Fields.NUMBER} > 0.9 & {Fields.ISBN} > 0.99)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.ABSTRACT} > 0.9 & {Fields.ISBN} > 0.99)",
            f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.NUMBER} > 0.9 & {Fields.PAGES} > 0.9 & {Fields.ISBN} > 0.99)",
            f"({Fields.AUTHOR} > 0.95 & title_partial_ratio > 0.8 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.DOI} > 0.99)",
            f'({Fields.ENTRYTYPE}_1 == "inproceedings" & {Fields.ENTRYTYPE}_2 == "inproceedings" & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.TITLE} > 0.9 & {Fields.AUTHOR} > 0.8 & {Fields.YEAR} > 0.9)',
        ]

        if self.debug:
            if pairs.shape[0] != 0:
                self.p_printer.pprint(pairs.iloc[0].to_dict())
                print("True merge conditions:")
                for query in queries:
                    if pairs.query(query).shape[0] > 0:
                        print(f"{Colors.GREEN}{query}{Colors.END}")
                    else:
                        print(f"{Colors.RED}{query}{Colors.END}")

        true_pairs = pairs.query("|".join(queries))

        print("TODO : continue here!")

        # TODO : the prevented-same-source merges should go into the manual list
        # TODO : integrate __prevent_invalid_merges here?!

        # exclude conditions
        queries = [
            f"({Fields.DOI} < 0.99 & {Fields.DOI} > 0.01)",
            f'(title_1.str.contains("editor")  & {Fields.NUMBER} < 1)',
        ]

        if self.debug:
            if pairs.shape[0] == 0:
                print("Exclude conditions:")
                for query in queries:
                    if pairs.query(query).shape[0] == 0:
                        print(f"{Colors.RED}{query}{Colors.END}")
                    else:
                        print(query)

        true_pairs = true_pairs.query("~(" + " | ".join(queries) + ")")

        true_pairs = true_pairs.drop_duplicates()

        maybe_pairs = pd.DataFrame()

        # TODO : for maybe_pairs, create a similarity score over all fields (catching cases where the entrytypes/fiels are highly erroneous)

        # # Make year numeric, then find matches where year differs
        # true_pairs['year1'] = pd.to_numeric(true_pairs['year1'], errors='coerce')
        # true_pairs['year2'] = pd.to_numeric(true_pairs['year2'], errors='coerce')
        # year_mismatch = true_pairs[true_pairs['year1'] != true_pairs['year2']]
        # year_mismatch_minor1 = year_mismatch[year_mismatch['year1'] == year_mismatch['year2'] + 1]
        # year_mismatch_minor2 = year_mismatch[year_mismatch['year1'] == year_mismatch['year2'] - 1]

        # year_mismatch_minor = pd.concat([year_mismatch_minor1, year_mismatch_minor2])
        # year_mismatch_minor = year_mismatch_minor.drop_duplicates()

        # # Identify where year differs >1 and remove from filtered dataset - need to manually deduplicate
        # year_mismatch_major = year_mismatch[~year_mismatch.index.isin(year_mismatch_minor.index)]
        # true_pairs = true_pairs[~true_pairs.index.isin(year_mismatch_major.index)]

        # true_pairs = true_pairs.drop_duplicates()

        # # Get potential duplicates for manual deduplication
        # maybe_pairs = pairs[
        #     (pairs[Fields.TITLE] > 0.85) & (pairs['author'] > 0.75) |
        #     (pairs[Fields.TITLE] > 0.8) & (pairs[Fields.ABSTRACT] > 0.8) |
        #     (pairs[Fields.TITLE] > 0.8) & (pairs[Fields.ISBN] > 0.99) |
        #     (pairs[Fields.TITLE] > 0.8) & (pairs[Fields.CONTAINER_TITLE] > 0.8) |
        #     (pd.isna(pairs[Fields.DOI]) | (pairs[Fields.DOI] > 0.99) | (pairs[Fields.DOI] == 0)) &
        #     ~((pd.to_numeric(pairs['year1'], errors='coerce') - pd.to_numeric(pairs['year2'], errors='coerce') > 1) |
        #     (pd.to_numeric(pairs['year2'], errors='coerce') - pd.to_numeric(pairs['year1'], errors='coerce') > 1))
        # ]

        # # maybe_pairs['record_ID1'] = maybe_pairs['record_ID1'].astype(str)
        # # maybe_pairs['record_ID2'] = maybe_pairs['record_ID2'].astype(str)
        # # true_pairs['record_ID1'] = true_pairs['record_ID1'].astype(str)
        # # true_pairs['record_ID2'] = true_pairs['record_ID2'].astype(str)

        # # # Get pairs required for manual dedup which are not in true pairs
        # # maybe_pairs = maybe_pairs[~maybe_pairs.set_index(['record_ID1', 'record_ID2']).index.isin(true_pairs.set_index(['record_ID1', 'record_ID2']).index)]

        # # # Add in problem doi matching pairs and different year data in ManualDedup
        # # important_mismatch = pd.concat([true_pairs_mismatch_doi, year_mismatch_major])
        # important_mismatch = true_pairs_mismatch_doi
        # maybe_pairs = pd.concat([maybe_pairs, important_mismatch])
        # maybe_pairs = maybe_pairs.drop_duplicates()

        origin_sets = [
            row["colrev_origin_1"].split(";") + row["colrev_origin_2"].split(";")
            for _, row in true_pairs.iterrows()
        ]
        duplicate_origin_sets = self.connected_components(origin_sets=origin_sets)

        return {
            "duplicate_origin_sets": duplicate_origin_sets,
            "true_pairs": true_pairs,
            "maybe_pairs": maybe_pairs,
        }
