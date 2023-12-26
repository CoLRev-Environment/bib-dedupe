#! /usr/bin/env python
"""Match for dedupe"""
import pprint
import time
from datetime import datetime

import pandas as pd

import bib_dedupe.conditions
import bib_dedupe.sim
import bib_dedupe.util
from bib_dedupe.constants import Colors
from bib_dedupe.constants import Fields

SIM_FIELDS = [
    Fields.AUTHOR,
    Fields.TITLE,
    Fields.CONTAINER_TITLE,
    Fields.YEAR,
    Fields.VOLUME,
    Fields.NUMBER,
    Fields.PAGES,
    Fields.ABSTRACT,
    Fields.ISBN,
    Fields.DOI,
]


def match(
    pairs: pd.DataFrame,
    *,
    include_metadata: bool = False,
    debug: bool = False,
) -> pd.DataFrame:
    p_printer = pprint.PrettyPrinter(indent=4, width=140, compact=False)
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

    updated_paper_pairs = pd.DataFrame()
    updated_pair_conditions = bib_dedupe.conditions.updated_pair_conditions
    if debug:
        p_printer.pprint(pairs.iloc[0].to_dict())
        print("Conditions for updated paper versions:")
        for updated_pair_condition in updated_pair_conditions:
            if pairs.query(updated_pair_condition).shape[0] != 0:
                print(f"{Colors.GREEN}{updated_pair_condition}{Colors.END}")
            else:
                print(updated_pair_condition)

    updated_paper_pairs = pairs.query("(" + " | ".join(updated_pair_conditions) + ")")

    duplicate_conditions = bib_dedupe.conditions.duplicate_conditions
    if debug:
        if pairs.shape[0] != 0:
            for item in [
                Fields.AUTHOR,
                Fields.TITLE,
                Fields.CONTAINER_TITLE,
                Fields.VOLUME,
                Fields.NUMBER,
                Fields.PAGES,
                Fields.ABSTRACT,
                Fields.YEAR,
                Fields.DOI,
                Fields.PAGE_RANGES_ADJACENT,
            ]:
                similarity = pairs.loc[0, item]
                if item == Fields.PAGE_RANGES_ADJACENT:
                    print(
                        f"{Colors.RED}{Fields.PAGE_RANGES_ADJACENT}: {similarity}{Colors.END}"
                    )
                    continue
                if similarity > 0.9:
                    print(
                        f"{Colors.GREEN}Similarity {item:<20}: {similarity:.2f}{Colors.END}"
                    )
                elif similarity > 0.6:
                    print(
                        f"{Colors.ORANGE}Similarity {item:<20}: {similarity:.2f}{Colors.END}"
                    )
                else:
                    print(
                        f"{Colors.RED}Similarity {item:<20}: {similarity:.2f}{Colors.END}"
                    )

            print("Merge conditions that matched:")
            for duplicate_condition in duplicate_conditions:
                if pairs.query(duplicate_condition).shape[0] > 0:
                    print(f"{Colors.GREEN}{duplicate_condition}{Colors.END}")
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
                print(f"{Colors.RED}{non_duplicate_condition}{Colors.END}")
            else:
                print(non_duplicate_condition)

    true_pairs = true_pairs.query("~(" + " | ".join(non_duplicate_conditions) + ")")

    # add updated pairs to true pairs
    true_pairs = pd.concat([true_pairs, updated_paper_pairs])

    true_pairs = true_pairs.drop_duplicates()

    maybe_pairs = pd.DataFrame()

    # TODO : integrate __prevent_invalid_merges here?!

    # TODO : for maybe_pairs, create a similarity score over all fields
    # (catching cases where the entrytypes/fiels are highly erroneous)

    # Get potential duplicates for manual deduplication
    maybe_pairs = pairs[
        (pairs[Fields.TITLE] > 0.85) & (pairs["author"] > 0.75)
        | (pairs[Fields.TITLE] > 0.8) & (pairs[Fields.ABSTRACT] > 0.8)
        | (pairs[Fields.TITLE] > 0.8) & (pairs[Fields.ISBN] > 0.99)
        | (pairs[Fields.TITLE] > 0.8) & (pairs[Fields.CONTAINER_TITLE] > 0.8)
        | (
            pd.isna(pairs[Fields.DOI])
            | (pairs[Fields.DOI] > 0.99)
            | (pairs[Fields.DOI] == 0)
        )
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
    updated_paper_pairs["duplicate_label"] = "updated_version"

    # Select the ID_1 and ID_2 fields and the new label column
    true_pairs = true_pairs[["ID_1", "ID_2", "duplicate_label"]]
    maybe_pairs = maybe_pairs[["ID_1", "ID_2", "duplicate_label"]]
    updated_paper_pairs = updated_paper_pairs[["ID_1", "ID_2", "duplicate_label"]]

    # Concatenate the dataframes
    result_df = pd.concat([true_pairs, maybe_pairs, updated_paper_pairs])

    return result_df
