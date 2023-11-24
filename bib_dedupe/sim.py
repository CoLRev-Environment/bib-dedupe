#! /usr/bin/env python
"""Similarities for dedupe"""
import re
from datetime import datetime

import colrev.env.language_service
import numpy as np
import pandas as pd
from colrev.constants import Fields
from rapidfuzz import fuzz


def calculate_token_sort_ratio_similarity(
    array_1: np.array, array_2: np.array
) -> np.array:
    """Calculate the token sort ratio similarity between two arrays."""
    result = np.zeros(len(array_1))
    for i in range(len(array_1)):
        if array_1[i] != "" and array_2[i] != "":
            result[i] = fuzz.token_sort_ratio(str(array_1[i]), str(array_2[i])) / 100
    return result


def calculate_author_similarity(
    author_array_1: np.array,
    author_full_array_1: np.array,
    author_array_2: np.array,
    author_full_array_2: np.array,
) -> np.array:
    """
    Calculate the author similarity between two arrays.
    """

    def calculate_similarity(a1: str, a_full1: str, a2: str, a_full2: str) -> float:
        if a1 == a2:  # to save computational time
            return 1.0

        abbreviated_similarity = (
            fuzz.token_sort_ratio(a1[:200], a2[:200]) / 100
            if len(a1) > 200 or len(a2) > 200
            else 0
        )
        # print(abbreviated_similarity)
        author_partial_diff = fuzz.partial_ratio(a1, a2) / 100
        # print(author_partial_diff)
        author_diff = fuzz.token_sort_ratio(a1, a2) / 100
        # print(author_diff)
        author_full_diff = 0.0
        if a_full1 != "" and a_full2 != "":
            author_full_diff = fuzz.token_sort_ratio(a_full1, a_full2) / 100
        # print(abbreviated_similarity, author_partial_diff, author_diff, author_full_diff)
        # print(max(abbreviated_similarity, author_partial_diff, author_diff, author_full_diff))
        return max(
            abbreviated_similarity, author_partial_diff, author_diff, author_full_diff
        )

    similarities = np.array(
        [
            calculate_similarity(str(a1), str(a_full1), str(a2), str(a_full2))
            for a1, a_full1, a2, a_full2 in zip(
                author_array_1, author_full_array_1, author_array_2, author_full_array_2
            )
        ]
    )

    return similarities


def calculate_page_similarity(
    pages_array_1: np.array, pages_array_2: np.array
) -> np.array:
    """
    Calculate the page similarity between two arrays.
    """

    def calculate_similarity(p1: str, p2: str) -> float:
        p1 = re.sub(r"[a-zA-Z]", "", p1)
        p2 = re.sub(r"[a-zA-Z]", "", p2)

        p1_match = re.search(r"\d+", p1)
        p1 = p1_match.group() if p1_match else ""
        p2_match = re.search(r"\d+", p2)
        p2 = p2_match.group() if p2_match else ""
        if p1 != "" and p2 != "" and p1 == p2:
            return 1
        else:
            return fuzz.token_sort_ratio(p1, p2) / 100

    similarities = np.array(
        [
            calculate_similarity(str(p1), str(p2))
            for p1, p2 in zip(pages_array_1, pages_array_2)
        ]
    )

    return similarities


def calculate_title_similarity(
    title_array_1: np.array, title_array_2: np.array, debug: bool = False
) -> np.array:
    """
    Calculate the title similarity between two arrays.
    """

    def calculate_similarity(t1: str, t2: str) -> float:
        t1 = str(t1)
        t2 = str(t2)

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

    similarities = np.array(
        [
            calculate_similarity(str(t1), str(t2))
            for t1, t2 in zip(title_array_1, title_array_2)
        ]
    )

    return similarities


def calculate_year_similarity(
    year_array_1: np.array, year_array_2: np.array
) -> np.array:
    """
    Calculate the similarity between two arrays of years.
    """

    # Convert arrays to integers, invalid conversions will be replaced with -1
    convert_to_int = np.vectorize(lambda x: int(x) if x.isdigit() else -1)
    year_array_1 = convert_to_int(year_array_1.astype(str))
    year_array_2 = convert_to_int(year_array_2.astype(str))

    # Note: fails when strings are passed (see test case "foo")
    # # Convert arrays to integers, invalid conversions will be replaced with -1
    # year_array_1 = np.where(
    #     np.char.isdigit(year_array_1.astype(str)), year_array_1.astype(int), -1
    # )
    # year_array_2 = np.where(
    #     np.char.isdigit(year_array_2.astype(str)), year_array_2.astype(int), -1
    # )

    # Calculate absolute difference between the arrays
    year_diff = np.abs(year_array_1 - year_array_2)

    # Calculate similarity based on the difference
    similarity = np.where(
        year_diff == 0,
        1.0,
        np.where(year_diff == 1, 0.95, np.where(year_diff == 2, 0.8, 0)),
    )

    # Set similarity to 0 where any of the years is -1
    similarity = np.where((year_array_1 == -1) | (year_array_2 == -1), 0, similarity)

    return similarity


def calculate_number_similarity(
    number_array_1: np.array, number_array_2: np.array
) -> np.array:
    """
    Calculate the similarity between two arrays of numbers.
    """

    def calculate_number_diff(n1_str: str, n2_str: str) -> float:
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

    return np.vectorize(calculate_number_diff)(number_array_1, number_array_2)


J_TRANSLATIONS = {"nati medi j chin": "zhon yi xue za zhi"}


def calculate_container_similarity(
    container_array_1: np.array, container_array_2: np.array
) -> np.array:
    """
    Calculate the similarity between two arrays of containers.
    """

    def calculate_container_diff(ct_1: str, ct_2: str) -> float:
        if ct_1 != "" and ct_2 != "":
            if ct_1 in J_TRANSLATIONS and J_TRANSLATIONS[ct_1] == ct_2:
                return 1.0
            if ct_2 in J_TRANSLATIONS and J_TRANSLATIONS[ct_2] == ct_1:
                return 1.0

            abbreviation_match = 0
            if " " not in ct_1 and " " in ct_2:
                first_letters_1 = ct_1
                first_letters_2 = "".join(word[0] for word in ct_2.split())
                abbreviation_match = 1 if first_letters_1 == first_letters_2 else 0
            if " " not in ct_2 and " " in ct_1:
                first_letters_1 = "".join(word[0] for word in ct_1.split())
                first_letters_2 = ct_2
                abbreviation_match = 1 if first_letters_1 == first_letters_2 else 0
            word_match = 1
            words_1 = ct_1.split()
            words_2 = ct_2.split()
            if len(words_1) != len(words_2):
                word_match = 0
            else:
                for word_1, word_2 in zip(words_1, words_2):
                    if not word_1.startswith(word_2) and not word_2.startswith(word_1):
                        word_match = 0
                        break

            overall_similarity = fuzz.partial_ratio(str(ct_1), str(ct_2)) / 100

            return max(overall_similarity, abbreviation_match, word_match)
        else:
            return 0

    return np.vectorize(calculate_container_diff)(container_array_1, container_array_2)


def calculate_title_partial_ratio(title_1: np.array, title_2: np.array) -> np.array:
    """
    Calculate the partial ratio between two arrays of titles.
    """
    return np.vectorize(
        lambda t1, t2: fuzz.partial_ratio(str(t1), str(t2)) / 100
        if t1 != "" and t2 != ""
        else 0
    )(title_1, title_2)


def calculate_similarities(pairs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate similarities between pairs of data in a DataFrame.

    Args:
        pairs_df (pd.DataFrame): DataFrame containing pairs of data.

    Returns:
        pd.DataFrame: DataFrame with calculated similarities.
    """
    # Add similarities if both fields exist

    print("Start sim at", datetime.now())

    similarity_functions = {
        Fields.AUTHOR: calculate_author_similarity,
        Fields.PAGES: calculate_page_similarity,
        Fields.TITLE: calculate_title_similarity,
        Fields.YEAR: calculate_year_similarity,
        Fields.NUMBER: calculate_number_similarity,
        Fields.CONTAINER_TITLE: calculate_container_similarity,
        "title_partial_ratio": calculate_title_partial_ratio,
        Fields.VOLUME: calculate_token_sort_ratio_similarity,
        Fields.ABSTRACT: calculate_token_sort_ratio_similarity,
        Fields.ISBN: calculate_token_sort_ratio_similarity,
        Fields.DOI: calculate_token_sort_ratio_similarity,
    }

    for field, function in similarity_functions.items():
        if function == calculate_author_similarity:
            pairs_df[field] = calculate_author_similarity(
                pairs_df[f"{field}_1"].values,
                pairs_df["author_full_1"].values,
                pairs_df[f"{field}_2"].values,
                pairs_df["author_full_2"].values,
            )

        elif function == calculate_title_partial_ratio:
            pairs_df["title_partial_ratio"] = function(  # type: ignore
                pairs_df["title_1"].values, pairs_df["title_2"].values
            )

        else:
            pairs_df[field] = function(  # type: ignore
                pairs_df[f"{field}_1"].values, pairs_df[f"{field}_2"].values
            )

    return pairs_df
