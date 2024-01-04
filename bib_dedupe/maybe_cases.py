#! /usr/bin/env python
"""Module to check maybe cases"""
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

import bib_dedupe.cluster
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import CONTAINER_TITLE
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR


def export_maybe(matched_df: pd.DataFrame, records_df: pd.DataFrame) -> None:
    """
    This method is used to check maybe cases for deduplication.

    Parameters:
    matched_df (pd.DataFrame): The dataframe containing the matched pairs.
    records_df (pd.DataFrame): The dataframe containing the records.
    """

    duplicate_id_clusters = bib_dedupe.cluster.get_connected_components(
        matched_df, label="duplicate"
    )

    # to avoid multiple maybe-pairs,
    # consider only one link between clusters (the first ID of duplicate_id_clusters)
    duplicate_id_dict = {
        i: duplicate_id_cluster[0]
        for duplicate_id_cluster in duplicate_id_clusters
        for i in duplicate_id_cluster
        if i != duplicate_id_cluster[0]
    }
    maybe_df = matched_df[matched_df["duplicate_label"] == "maybe"]
    maybe_df["ID_1"] = maybe_df["ID_1"].map(duplicate_id_dict).fillna(maybe_df["ID_1"])
    maybe_df["ID_2"] = maybe_df["ID_2"].map(duplicate_id_dict).fillna(maybe_df["ID_2"])
    maybe_df = maybe_df.drop_duplicates(subset=["ID_1", "ID_2"])

    maybe_id_pairs = maybe_df[["ID_1", "ID_2"]].values.tolist()
    maybe_id_pairs = [pair for pair in maybe_id_pairs if pair[0] != pair[1]]

    maybe_cases_df = pd.DataFrame()
    maybe_cases_df.loc[:, "ID"] = [id for sublist in maybe_id_pairs for id in sublist]

    maybe_cases_df.loc[:, "cluster_ID"] = [
        i for i, sublist in enumerate(maybe_id_pairs) for _ in sublist
    ]

    if maybe_cases_df.empty:
        return

    maybe_df = pd.merge(
        maybe_cases_df,
        records_df,
        left_on="ID",
        right_on="ID",
        how="inner",
    )

    def calculate_similarity(
        author1: str, title1: str, author2: str, title2: str
    ) -> float:
        concatenated1 = author1 + title1
        concatenated2 = author2 + title2
        return round(fuzz.ratio(concatenated1, concatenated2) / 100, 2)

    similarity_scores = maybe_df.groupby("cluster_ID").apply(
        lambda group: calculate_similarity(
            group["author"].iloc[0],
            group["title"].iloc[0],
            group["author"].iloc[1],
            group["title"].iloc[1],
        )
    )
    maybe_df = maybe_df.merge(
        similarity_scores.rename("similarity_score"),
        left_on="cluster_ID",
        right_index=True,
    )

    maybe_df = maybe_df.sort_values(
        ["similarity_score", "cluster_ID"], ascending=[False, True]
    ).reset_index(drop=True)
    maybe_df.insert(0, "duplicate_label", "maybe")
    maybe_df = maybe_df[
        [
            "similarity_score",
            "duplicate_label",
            "cluster_ID",
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
        + [
            col
            for col in maybe_df.columns
            if col
            not in [
                "similarity_score",
                "duplicate_label",
                "cluster_ID",
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
        ]
    ]

    from pathlib import Path
    from datetime import datetime

    file_path = Path("maybe_cases.csv")
    if file_path.exists():
        file_path.rename(
            file_path.stem
            + "_"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + file_path.suffix
        )

    maybe_df.to_csv("maybe_cases.csv", index=False)

    print(
        "Please follow the steps below to replace the "
        "'duplicate_label' column with 'duplicate' if it is a duplicate:"
    )
    print("1. Open the 'maybe_cases.csv' file.")
    print(
        "2. Replace the 'duplicate_label' column values with 'duplicate' where necessary."
    )
    print("3. Save the changes to 'maybe_cases.csv'.")


def import_maybe(matched_df: pd.DataFrame) -> pd.DataFrame:
    """
    This method is used to import decisions for maybe cases.

    Parameters:
    matched_df (pd.DataFrame): The dataframe containing the matches.

    Returns:
    pd.DataFrame: The dataframe containing the updated matches.
    """

    if not Path("maybe_cases.csv").is_file():
        return matched_df

    # Load the 'maybe_cases.csv' file
    maybe_cases_df = pd.read_csv("maybe_cases.csv")

    duplicate_cases = (
        maybe_cases_df[maybe_cases_df["duplicate_label"] == "duplicate"]
        .groupby("cluster_ID")
        .apply(lambda group: set(group["ID"].values.flatten().astype(str)))
        .values.tolist()
    )

    # Print how many cases were labeled as duplicate
    print(f"Number of cases labeled as duplicate: {len(duplicate_cases)}")

    if len(duplicate_cases):
        # Replace the 'duplicate_label' column in matched_df dataframe with 'duplicate' for these cases
        matched_df.loc[
            matched_df.apply(
                lambda row: {row["ID_1"], row["ID_2"]} in duplicate_cases, axis=1
            ),
            "duplicate_label",
        ] = "duplicate"

    # if not keep_maybes:
    matched_df = matched_df[matched_df["duplicate_label"] != "maybe"]

    return matched_df
