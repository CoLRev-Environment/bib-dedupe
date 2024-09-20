#! /usr/bin/env python
"""Match for dedupe"""
import time
from datetime import datetime

import pandas as pd

import bib_dedupe.match_conditions
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
from bib_dedupe.constants.fields import DUPLICATE
from bib_dedupe.constants.fields import DUPLICATE_LABEL
from bib_dedupe.constants.fields import ID
from bib_dedupe.constants.fields import MAYBE
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGE_RANGES_ADJACENT
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import SEARCH_SET
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR

SIM_FIELDS_FLOAT = [
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

SIM_FIELDS = SIM_FIELDS_FLOAT + [PAGE_RANGES_ADJACENT]

NON_DUPLICATE_CONDITIONS = bib_dedupe.match_conditions.non_duplicate_conditions
DUPLICATE_CONDITIONS = bib_dedupe.match_conditions.duplicate_conditions


def __print_details(pairs: pd.DataFrame) -> None:
    if verbose_print.verbosity_level < 2:
        return

    verbose_print.pretty_print(pairs.iloc[0].to_dict())
    if pairs.shape[0] == 0:
        return

    for item in SIM_FIELDS:
        similarity = pairs.loc[0, item]
        if item == PAGE_RANGES_ADJACENT:
            verbose_print.print(f"{RED}{PAGE_RANGES_ADJACENT}: {similarity}{END}")
            continue
        if similarity > 0.9:
            verbose_print.print(f"{GREEN}Similarity {item:<20}: {similarity:.2f}{END}")
        elif similarity > 0.6:
            verbose_print.print(f"{ORANGE}Similarity {item:<20}: {similarity:.2f}{END}")
        else:
            verbose_print.print(f"{RED}Similarity {item:<20}: {similarity:.2f}{END}")

    verbose_print.print("Merge conditions that matched:")
    for duplicate_condition in DUPLICATE_CONDITIONS:
        if pairs.query(duplicate_condition, engine="python").shape[0] > 0:
            verbose_print.print(f"{GREEN}{duplicate_condition}{END}")
        else:
            verbose_print.print(f"{duplicate_condition}")

    verbose_print.print()
    verbose_print.print(pairs)
    verbose_print.print("Non-merge conditions that matched:")
    for non_duplicate_condition in NON_DUPLICATE_CONDITIONS:
        if pairs.query(non_duplicate_condition, engine="python").shape[0] != 0:
            verbose_print.print(f"{RED}{non_duplicate_condition}{END}")
        else:
            verbose_print.print(non_duplicate_condition)


def __get_true_pairs(pairs: pd.DataFrame) -> pd.DataFrame:
    true_pairs = pairs.query("|".join(DUPLICATE_CONDITIONS), engine="python")
    true_pairs = true_pairs.query(
        "~(" + " | ".join(NON_DUPLICATE_CONDITIONS) + ")", engine="python"
    )
    true_pairs = true_pairs.drop_duplicates()

    # Add a label column to each dataframe
    true_pairs[DUPLICATE_LABEL] = DUPLICATE
    # Select the ID_1, SEARCH_SET_1 and ID_2, SEARCH_SET_2 fields and the new label column
    true_pairs = true_pairs[
        [f"{ID}_1", f"{SEARCH_SET}_1", f"{SEARCH_SET}_2", f"{ID}_2", DUPLICATE_LABEL]
    ]

    return true_pairs


def __get_maybe_pairs(pairs: pd.DataFrame, true_pairs: pd.DataFrame) -> pd.DataFrame:
    maybe_pairs = pd.DataFrame()

    maybe_pairs = pairs[
        (pairs[TITLE] > 0.85) & (pairs["author"] > 0.75)
        | (pairs[TITLE] > 0.8) & (pairs[ABSTRACT] > 0.8)
        | (pairs[TITLE] > 0.8) & (pairs[CONTAINER_TITLE] > 0.8)
        | (pd.isna(pairs[DOI]) | (pairs[DOI] > 0.99) | (pairs[DOI] == 0))
        & ~(
            (
                pd.to_numeric(pairs[f"{YEAR}_1"], errors="coerce")
                - pd.to_numeric(pairs[f"{YEAR}_2"], errors="coerce")
                > 1
            )
            | (
                pd.to_numeric(pairs[f"{YEAR}_2"], errors="coerce")
                - pd.to_numeric(pairs[f"{YEAR}_1"], errors="coerce")
                > 1
            )
        )
    ]

    maybe_pairs = maybe_pairs.drop_duplicates()

    # Drop from maybe_pairs where ID_1 ID_2 combinations are in true_pairs
    maybe_pairs = maybe_pairs[
        ~maybe_pairs.set_index([f"{ID}_1", f"{ID}_2"]).index.isin(
            true_pairs.set_index([f"{ID}_1", f"{ID}_2"]).index
        )
    ]

    # Add a label column to each dataframe
    maybe_pairs[DUPLICATE_LABEL] = MAYBE
    # Select the ID_1, SEARCH_SET_1 and ID_2, SEARCH_SET_2 fields and the new label column
    maybe_pairs = maybe_pairs[
        [f"{ID}_1", f"{SEARCH_SET}_1", f"{SEARCH_SET}_2", f"{ID}_2", DUPLICATE_LABEL]
    ]

    return maybe_pairs


def match(pairs: pd.DataFrame, cpu: int = -1) -> pd.DataFrame:
    pairs = bib_dedupe.sim.calculate_similarities(pairs, cpu=cpu)

    verbose_print.print(
        "Match started at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    start_time = time.time()

    if pairs.empty:
        end_time = time.time()
        verbose_print.print(
            f"Match completed after: {end_time - start_time:.2f} seconds"
        )

        return pd.DataFrame(columns=[f"{ID}_1", f"{ID}_2", DUPLICATE_LABEL])

    for field in SIM_FIELDS_FLOAT:
        pairs[field] = pairs[field].astype(float)

    remaining_fields = set(pairs.columns) - set(SIM_FIELDS_FLOAT)
    for field in remaining_fields:
        pairs[field] = pairs[field].astype(str)

    __print_details(pairs)

    true_pairs = __get_true_pairs(pairs)

    maybe_pairs = __get_maybe_pairs(pairs, true_pairs)

    end_time = time.time()
    verbose_print.print(f"Match completed after: {end_time - start_time:.2f} seconds")

    return pd.concat([true_pairs, maybe_pairs])
