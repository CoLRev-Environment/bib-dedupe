#! /usr/bin/env python
"""Module for preparing bibliographic data for deduplication."""
import concurrent.futures
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd

from bib_dedupe import verbose_print
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import BOOKTITLE
from bib_dedupe.constants.fields import CONTAINER_TITLE
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import ENTRYTYPE
from bib_dedupe.constants.fields import ID
from bib_dedupe.constants.fields import JOURNAL
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import SEARCH_SET
from bib_dedupe.constants.fields import SERIES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR
from bib_dedupe.prep_abstract import prep_abstract
from bib_dedupe.prep_author import prep_authors
from bib_dedupe.prep_author import select_authors
from bib_dedupe.prep_container_title import get_container_title_short
from bib_dedupe.prep_container_title import prep_container_title
from bib_dedupe.prep_container_title import set_container_title
from bib_dedupe.prep_doi import prep_doi
from bib_dedupe.prep_number import prep_number
from bib_dedupe.prep_pages import prep_pages
from bib_dedupe.prep_title import prep_title
from bib_dedupe.prep_volume import prep_volume
from bib_dedupe.prep_year import prep_year

pd.set_option('future.no_silent_downcasting', True)

REQUIRED_FIELDS = [ID, ENTRYTYPE, TITLE, AUTHOR, YEAR]
OPTIONAL_FIELDS = [
    JOURNAL,
    BOOKTITLE,
    SERIES,
    VOLUME,
    NUMBER,
    PAGES,
    ABSTRACT,
    DOI,
    SEARCH_SET,
]
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS + [CONTAINER_TITLE]

function_mapping = {
    AUTHOR: prep_authors,
    TITLE: prep_title,
    CONTAINER_TITLE: prep_container_title,
    YEAR: prep_year,
    VOLUME: prep_volume,
    NUMBER: prep_number,
    PAGES: prep_pages,
    ABSTRACT: prep_abstract,
    DOI: prep_doi,
}


def prepare_df_split(split_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a split dataframe for deduplication.

    Args:
        split_df: A split dataframe.

    Returns:
        The processed dataframe.
    """
    split_df.replace(
        to_replace={
            "UNKNOWN": "",
            "n/a": "",
            "N/A": "",
            "NA": "",
            "&amp;": "and",
            " & ": " and ",
            " + ": " and ",
        },
        inplace=True,
    )

    set_container_title(split_df)

    split_df["author_full"] = split_df[AUTHOR]

    for field, function in function_mapping.items():
        split_df[field] = function(split_df[field].values)  # type: ignore

    split_df[AUTHOR] = select_authors(split_df[AUTHOR].values)

    # Fix cases where years are erroneously entered into pages field
    split_df.loc[split_df[PAGES] == split_df[YEAR], PAGES] = ""

    if BOOKTITLE in split_df.columns:
        split_df = split_df.drop(columns=[BOOKTITLE])
    if JOURNAL in split_df.columns:
        split_df = split_df.drop(columns=[JOURNAL])

    split_df = split_df.fillna("")

    return split_df


def __general_prep(records_df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform general preparation on the records dataframe.

    Args:
        records_df: The records dataframe.

    Returns:
        The prepared dataframe.
    """
    records_df = records_df.copy()

    if ID not in records_df.columns:
        records_df.loc[:, ID] = range(1, len(records_df) + 1)
    if not records_df[ID].is_unique:
        raise ValueError("ID column in records_df must be unique.")

    if ENTRYTYPE not in records_df.columns:
        records_df[ENTRYTYPE] = "article"

    missing_fields = [f for f in REQUIRED_FIELDS if f not in records_df.columns]
    assert len(missing_fields) == 0, f"Missing required fields: {missing_fields}"

    for column in records_df.columns:
        records_df[column] = (
            records_df[column]
            .replace(["#NAME?", "UNKNOWN", ""], np.nan)
        )
    if records_df[TITLE].isnull().any():
        verbose_print.print(
            "Warning: Some records have empty title field. These records will not be considered."
        )
        records_df = records_df.dropna(subset=[TITLE])

    # if columns are of type float, we need to avoid casting "3.0" to "30"
    for col in records_df.columns:
        if records_df[col].dtype == float:
            records_df[col] = records_df[col].apply(
                lambda x: str(int(x))
                if pd.notna(x) and isinstance(x, (int, float))
                else ""
            )

    for optional_field in OPTIONAL_FIELDS:
        if optional_field not in records_df.columns:
            records_df = records_df.assign(**{optional_field: ""})

    records_df = records_df.drop(
        labels=list(records_df.columns.difference(ALL_FIELDS)),
        axis=1,
    )
    records_df.loc[:, CONTAINER_TITLE] = ""
    records_df.loc[:, ALL_FIELDS] = records_df[ALL_FIELDS].astype(str)

    return records_df


def determine_cpu_count(requested_cpu: int, record_count: int) -> int:
    """
    Determines the number of CPUs to use based on the requested CPU count and the number of records.

    Args:
        requested_cpu: The requested CPU count.
        record_count: The number of records.

    Returns:
        The number of CPUs to use.
    """
    if requested_cpu == -1:
        cpu_count = os.cpu_count() or 1
    else:
        cpu_count = requested_cpu

    # For small datasets, use a single CPU
    if record_count < 100:
        cpu_count = 1

    return cpu_count


def prep(records_df: pd.DataFrame, *, cpu: int = -1) -> pd.DataFrame:
    """
    Prepare records for deduplication.

    Args:
        records_df: The records dataframe.
        cpu: The number of CPUs to use. If -1, use all available CPUs.

    Returns:
        The prepared records dataframe.
    """

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    verbose_print.print(f"Loaded {records_df.shape[0]:,} records")
    verbose_print.print(f"Prep started at {now}")
    start_time = time.time()

    if 0 == records_df.shape[0]:
        verbose_print.print("No records to prepare")
        return {}

    records_df = __general_prep(records_df)
    cpu = determine_cpu_count(cpu, records_df.shape[0])
    if cpu == 1:
        records_df = prepare_df_split(records_df)
    else:
        df_split = np.array_split(records_df, cpu)
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu) as executor:
            results = executor.map(prepare_df_split, df_split)
        records_df = pd.concat(list(results))
    records_df = records_df.assign(
        author_first=records_df[AUTHOR].str.split().str[0],
        title_short=records_df[TITLE].apply(lambda x: " ".join(x.split()[:10])),
        container_title_short=get_container_title_short(
            records_df[CONTAINER_TITLE].values
        ),
    )

    for column in records_df.columns:
        records_df.loc[records_df[column] == "nan", column] = ""

    end_time = time.time()
    verbose_print.print(f"Prep completed after: {end_time - start_time:.2f} seconds")

    return records_df
