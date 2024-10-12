#! /usr/bin/env python
"""Debug for dedupe"""
import pandas as pd

from bib_dedupe import verbose_print
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import JOURNAL
from bib_dedupe.constants.fields import ORIGIN
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import YEAR


def percent_upper_chars(input_string: str) -> float:
    """Get the percentage of upper-case characters in a string"""
    if len(input_string) == 0:
        return 0
    return sum(map(str.isupper, input_string)) / len(input_string)


def default_merge_function_title(titles: list) -> str:
    """Default merge function for title field"""

    if len([title for title in titles if not (pd.isnull(title) or title == "")]) <= 1:
        return titles[0]

    best_title = titles[0]

    # Note : avoid switching titles
    for title in titles[1:]:
        if best_title.replace(" - ", ": ") == title.replace(" - ", ": "):
            return best_title

    best_title_upper = percent_upper_chars(best_title)

    for title in titles[1:]:
        title_upper = percent_upper_chars(title)

        if title[-1] not in ["*", "1", "2"]:
            # Relatively simple rule...
            # catches cases when best_title is all upper or title case
            if best_title_upper > title_upper:
                best_title = title
    return best_title


def default_merge_function_author(authors: list) -> str:
    """Default merge function for author field"""

    if (
        len([author for author in authors if not (pd.isnull(author) or author == "")])
        <= 1
    ):
        return authors[0]

    best_author = authors[0]

    best_author_upper = percent_upper_chars(best_author)

    for author in authors[1:]:
        author_upper = percent_upper_chars(author)

        # Prefer title case (not all-caps)
        if best_author_upper > 0.8 and author_upper <= 0.8:
            best_author = author
    return best_author


def default_merge_function_container_title(journals: list) -> str:
    """Default merge function for container-title field"""

    if (
        len(
            [
                journal
                for journal in journals
                if not (pd.isnull(journal) or journal == "")
            ]
        )
        <= 1
    ):
        return journals[0]

    journals = [
        journal for journal in journals if not (pd.isnull(journal) or journal == "")
    ]

    best_journal = journals[0]

    best_journal_upper = percent_upper_chars(best_journal)

    for journal in journals[1:]:
        journal_upper = percent_upper_chars(journal)

        # Simple heuristic to avoid abbreviations
        if "." in best_journal and "." not in journal:
            best_journal = journal
        # Relatively simple rule...
        # catches cases when best_journal is all upper or title case
        if best_journal_upper > journal_upper:
            best_journal = journal
    return best_journal


def default_merge_function_year(years: list) -> str:
    """Default merge function for year field"""
    # max() to select published version when merging with forthcoming
    years = [str(year) for year in years if not (pd.isnull(year) or year == "")]

    if not any(year.isdigit() for year in years):
        return ""
    return str(max(int(year) for year in years if year.isdigit()))


def default_merge_function_pages(pages: list) -> str:
    """Default merge function for pages field"""

    if len([page for page in pages if not (pd.isnull(page) or page == "")]) <= 1:
        return pages[0]

    pages = [page for page in pages if not (pd.isnull(page) or page == "")]

    best_pages = pages[0]
    for page in pages[1:]:
        if "--" in page and "--" not in best_pages:
            best_pages = page
    return best_pages


def default_merge_function_origin(origins: list) -> str:
    """Default merge function for origin field"""

    unique_origins = set()
    for origin in origins:
        unique_origins.update(origin.split(";"))
    return ";".join(sorted(unique_origins))


DEFAULT_MERGE_FUNCTIONS = {
    ORIGIN: default_merge_function_origin,
    TITLE: default_merge_function_title,
    AUTHOR: default_merge_function_author,
    YEAR: default_merge_function_year,
    JOURNAL: default_merge_function_container_title,
    PAGES: default_merge_function_pages,
}


def merge(
    records_df: pd.DataFrame,
    *,
    duplicate_id_sets: list,
    merge_functions: dict = DEFAULT_MERGE_FUNCTIONS,
    origin_column: str = ORIGIN,
) -> pd.DataFrame:
    """
    This function merges duplicate records in a DataFrame.

    Parameters:
    records_df (pd.DataFrame): The DataFrame containing the records.
    duplicate_id_sets (list): A list of sets, each containing IDs of duplicate records.
    merge_functions (dict, optional): A dictionary mapping column names to functions
    that determine how to merge values in that column. If not provided, default merge
    functions will be used.
    origin_column (str, optional): The name of the column to use as the origin.
    Defaults to ORIGIN.

    Returns:
    pd.DataFrame: The DataFrame with duplicate records merged.
    """

    if not records_df["ID"].is_unique:
        raise ValueError("ID column in records_df must be unique.")

    for duplicate_ids in duplicate_id_sets:
        if not set(duplicate_ids).issubset(set(records_df["ID"].tolist())):
            raise ValueError("Not all duplicate IDs are in the records DataFrame.")

    # Cast all columns in records_df to strings
    records_df = records_df.astype(str)

    if origin_column not in records_df.columns:
        verbose_print.print(f"Add missing origin column ({origin_column})", level=2)
        records_df[origin_column] = records_df["ID"]

    if origin_column not in merge_functions:
        verbose_print.print("Add default_merge_function_origin", level=2)
        merge_functions[origin_column] = DEFAULT_MERGE_FUNCTIONS[ORIGIN]
    if merge_functions == DEFAULT_MERGE_FUNCTIONS:
        verbose_print.print("Use DEFAULT_MERGE_FUNCTIONS", level=2)
    else:
        # Add missing items to merge_function based on DEFAULT_MERGE_FUNCTIONS
        for key, value in DEFAULT_MERGE_FUNCTIONS.items():
            if key not in merge_functions:
                verbose_print.print(
                    f"For {key} add {DEFAULT_MERGE_FUNCTIONS[key].__name__}()", level=2
                )
                merge_functions[key] = value

    non_duplicate_ids = set(records_df["ID"].tolist())
    for duplicate_ids in duplicate_id_sets:
        non_duplicate_ids -= set(duplicate_ids)
        # Apply custom merge functions
        for column, merge_func in merge_functions.items():
            if column in records_df.columns:
                values = records_df.loc[
                    records_df["ID"].isin(duplicate_ids), column
                ].tolist()
                merged_value = merge_func(values)
                verbose_print.print(f"{column}: {values} -> {merged_value}", level=2)
                records_df.loc[
                    records_df["ID"].isin(duplicate_ids), column
                ] = merged_value

    # NOTE: merge_functions must return string. cannot assign object to pandas cell!
    for non_duplicate_id in non_duplicate_ids:
        for column, merge_func in merge_functions.items():
            if column in records_df.columns:
                if column != "nr_intext_citations":
                    continue
                value = records_df.loc[
                    records_df["ID"] == non_duplicate_id, column
                ].tolist()
                merged_value = merge_func(value)
                records_df.loc[
                    records_df["ID"] == non_duplicate_id, column
                ] = merged_value

    to_drop = [o for ol in duplicate_id_sets for o in ol[1:]]

    merged_df = records_df[~records_df["ID"].isin(to_drop)]

    return merged_df
