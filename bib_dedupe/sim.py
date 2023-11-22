#! /usr/bin/env python
"""Similarities for dedupe"""
import re

import colrev.env.language_service
import pandas as pd
from colrev.constants import Fields
from rapidfuzz import fuzz


def calculate_similarities(pairs_df: pd.DataFrame) -> pd.DataFrame:
    # Add similarities if both fields exist

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
        if function == calculate_token_sort_ratio_similarity:
            pairs_df[field] = pairs_df.apply(function, args=(field,), axis=1)
        else:
            pairs_df[field] = pairs_df.apply(function, axis=1)


def calculate_token_sort_ratio_similarity(row: pd.Series, sim_field: str) -> float:
    if row[f"{sim_field}_1"] != "" and row[f"{sim_field}_2"] != "":
        return (
            fuzz.token_sort_ratio(
                str(row[f"{sim_field}_1"]), str(row[f"{sim_field}_2"])
            )
            / 100
        )
    else:
        return 0


def calculate_author_similarity(row: pd.Series) -> float:
    if "author_1" in row and "author_2" in row:
        author_1 = str(row["author_1"])
        author_2 = str(row["author_2"])

        abbreviated_similarity = 0
        if len(author_1) > 200 or len(author_2) > 200:
            abbreviated_similarity = (
                fuzz.token_sort_ratio(author_1[:200], author_2[:200]) / 100
            )

        author_partial_diff = fuzz.partial_ratio(author_1, author_2) / 100
        author_diff = fuzz.token_sort_ratio(author_1, author_2) / 100
        author_full_diff = (
            fuzz.token_sort_ratio(str(row["author_full_1"]), str(row["author_full_2"]))
            / 100
        )
        author_diff = max(
            author_diff,
            author_full_diff,
            author_partial_diff,
            abbreviated_similarity,
        )
        return author_diff
    return 0


def calculate_page_similarity(row: pd.Series) -> float:
    if "pages_1" in row and "pages_2" in row:
        pages_1 = re.sub(r"[a-zA-Z]", "", row["pages_1"])
        pages_2 = re.sub(r"[a-zA-Z]", "", row["pages_2"])

        pages_1_match = re.search(r"\d+", pages_1)
        pages_1 = pages_1_match.group() if pages_1_match else ""
        pages_2_match = re.search(r"\d+", pages_2)
        pages_2 = pages_2_match.group() if pages_2_match else ""
        if pages_1 != "" and pages_2 != "" and pages_1 == pages_2:
            return 1
        else:
            return fuzz.token_sort_ratio(str(row["pages_1"]), str(row["pages_2"])) / 100
    return 0


def calculate_title_similarity(row: pd.Series) -> float:
    if "title_1" in row and "title_2" in row:
        title_1 = str(row["title_1"])
        title_2 = str(row["title_2"])

        if len(title_1) > 1.7 * len(title_2):
            language_service = colrev.env.language_service.LanguageService()
            half_length = len(title_1) // 2
            lang_first_half = language_service.compute_language(
                text=title_1[:half_length]
            )
            if lang_first_half == "eng":
                title_1 = title_1[:half_length]
            else:
                lang_second_half = language_service.compute_language(
                    text=title_1[half_length:]
                )
                if lang_second_half == "eng":
                    title_1 = title_2[half_length:]
        if len(title_2) > 1.7 * len(title_1):
            language_service = colrev.env.language_service.LanguageService()
            half_length = len(title_2) // 2
            lang_first_half = language_service.compute_language(
                text=title_2[:half_length]
            )
            if lang_first_half == "eng":
                title_2 = title_2[:half_length]
            else:
                lang_second_half = language_service.compute_language(
                    text=title_2[half_length:]
                )
                if lang_second_half == "eng":
                    title_2 = title_2[half_length:]

        # Similarity for mismatching numbers (part 1 vs 2) should be 0
        title_1_digits = re.findall(r"(?<!\[)\d+", title_1)
        title_2_digits = re.findall(r"(?<!\[)\d+", title_2)
        if title_1_digits != title_2_digits:
            return 0
        title_1_parts = re.findall(r"part [a-z]", title_1)
        title_2_parts = re.findall(r"part [a-z]", title_2)
        if title_1_parts != title_2_parts:
            return 0

        effect_1 = re.findall(r"effect[s]? of (\w+)", title_1)
        effect_2 = re.findall(r"effect[s]? of (\w+)", title_2)
        if effect_1 != effect_2:
            return 0

        treatment_1 = re.findall(r"treatment of (\w+)", title_1)
        treatment_2 = re.findall(r"treatment of (\w+)", title_2)
        if treatment_1 != treatment_2:
            return 0

        # Remove common stopwords from title_1 and title_2
        stopwords = ["the", "a", "an", "in", "on", "at", "and", "or", "of"]
        title_1 = " ".join(word for word in title_1.split() if word not in stopwords)
        title_2 = " ".join(word for word in title_2.split() if word not in stopwords)

        # Remove chemical formulae
        title_1 = re.sub(r"\[[a-z0-9]{1,5}\]", "", title_1)
        title_2 = re.sub(r"\[[a-z0-9]{1,5}\]", "", title_2)

        # Insert a space between digits that come directly after a string
        title_1 = re.sub(r"([A-Za-z])(\d)", r"\1 \2", title_1)
        title_2 = re.sub(r"([A-Za-z])(\d)", r"\1 \2", title_2)

        title_diff = fuzz.token_sort_ratio(title_1, title_2) / 100

        return title_diff
    return 0


def calculate_year_similarity(row: pd.Series) -> float:
    if "year_1" in row and "year_2" in row:
        try:
            year_1 = int(row["year_1"])
            year_2 = int(row["year_2"])
        except ValueError:
            return 0
        year_diff = abs(year_1 - year_2)
        if year_diff == 0:
            return 1.0
        elif year_diff == 1:
            return 0.95
        elif year_diff == 2:
            return 0.8
    return 0


def calculate_number_similarity(row: pd.Series) -> float:
    if "number_1" in row and "number_2" in row:
        number_1 = int(row["number_1"]) if row["number_1"].isdigit() else 0
        number_2 = int(row["number_2"]) if row["number_2"].isdigit() else 0
        if number_1 > 12 and number_2 > 12:
            number_diff = abs(number_1 - number_2)
            if number_diff == 0:
                return 1.0
            elif number_diff <= 2:
                return 0.95
            else:
                return 0.0
        else:
            # Fields.NUMBER,  # some journals have numbers like 3/4 (which can be abbreviated)
            return (
                fuzz.token_sort_ratio(str(row["number_1"]), str(row["number_2"])) / 100
            )

    return 0


J_TRANSLATIONS = {"nati medi j chin": "zhon yi xue za zhi"}


def calculate_container_similarity(row: pd.Series) -> float:
    sim_field = Fields.CONTAINER_TITLE
    ct_1 = row[f"{sim_field}_1"]
    ct_2 = row[f"{sim_field}_2"]
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


def calculate_title_partial_ratio(row: pd.Series) -> float:
    if row["title_1"] != "" and row["title_2"] != "":
        return fuzz.partial_ratio(str(row["title_1"]), str(row["title_2"])) / 100
    else:
        return 0
