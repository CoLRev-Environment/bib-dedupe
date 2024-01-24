#! /usr/bin/env python
"""Preparation of author field"""
import re
import typing
import unicodedata
from typing import List

import numpy as np

# Note: for re.sub, "van der" must be checked before "van"
NAME_PREFIXES_LOWER = [
    "van der",
    "van",
    "von der",
    "von",
    "vom",
    "le",
    "den",
    "der",
    "ter",
    "de",
    "da",
    "di",
]


def get_author_format_case(authors: typing.List[str], original_string: str) -> str:
    if authors == [""]:
        return "empty"

    if any(
        keyword in original_string.lower() for keyword in ["group", "agency", "council"]
    ):
        return "organization"

    if (" and " in original_string and ", " in original_string) or (
        " and " not in original_string
        and ", " in original_string
        and len(original_string) < 50
    ):
        return "proper_format"

    if len(authors) < 4 and not any("," in a for a in authors):
        return "single_author_missing_comma"

    if " and " not in authors and "," not in authors and len(original_string) > 5:
        if (
            sum(
                1
                for author in authors
                if author.isupper() and len(re.sub(r"[ .-]", "", author)) < 3
            )
            / len(authors)
            >= 0.4
        ):
            return "abbreviated_initials"

        if (
            sum(1 for match in re.findall(r"[A-Z][a-z\.]+[A-Z][a-z]+", original_string))
            / len(authors)
            >= 0.1
        ):
            if " " in original_string:
                return "missing_spaces_between_words"
            else:
                return "no_spaces_at_al"

    return "special_case"


def get_authors_split(authors: str) -> list:
    # single author
    if len(authors) < 15:
        if " " not in authors and re.search(r"[a-z]{3}[A-Z]", authors):
            return re.split(r"(?<=[a-z])(?=[A-Z])", authors)

        if authors.count(" ") <= 2:
            return authors.split(" ")

    authors_list = re.split(r"(?=[A-Z])", authors)
    for i in range(len(authors_list) - 1):
        if (
            authors_list[i].endswith("-")
            or authors_list[i] in ["Mc", "Mac"]
            or (
                len(authors_list[i]) == 1
                and authors_list[i].isupper()
                and len(authors_list[i + 1]) == 1
                and authors_list[i + 1].isupper()
            )
        ):
            authors_list[i + 1] = authors_list[i] + authors_list[i + 1]
            authors_list[i] = ""
    return [author.rstrip() for author in authors_list if author != ""]


def remove_accents(*, input_str: str) -> str:
    """Replace the accents in a string"""

    def rmdiacritics(char: str) -> str:
        """
        Return the base character of char, by "removing" any
        diacritics like accents or curls and strokes and the like.
        """
        try:
            desc = unicodedata.name(char)
            cutoff = desc.find(" WITH ")
            if cutoff != -1:
                desc = desc[:cutoff]
                char = unicodedata.lookup(desc)
        except (KeyError, ValueError):
            pass  # removing "WITH ..." produced an invalid name
        return char

    try:
        nfkd_form = unicodedata.normalize("NFKD", input_str)
        wo_ac_list = [
            rmdiacritics(c) for c in nfkd_form if not unicodedata.combining(c)
        ]
        wo_ac = "".join(wo_ac_list)
    except ValueError:
        wo_ac = input_str
    return wo_ac


def __prep_author_abbreviated_initials(authors_list: typing.List[str]) -> str:
    temp_authors_list: typing.List[str] = []
    next_author: typing.List[str] = []
    for author_fragment in authors_list:
        if re.match(r"[A-Z][a-z]+", author_fragment):
            temp_authors_list.append(" ".join(next_author))
            next_author = [author_fragment]
        else:
            next_author.append(author_fragment)
    temp_authors_list.append(" ".join(next_author))
    temp_authors_list = [author for author in temp_authors_list if author != ""]

    for i in range(len(temp_authors_list)):
        words = temp_authors_list[i].split()
        for j in range(len(words) - 1, -1, -1):
            if words[j].isupper() and not words[j - 1].isupper():
                words[j - 1] = words[j - 1] + ","
                break
        temp_authors_list[i] = " ".join(words)

    for i in range(len(temp_authors_list)):
        if i == len(temp_authors_list) - 1:
            temp_authors_list[i] = temp_authors_list[i]
        elif ", " in temp_authors_list[i]:
            temp_authors_list[i] = temp_authors_list[i] + " and "
        else:
            temp_authors_list[i] = temp_authors_list[i] + " "

    authors_str = "".join(temp_authors_list)
    return authors_str


def __prep_author_no_spaces_at_al(authors_list: List[str]) -> str:
    authors_str = ""
    for element in authors_list:
        if re.match(r"^[A-Z][a-z]+", element):
            authors_str += element + " "
        else:
            authors_str += ", " + element + " and "
    authors_str = authors_str.rstrip(" and ")
    return authors_str


def __prep_author_missing_spaces_between_words(original_string: str) -> str:
    new_authors = re.sub(
        r"([A-Z][a-z.]+)([A-Z])", r"\1 SPLIT\2", original_string
    ).split("SPLIT")
    for i, element in enumerate(new_authors):
        words = [
            w.replace(".", "").rstrip()
            for w in element.split()
            if w.lower() not in NAME_PREFIXES_LOWER
        ]
        if len(words) > 1:
            middle_index = len(words) // 2
            words.insert(middle_index, ",")
            new_authors[i] = " ".join(words)
    authors_str = " and ".join(new_authors)
    return authors_str


def preprocess_author(authors: str, *, debug: bool) -> str:
    authors = str(authors)
    if authors.lower() in ["nan", "anonymous"]:
        return ""

    # Many databases do not handle accents properly...
    authors = (
        remove_accents(input_str=authors)
        .replace("ue", "u")
        .replace("oe", "o")
        .replace("ae", "a")
    )

    authors = re.sub(r"\d", "", authors)

    if ";" in authors:
        authors = authors.replace(";", " and ")

    # Capitalize von/van/... and add "-" to connect last-names
    authors = re.sub(
        r"([A-Z])(" + "|".join(NAME_PREFIXES_LOWER) + r") (\w+)",
        lambda match: match.group(1)
        + match.group(2).title().replace(" ", "-")
        + "-"
        + match.group(3),
        authors,
    )
    authors = re.sub(
        r"(^| |\.|-)(" + "|".join(NAME_PREFIXES_LOWER) + r") (\w+)",
        lambda match: match.group(1)
        + match.group(2).title().replace(" ", "-")
        + "-"
        + match.group(3),
        authors,
        flags=re.IGNORECASE,
    )

    original_string = authors

    authors_list = get_authors_split(authors)

    format_case = get_author_format_case(authors_list, original_string)

    # TODO : handle debug / verbose_print
    if debug:
        print(original_string)
        print(f"format_case: {format_case}")
        print(f"authors_list: {authors_list}")

    if format_case == "proper_format":
        authors_str = authors

    elif format_case == "organization":
        authors_str = authors

    elif format_case == "empty":
        authors_str = ""

    elif format_case == "single_author_missing_comma":
        if authors_list[0].isupper():
            authors_list[0] = authors_list[0].title()

        authors_str = authors_list[0] + ", " + " ".join(authors_list[1:])

    # Broadley K.Burton A. C.Avgar T.Boutin S.
    elif format_case == "abbreviated_initials":
        authors_str = __prep_author_abbreviated_initials(authors_list)

    # PayenJ.-L.IzopetJ.Galindo-MigeotV.Lauwers-Cances
    elif format_case == "no_spaces_at_al":
        authors_str = __prep_author_no_spaces_at_al(authors_list)

    # Vernia FilippoDi Ruscio MirkoStefanelli GianpieroViscido AngeloFrieri GiuseppeLatella Giovanni
    elif format_case == "missing_spaces_between_words":
        authors_str = __prep_author_missing_spaces_between_words(original_string)

    else:
        # For debugging:
        # print(f"{format_case}: {original_string}")
        authors_str = " and ".join(authors_list)

    authors_str = authors_str.replace(" ,", ",")
    authors_str = re.sub(r"[^A-Za-z0-9, ]+", "", authors_str)
    return authors_str.lower()


def prep_authors(authors_array: np.array, *, debug: bool = False) -> np.array:
    return np.array(
        [preprocess_author(author, debug=debug) for author in authors_array]
    )


def select_authors(authors_array: np.array) -> np.array:
    def select_author(authors: str) -> str:
        """Select first author"""

        authors_list = authors.split(" and ")
        authors_str = " ".join(
            [
                re.sub(
                    r"(^| )(" + "|".join(NAME_PREFIXES_LOWER) + r") ",
                    lambda match: match.group(1) + match.group(2).replace(" ", "-") + "-",  # type: ignore
                    author.split(",")[0],
                    flags=re.IGNORECASE,
                ).replace(" ", "")
                for author in authors_list
            ][:8]
        )
        authors_str = authors_str.replace("anonymous", "").replace("jr", "")
        authors_str = re.sub(r"[^A-Za-z0-9, ]+", "", authors_str)
        return authors_str

    return np.array([select_author(author) for author in authors_array])
