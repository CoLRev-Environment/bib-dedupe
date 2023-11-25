#! /usr/bin/env python
"""Similarities for dedupe"""
import concurrent.futures
import re
import time
from datetime import datetime

import colrev.env.language_service
import numpy as np
import pandas as pd
from rapidfuzz import fuzz

from bib_dedupe.constants import Fields


def calculate_token_sort_ratio_similarity(string_1: str, string_2: str) -> float:
    """Calculate the token sort ratio similarity between two strings."""
    if string_1 != "" and string_2 != "":
        return fuzz.token_sort_ratio(string_1, string_2) / 100
    return 0.0


def calculate_author_similarity(
    author_1: str,
    author_full_1: str,
    author_2: str,
    author_full_2: str,
) -> float:
    """
    Calculate the author similarity between two strings.
    """

    if author_1 == author_2:  # to save computational time
        return 1.0

    abbreviated_similarity = (
        fuzz.token_sort_ratio(author_1[:200], author_2[:200]) / 100
        if len(author_1) > 200 or len(author_2) > 200
        else 0
    )
    author_partial_diff = fuzz.partial_ratio(author_1, author_2) / 100
    author_diff = fuzz.token_sort_ratio(author_1, author_2) / 100
    author_full_diff = 0.0
    if author_full_1 != "" and author_full_2 != "":
        author_full_diff = fuzz.token_sort_ratio(author_full_1, author_full_2) / 100
    return max(
        abbreviated_similarity, author_partial_diff, author_diff, author_full_diff
    )


def calculate_page_similarity(pages_string_1: str, pages_string_2: str) -> float:
    """
    Calculate the page similarity between two strings.
    """

    pages_string_1 = re.sub(r"[a-zA-Z]", "", pages_string_1)
    pages_string_2 = re.sub(r"[a-zA-Z]", "", pages_string_2)

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


def calculate_title_similarity(
    title_1: str, title_2: str, debug: bool = False
) -> float:
    """
    Calculate the title similarity between two strings.
    """

    t1 = str(title_1)
    t2 = str(title_2)

    if t1.replace(" ", "") == t2.replace(" ", ""):
        return 1.0

    if len(t1) > 1.7 * len(t2):
        language_service = colrev.env.language_service.LanguageService()
        substring_similarity = fuzz.ratio(t1[: len(t2)], t2) / 100
        if substring_similarity > 0.97:
            lang_second_half = language_service.compute_language(text=t1[len(t2) :])
            if lang_second_half != "eng":
                t1 = t1[: len(t2)]

    if len(t2) > 1.7 * len(t1):
        language_service = colrev.env.language_service.LanguageService()
        substring_similarity = fuzz.ratio(t2[: len(t1)], t1) / 100
        if substring_similarity > 0.97:
            lang_second_half = language_service.compute_language(text=t2[len(t1) :])
            if lang_second_half != "eng":
                t2 = t2[: len(t1)]

    # Similarity for mismatching numbers (part 1 vs 2) should be 0
    t1_digits = re.findall(r"(?<!\[)\d+", t1)
    t2_digits = re.findall(r"(?<!\[)\d+", t2)
    if t1_digits != t2_digits and len(t1_digits) < 3:
        if debug:
            print(f"mismatching digits: {t1_digits} - {t2_digits}")
        return 0
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

    # Remove common stopwords from t1 and t2
    stopwords = ["the", "a", "an", "in", "on", "at", "and", "or", "of"]
    t1 = " ".join(word for word in t1.split() if word not in stopwords)
    t2 = " ".join(word for word in t2.split() if word not in stopwords)

    # Remove chemical formulae
    t1 = re.sub(r"\[[a-z0-9 ]{1,5}\]", "", t1)
    t2 = re.sub(r"\[[a-z0-9 ]{1,5}\]", "", t2)

    # Insert a space between digits that come directly after a string
    t1 = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t1)
    t2 = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t2)

    title_diff = fuzz.token_sort_ratio(t1, t2) / 100

    return title_diff


def calculate_year_similarity(year_1_str: str, year_2_str: str) -> float:
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


def calculate_number_similarity(n1_str: str, n2_str: str) -> float:
    """
    Calculate the similarity between two numbers.
    """

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
        # Fields.NUMBER,  # some journals have numbers like 3/4 (which can be abbreviated)
        return fuzz.token_sort_ratio(str(n1), str(n2)) / 100


J_TRANSLATIONS = {"nati medi j chin": "zhon yi xue za zhi"}


def calculate_container_similarity(container_1: str, container_2: str) -> float:
    """
    Calculate the similarity between two containers.
    """

    if container_1 != "" and container_2 != "":
        if container_1 in J_TRANSLATIONS and J_TRANSLATIONS[container_1] == container_2:
            return 1.0
        if container_2 in J_TRANSLATIONS and J_TRANSLATIONS[container_2] == container_1:
            return 1.0

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

        overall_similarity = (
            fuzz.partial_ratio(str(container_1), str(container_2)) / 100
        )

        return max(overall_similarity, abbreviation_match, word_match)
    else:
        return 0


def calculate_title_partial_ratio(title_1: str, title_2: str) -> float:
    """
    Calculate the partial ratio between two titles.
    """
    if title_1 != "" and title_2 != "":
        return fuzz.partial_ratio(str(title_1), str(title_2)) / 100
    else:
        return 0


similarity_functions = {
    # Fields.AUTHOR: calculate_author_similarity,
    Fields.PAGES: calculate_page_similarity,
    Fields.TITLE: calculate_title_similarity,
    Fields.YEAR: calculate_year_similarity,
    Fields.NUMBER: calculate_number_similarity,
    Fields.CONTAINER_TITLE: calculate_container_similarity,
    # "title_partial_ratio": calculate_title_partial_ratio,
    Fields.VOLUME: calculate_token_sort_ratio_similarity,
    Fields.ABSTRACT: calculate_token_sort_ratio_similarity,
    Fields.ISBN: calculate_token_sort_ratio_similarity,
    Fields.DOI: calculate_token_sort_ratio_similarity,
}


def process_df_split(split_df: pd.DataFrame) -> pd.DataFrame:
    for index, row in split_df.iterrows():
        split_df.loc[index, Fields.AUTHOR] = calculate_author_similarity(
            row["author_1"],
            row["author_full_1"],
            row["author_2"],
            row["author_full_2"],
        )
        split_df.loc[index, "title_partial_ratio"] = calculate_title_partial_ratio(  # type: ignore
            row["title_1"], row["title_2"]
        )

        for field, function in similarity_functions.items():
            # if function == calculate_author_similarity:

            # elif function == calculate_title_partial_ratio:

            # else:
            split_df.loc[index, field] = function(  # type: ignore
                row[f"{field}_1"], row[f"{field}_2"]
            )

    return split_df


def calculate_similarities(pairs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate similarities between pairs of data in a DataFrame.

    Args:
        pairs_df (pd.DataFrame): DataFrame containing pairs of data.

    Returns:
        pd.DataFrame: DataFrame with calculated similarities.
    """

    print("Sim started at", datetime.now())
    start_time = time.time()

    # pairs_df = process_df_split(pairs_df)

    df_split = np.array_split(pairs_df, 8)

    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
        results = executor.map(process_df_split, df_split)

    pairs_df = pd.concat(list(results))

    end_time = time.time()
    print(f"Sim completed after: {end_time - start_time:.2f} seconds")

    return pairs_df
