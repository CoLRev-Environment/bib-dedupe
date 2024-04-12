#! /usr/bin/env python
"""Similarities for dedupe"""
import concurrent.futures
import re
import time
from datetime import datetime

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

from bib_dedupe import verbose_print
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import CONTAINER_TITLE
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import ID
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGE_RANGES_ADJACENT
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR

TITLE_STOPWORDS = ["the", "a", "an", "in", "on", "at", "and", "or", "of"]


def sim_token_sort_ratio(string_1: str, string_2: str) -> float:
    """Calculate the token sort ratio similarity between two strings."""
    if string_1 != "" and string_2 != "":
        return fuzz.token_sort_ratio(string_1, string_2) / 100
    return 0.0


def sim_author(
    author_1: str,
    author_full_1: str,
    author_2: str,
    author_full_2: str,
) -> float:
    """
    Calculate the author similarity between two strings.
    """

    if author_1 == "" and author_2 == "":
        return 0.0

    if author_1 == author_2:  # to save computational time
        return 1.0

    author_1 = author_1.replace("vander", "")
    author_2 = author_2.replace("vander", "")

    abbreviated = (
        fuzz.token_sort_ratio(author_1[:200], author_2[:200]) / 100
        if len(author_1) > 200 or len(author_2) > 200
        else 0
    )
    author_partial_diff = fuzz.partial_ratio(author_1, author_2) / 100

    author_diff = 0.0

    if len(author_full_1) > 5 and len(author_full_2) > 5:
        # Extract capital letters from both author_full_1 and author_full_2
        capital_letters_author_full_1 = re.findall(r"[A-Z]", author_full_1)
        capital_letters_author_full_2 = re.findall(r"[A-Z]", author_full_2)
        # Calculate similarity of capital letters in author_full_1 and author_full_2
        capital_letters = (
            fuzz.token_sort_ratio(
                " ".join(capital_letters_author_full_1),
                " ".join(capital_letters_author_full_2),
            )
            / 100
        )
        author_diff = capital_letters

    author_full_diff = 0.0

    if author_full_1 != "" and author_full_2 != "":
        author_full_diff = fuzz.token_sort_ratio(author_full_1, author_full_2) / 100

    return max(abbreviated, author_partial_diff, author_diff, author_full_diff)


def sim_page(pages_string_1: str, pages_string_2: str) -> float:
    """
    Calculate the page similarity between two strings.
    """

    pages_string_1 = re.sub(r"[a-zA-Z]", "", pages_string_1)
    pages_string_2 = re.sub(r"[a-zA-Z]", "", pages_string_2)

    if pages_string_1 == "" and pages_string_2 == "":
        return 0.0

    if (
        (
            (pages_string_1.endswith(pages_string_2) and pages_string_2.isdigit())
            or (pages_string_2.endswith(pages_string_1) and pages_string_1.isdigit())
        )
        and pages_string_1 != ""
        and pages_string_2 != ""
    ):
        return 1.0

    pages_string_1_match = re.search(r"\d+", pages_string_1)
    pages_string_1 = pages_string_1_match.group() if pages_string_1_match else ""
    pages_string_2_match = re.search(r"\d+", pages_string_2)
    pages_string_2 = pages_string_2_match.group() if pages_string_2_match else ""

    if (
        pages_string_1 != ""
        and pages_string_2 != ""
        and pages_string_1 == pages_string_2
    ):
        return 1
    else:
        return fuzz.token_sort_ratio(pages_string_1, pages_string_2) / 100


def sim_title(title_1: str, title_2: str, debug: bool = False) -> float:
    """
    Calculate the title similarity between two strings.
    """

    t1 = str(title_1)
    t2 = str(title_2)

    if t1 == "" and t2 == "":
        return 0.0

    if t1.replace(" ", "") == t2.replace(" ", "") and t1.replace(" ", "") != "":
        return 1.0

    # comment/reply etc.
    if any(
        [
            ((term in t1 and term not in t2) or (term in t2 and term not in t1))
            for term in [
                "comment",
                "response",
                "reply",
            ]
        ]
    ):
        return 0

    # In long titles, secondary titles may not be added in all cases
    if len(t1) > 60 and len(t2) > 60 and t1.startswith(t2) or t2.startswith(t1):
        return 1.0

    # Remove chemical formulae
    if "[" in t1:
        t1 = re.sub(r"\[[a-z0-9 ]{1,5}\]", "", t1)
    if "[" in t2:
        t2 = re.sub(r"\[[a-z0-9 ]{1,5}\]", "", t2)

    # Similarity for mismatching numbers (part 1 vs 2) should be 0
    t1_digits = re.findall(r"(?<!\[)\d+", t1)
    t2_digits = re.findall(r"(?<!\[)\d+", t2)
    if (
        t1_digits != t2_digits
        and "".join(t1_digits) != "".join(t2_digits)
        and len(t1_digits) < 3
    ):
        if debug:
            verbose_print.print(f"mismatching digits: {t1_digits} - {t2_digits}")
        return 0

    # Women vs men split studies
    if any(
        [
            ((term in t1 and term not in t2) or (term in t2 and term not in t1))
            for term in [
                "women",
                "adult",
                "pediatric",
                "protocol",
                "vivo",
                "vitro",
                "rats",
                "cats",
            ]
        ]
    ):
        return 0

    if any(term in t1 for term in ["part", "effect", "treatment"]):
        t1_parts = re.findall(r"part [a-z]", t1)
        t2_parts = re.findall(r"part [a-z]", t2)
        if t1_parts != t2_parts and len(t1_digits) < 3:
            return 0

        effect_1 = re.findall(r"effect[s]? of (\w+)", t1)
        effect_2 = re.findall(r"effect[s]? of (\w+)", t2)
        if effect_1 != effect_2:
            return 0

        treatment_1 = re.findall(r"treatment of (\w+)", t1)
        treatment_2 = re.findall(r"treatment of (\w+)", t2)
        if treatment_1 != treatment_2:
            return 0

        patients_1 = re.findall(r"(\w+) patients", t1)
        patients_2 = re.findall(r"(\w+) patients", t2)
        if patients_1 != patients_2:
            return 0

    if t1.endswith(t2) or t2.endswith(t1):
        return 1.0

    # Remove common stopwords from t1 and t2
    t1 = " ".join(word for word in t1.split() if word not in TITLE_STOPWORDS)
    t2 = " ".join(word for word in t2.split() if word not in TITLE_STOPWORDS)

    # Insert a space between digits that come directly after a string
    t1 = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t1)
    t2 = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t2)

    title_diff = fuzz.ratio(t1, t2) / 100

    # Title fields containing translated version of the title
    if title_diff < 0.7:
        if len(t1) > (1.7 * len(t2)):
            partial_ratio = fuzz.partial_ratio(t1, t2) / 100
            if partial_ratio > title_diff:
                return partial_ratio
        if len(t2) > (1.7 * len(t1)):
            partial_ratio = fuzz.partial_ratio(t2, t1) / 100
            if partial_ratio > title_diff:
                return partial_ratio

    return title_diff


def sim_year(year_1_str: str, year_2_str: str) -> float:
    """
    Calculate the similarity between two years.
    """

    # Convert years to integers, invalid conversions will be replaced with -1
    def convert_to_int(year_str: str) -> int:
        if year_str.isdigit():
            return int(year_str)
        else:
            return -1

    year_1 = convert_to_int(year_1_str)
    year_2 = convert_to_int(year_2_str)

    # Calculate absolute difference between the years
    year_diff = abs(year_1 - year_2)

    # Calculate similarity based on the difference
    similarity = (
        1.0
        if year_diff == 0
        else 0.95
        if year_diff == 1
        else 0.8
        if year_diff == 2
        else 0
    )

    # Set similarity to 0 where any of the years is -1
    similarity = 0 if year_1 == -1 or year_2 == -1 else similarity

    return similarity


def sim_doi(doi_1_str: str, doi_2_str: str) -> float:
    if doi_1_str == "" or doi_2_str == "":
        return 0

    return fuzz.ratio(doi_1_str, doi_2_str) / 100


def sim_number(n1_str: str, n2_str: str) -> float:
    """
    Calculate the similarity between two numbers.
    """

    if n1_str == "" or n2_str == "":
        return 0

    n1 = int(n1_str) if str(n1_str).isdigit() else 0
    n2 = int(n2_str) if str(n2_str).isdigit() else 0
    if n1 > 12 and n2 > 12:
        number_diff = abs(n1 - n2)
        if number_diff == 0:
            return 1.0
        elif number_diff <= 2:
            return 0.95
        else:
            return 0.0
    else:
        # some journals have numbers like 3/4 (which can be abbreviated)
        return fuzz.token_sort_ratio(str(n1), str(n2)) / 100


def sim_volume(v1_str: str, v2_str: str) -> float:
    """
    Calculate the similarity between two volumes.
    """

    if v1_str == "" or v2_str == "":
        return 0

    v1 = int(v1_str) if str(v1_str).isdigit() else 0
    v2 = int(v2_str) if str(v2_str).isdigit() else 0

    if v1 == v2:
        return 1.0
    return 0.0


def sim_abstract(abstract_1: str, abstract_2: str) -> float:
    abstract_1 = str(abstract_1)
    abstract_2 = str(abstract_2)

    if abstract_1 == "" or abstract_2 == "":
        return 0.0

    if len(abstract_1) > 500 and len(abstract_2) > 500:
        if abstract_1.startswith(abstract_2[:-100]) or abstract_2.startswith(
            abstract_1[:-100]
        ):
            return 1.0

    return fuzz.ratio(abstract_1, str(abstract_2)) / 100


def sim_container_title(container_1: str, container_2: str) -> float:
    """
    Calculate the similarity between two containers.
    """

    if container_1 == "" or container_2 == "":
        return 0.0

    if ("euro " in container_1 and "am " in container_2) or (
        "euro " in container_2 and "am " in container_1
    ):
        return 0.0

    container_1 = container_1.replace("res", "")
    container_2 = container_2.replace("res", "")

    abbreviation_match = 0
    if " " not in container_1 and " " in container_2:
        first_letters_1 = container_1
        first_letters_2 = "".join(word[0] for word in container_2.split())
        abbreviation_match = 1 if first_letters_1 == first_letters_2 else 0
    if " " not in container_2 and " " in container_1:
        first_letters_1 = "".join(word[0] for word in container_1.split())
        first_letters_2 = container_2
        abbreviation_match = 1 if first_letters_1 == first_letters_2 else 0
    word_match = 1
    words_1 = container_1.split()
    words_2 = container_2.split()
    if len(words_1) != len(words_2):
        word_match = 0
    else:
        for word_1, word_2 in zip(words_1, words_2):
            if not word_1.startswith(word_2) and not word_2.startswith(word_1):
                word_match = 0
                break

    spaces_1 = container_1.count(" ")
    spaces_2 = container_2.count(" ")

    if spaces_1 < 5 and spaces_2 < 5:
        if container_1.startswith(container_2) or container_2.startswith(container_1):
            return 1.0
        overall = fuzz.ratio(str(container_1), str(container_2)) / 100
    else:
        overall = fuzz.partial_ratio(str(container_1), str(container_2)) / 100

    return max(overall, abbreviation_match, word_match)


def page_ranges_adjacent(row: pd.Series) -> str:
    """
    This function checks if the page ranges of two articles are adjacent.

    Parameters:
    row (pd.Series): A row of a DataFrame containing the page ranges of two articles.

    Returns:
    float: Returns 1.0 if the page ranges are adjacent, 0.0 otherwise.
    """
    if row["pages_1"] == row["pages_2"]:
        return ""
    if not re.match(r"\d{1,}-\d{1,}", row["pages_1"]) or not re.match(
        r"\d{1,}-\d{1,}", row["pages_2"]
    ):
        return ""

    pages_1 = row["pages_1"].split("-")
    pages_2 = row["pages_2"].split("-")
    if len(pages_1) == 2 and len(pages_2) == 2:
        pages_1_start, pages_1_end = map(int, pages_1)

        pages_2_start, pages_2_end = map(int, pages_2)

        if pages_1_end + 1 == pages_2_start or pages_2_end + 1 == pages_1_start:
            return "adjacent"

        if pages_1_end < pages_2_start or pages_2_end < pages_1_start:
            return "non_overlapping"

    return ""


similarity_functions = {
    PAGES: sim_page,
    TITLE: sim_title,
    YEAR: sim_year,
    NUMBER: sim_number,
    CONTAINER_TITLE: sim_container_title,
    VOLUME: sim_volume,
    ABSTRACT: sim_abstract,
    DOI: sim_doi,
}


def process_df_split(split_df: pd.DataFrame) -> pd.DataFrame:
    for index, row in split_df.iterrows():
        split_df.loc[index, AUTHOR] = sim_author(
            str(row["author_1"]),
            str(row["author_full_1"]),
            str(row["author_2"]),
            str(row["author_full_2"]),
        )

        for field, function in similarity_functions.items():
            split_df.loc[index, field] = function(  # type: ignore
                str(row[f"{field}_1"]), str(row[f"{field}_2"])
            )

        split_df.loc[index, PAGE_RANGES_ADJACENT] = page_ranges_adjacent(row)

    return split_df


def calculate_similarities(pairs_df: pd.DataFrame, cpu: int) -> pd.DataFrame:
    """
    Calculate similarities between pairs of data in a DataFrame.

    Args:
        pairs_df (pd.DataFrame): DataFrame containing pairs of data.

    Returns:
        pd.DataFrame: DataFrame with calculated similarities.
    """

    required_columns = [
        f"{col}_1"
        for col in [
            ID,
            "author_full",
            TITLE,
            YEAR,
            ABSTRACT,
            AUTHOR,
            CONTAINER_TITLE,
            DOI,
            NUMBER,
            PAGES,
            VOLUME,
        ]
    ] + [
        f"{col}_2"
        for col in [
            ID,
            "author_full",
            TITLE,
            YEAR,
            ABSTRACT,
            AUTHOR,
            CONTAINER_TITLE,
            DOI,
            NUMBER,
            PAGES,
            VOLUME,
        ]
    ]
    missing_columns = list(
        filter(lambda col: col not in pairs_df.columns, required_columns)
    )
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    verbose_print.print(
        "Sim started at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    start_time = time.time()
    if cpu == 1:
        pairs_df = process_df_split(pairs_df)
    else:
        df_split = np.array_split(pairs_df, 8)

        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            results = executor.map(process_df_split, df_split)

        pairs_df = pd.concat(list(results))

    end_time = time.time()
    verbose_print.print(f"Sim completed after: {end_time - start_time:.2f} seconds")

    return pairs_df
