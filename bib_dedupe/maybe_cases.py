#! /usr/bin/env python
"""Module to check maybe cases"""
from datetime import datetime
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

import bib_dedupe.cluster
from bib_dedupe import verbose_print
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import CLUSTER_ID
from bib_dedupe.constants.fields import CONTAINER_TITLE
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import DUPLICATE
from bib_dedupe.constants.fields import DUPLICATE_LABEL
from bib_dedupe.constants.fields import ID
from bib_dedupe.constants.fields import MAYBE
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR

MAYBE_CASES_FILEPATH = "maybe_cases.csv"
SIMILARITY_SCORE = "similarity_score"
FIELDS_TO_EXPORT = [
    SIMILARITY_SCORE,
    DUPLICATE_LABEL,
    CLUSTER_ID,
    AUTHOR,
    TITLE,
    CONTAINER_TITLE,
    YEAR,
    VOLUME,
    NUMBER,
    PAGES,
    DOI,
    ABSTRACT,
]


def __calculate_similarity(
    author1: str, title1: str, author2: str, title2: str
) -> float:
    concatenated1 = author1 + title1
    concatenated2 = author2 + title2
    return round(fuzz.ratio(concatenated1, concatenated2) / 100, 2)


def export_maybe(
    matched_df: pd.DataFrame,
    records_df: pd.DataFrame,
) -> None:
    """
    This method is used to check maybe cases for deduplication.

    Parameters:
    matched_df (pd.DataFrame): The dataframe containing the matched pairs.
    records_df (pd.DataFrame): The dataframe containing the records.
    """

    duplicate_id_clusters = bib_dedupe.cluster.get_connected_components(
        matched_df, label=DUPLICATE
    )

    # to avoid multiple maybe-pairs,
    # consider only one link between clusters (the first ID of duplicate_id_clusters)
    duplicate_id_dict = {
        i: duplicate_id_cluster[0]
        for duplicate_id_cluster in duplicate_id_clusters
        for i in duplicate_id_cluster
        if i != duplicate_id_cluster[0]
    }
    maybe_df = matched_df.loc[matched_df[DUPLICATE_LABEL] == MAYBE].copy()
    maybe_df.loc[:, f"{ID}_1"] = (
        maybe_df[f"{ID}_1"].map(duplicate_id_dict).fillna(maybe_df[f"{ID}_1"])
    )
    maybe_df.loc[:, f"{ID}_2"] = (
        maybe_df[f"{ID}_2"].map(duplicate_id_dict).fillna(maybe_df[f"{ID}_2"])
    )

    maybe_df = maybe_df.drop_duplicates(subset=[f"{ID}_1", f"{ID}_2"])

    maybe_id_pairs = maybe_df[[f"{ID}_1", f"{ID}_2"]].values.tolist()
    maybe_id_pairs = [pair for pair in maybe_id_pairs if pair[0] != pair[1]]

    maybe_cases_df = pd.DataFrame()
    maybe_cases_df.loc[:, ID] = [id for sublist in maybe_id_pairs for id in sublist]

    maybe_cases_df.loc[:, CLUSTER_ID] = [
        i for i, sublist in enumerate(maybe_id_pairs) for _ in sublist
    ]

    if maybe_cases_df.empty:
        return

    maybe_df = pd.merge(
        maybe_cases_df,
        records_df,
        left_on=ID,
        right_on=ID,
        how="inner",
    )

    similarity_scores = maybe_df.groupby(CLUSTER_ID).apply(
        lambda group: __calculate_similarity(
            group[AUTHOR].iloc[0],
            group[TITLE].iloc[0],
            group[AUTHOR].iloc[1],
            group[TITLE].iloc[1],
        )
    )
    maybe_df = maybe_df.merge(
        similarity_scores.rename(SIMILARITY_SCORE),
        left_on=CLUSTER_ID,
        right_index=True,
    )

    maybe_df = maybe_df.sort_values(
        [SIMILARITY_SCORE, CLUSTER_ID], ascending=[False, True]
    ).reset_index(drop=True)
    maybe_df.insert(0, DUPLICATE_LABEL, MAYBE)

    # Reorder the columns
    maybe_df = maybe_df[
        FIELDS_TO_EXPORT
        + [col for col in maybe_df.columns if col not in FIELDS_TO_EXPORT]
    ]

    file_path = Path(MAYBE_CASES_FILEPATH)
    if file_path.exists():
        file_path.rename(
            file_path.stem
            + "_"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + file_path.suffix
        )

    maybe_df.to_csv(MAYBE_CASES_FILEPATH, index=False)

    verbose_print.print(
        """Please follow the steps below to replace the 'duplicate_label' column
        with 'duplicate' if it is a duplicate:
        1. Open the 'maybe_cases.csv' file.
        2. Replace the 'duplicate_label' column values with 'duplicate' where necessary.
        3. Save the changes to 'maybe_cases.csv'."""
    )


def import_maybe(
    matched_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    This method is used to import decisions for maybe cases.

    Parameters:
    matched_df (pd.DataFrame): The dataframe containing the matches.

    Returns:
    pd.DataFrame: The dataframe containing the updated matches.
    """

    if not Path(MAYBE_CASES_FILEPATH).is_file():
        verbose_print.print(f"File {MAYBE_CASES_FILEPATH} does not exist")
        return matched_df

    maybe_cases_df = pd.read_csv(MAYBE_CASES_FILEPATH)

    duplicate_cases = (
        maybe_cases_df[maybe_cases_df[DUPLICATE_LABEL] == DUPLICATE]
        .groupby(CLUSTER_ID)
        .apply(lambda group: set(group[ID].values.flatten().astype(str)))
        .values.tolist()
    )

    verbose_print.print(f"Number of cases labeled as duplicate: {len(duplicate_cases)}")

    # Replace the 'duplicate_label' column in matched_df dataframe with 'duplicate' for these cases
    if len(duplicate_cases):
        matched_df.loc[
            matched_df.apply(
                lambda row: {row[f"{ID}_1"], row[f"{ID}_2"]} in duplicate_cases, axis=1
            ),
            DUPLICATE_LABEL,
        ] = DUPLICATE

    matched_df = matched_df[matched_df[DUPLICATE_LABEL] != MAYBE]

    return matched_df
