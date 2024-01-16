#! /usr/bin/env python
"""Match for dedupe"""
import time
from datetime import datetime

import pandas as pd

import bib_dedupe.conditions
import bib_dedupe.sim
import bib_dedupe.util
from bib_dedupe import verbose_print
from bib_dedupe.constants.colors import END
from bib_dedupe.constants.colors import GREEN
from bib_dedupe.constants.colors import ORANGE
from bib_dedupe.constants.colors import RED
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import CONTAINER_TITLE
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGE_RANGES_ADJACENT
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR

SIM_FIELDS = [
    AUTHOR,
    TITLE,
    CONTAINER_TITLE,
    YEAR,
    VOLUME,
    NUMBER,
    PAGES,
    ABSTRACT,
    DOI,
]


def match(
    pairs: pd.DataFrame,
    *,
    include_metadata: bool = False,
    debug: bool = False,
) -> pd.DataFrame:
    pairs = bib_dedupe.sim.calculate_similarities(pairs)

    print("Match started at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    start_time = time.time()

    if pairs.empty:
        end_time = time.time()
        print(f"Match completed after: {end_time - start_time:.2f} seconds")

        return pd.DataFrame(columns=["ID_1", "ID_2", "duplicate_label"])

    for field in SIM_FIELDS:
        pairs[field] = pairs[field].astype(float)

    remaining_fields = set(pairs.columns) - set(SIM_FIELDS)
    for field in remaining_fields:
        pairs[field] = pairs[field].astype(str)

    duplicate_conditions = bib_dedupe.conditions.duplicate_conditions
    if debug:
        verbose_print.pretty_print(pairs.iloc[0].to_dict())
        if pairs.shape[0] != 0:
            for item in [
                AUTHOR,
                TITLE,
                CONTAINER_TITLE,
                VOLUME,
                NUMBER,
                PAGES,
                ABSTRACT,
                YEAR,
                DOI,
                PAGE_RANGES_ADJACENT,
            ]:
                similarity = pairs.loc[0, item]
                if item == PAGE_RANGES_ADJACENT:
                    print(f"{RED}{PAGE_RANGES_ADJACENT}: {similarity}{END}")
                    continue
                if similarity > 0.9:
                    print(f"{GREEN}Similarity {item:<20}: {similarity:.2f}{END}")
                elif similarity > 0.6:
                    print(f"{ORANGE}Similarity {item:<20}: {similarity:.2f}{END}")
                else:
                    print(f"{RED}Similarity {item:<20}: {similarity:.2f}{END}")

            print("Merge conditions that matched:")
            for duplicate_condition in duplicate_conditions:
                if pairs.query(duplicate_condition).shape[0] > 0:
                    print(f"{GREEN}{duplicate_condition}{END}")
                else:
                    print(f"{duplicate_condition}")

    true_pairs = pairs.query("|".join(duplicate_conditions))

    non_duplicate_conditions = bib_dedupe.conditions.non_duplicate_conditions
    if debug:
        print()
        print(pairs)
        print("Exclude conditions:")
        for non_duplicate_condition in non_duplicate_conditions:
            if pairs.query(non_duplicate_condition).shape[0] != 0:
                print(f"{RED}{non_duplicate_condition}{END}")
            else:
                print(non_duplicate_condition)

    true_pairs = true_pairs.query("~(" + " | ".join(non_duplicate_conditions) + ")")

    true_pairs = true_pairs.drop_duplicates()

    maybe_pairs = pd.DataFrame()

    # TODO : integrate __prevent_invalid_merges here?!

    # TODO : for maybe_pairs, create a similarity score over all fields
    # (catching cases where the entrytypes/fiels are highly erroneous)

    # Get potential duplicates for manual deduplication
    maybe_pairs = pairs[
        (pairs[TITLE] > 0.85) & (pairs["author"] > 0.75)
        | (pairs[TITLE] > 0.8) & (pairs[ABSTRACT] > 0.8)
        | (pairs[TITLE] > 0.8) & (pairs[CONTAINER_TITLE] > 0.8)
        | (pd.isna(pairs[DOI]) | (pairs[DOI] > 0.99) | (pairs[DOI] == 0))
        & ~(
            (
                pd.to_numeric(pairs["year_1"], errors="coerce")
                - pd.to_numeric(pairs["year_2"], errors="coerce")
                > 1
            )
            | (
                pd.to_numeric(pairs["year_2"], errors="coerce")
                - pd.to_numeric(pairs["year_1"], errors="coerce")
                > 1
            )
        )
    ]

    # # Get pairs required for manual dedup which are not in true pairs
    # maybe_pairs = maybe_pairs[~maybe_pairs.set_index(['record_ID1', 'record_ID2'])
    # .index.isin(true_pairs.set_index(['record_ID1', 'record_ID2']).index)]

    # # Add in problem doi matching pairs and different year data in ManualDedup
    # important_mismatch = pd.concat([true_pairs_mismatch_doi, year_mismatch_major])
    # important_mismatch = true_pairs_mismatch_doi
    # maybe_pairs = pd.concat([maybe_pairs, important_mismatch])
    maybe_pairs = maybe_pairs.drop_duplicates()
    # Drop from maybe_pairs where ID_1 ID_2 combinations are in true_pairs
    maybe_pairs = maybe_pairs[
        ~maybe_pairs.set_index(["ID_1", "ID_2"]).index.isin(
            true_pairs.set_index(["ID_1", "ID_2"]).index
        )
    ]

    end_time = time.time()
    print(f"Match completed after: {end_time - start_time:.2f} seconds")

    # TODO : drop metadata if include_metadata False

    # Add a label column to each dataframe
    true_pairs["duplicate_label"] = "duplicate"
    maybe_pairs["duplicate_label"] = "maybe"

    # Select the ID_1 and ID_2 fields and the new label column
    true_pairs = true_pairs[["ID_1", "ID_2", "duplicate_label"]]
    maybe_pairs = maybe_pairs[["ID_1", "ID_2", "duplicate_label"]]

    # Concatenate the dataframes
    result_df = pd.concat([true_pairs, maybe_pairs])

    return result_df
