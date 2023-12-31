#! /usr/bin/env python
"""Preparation for dedupe"""
import concurrent.futures
import html
import os
import re
import time
import typing
import unicodedata
import urllib.parse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from number_parser import parse

from bib_dedupe.constants.entrytypes import ARTICLE
from bib_dedupe.constants.entrytypes import BOOK
from bib_dedupe.constants.entrytypes import INBOOK
from bib_dedupe.constants.entrytypes import INPROCEEDINGS
from bib_dedupe.constants.entrytypes import PROCEEDINGS
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import BOOKTITLE
from bib_dedupe.constants.fields import CONTAINER_TITLE
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import ENTRYTYPE
from bib_dedupe.constants.fields import ID
from bib_dedupe.constants.fields import ISBN
from bib_dedupe.constants.fields import JOURNAL
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import SEARCH_SET
from bib_dedupe.constants.fields import SERIES
from bib_dedupe.constants.fields import STATUS
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import URL
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR

current_dir = Path(__file__).parent
journal_variants_path = current_dir / "journal_variants.csv"
journal_variants = pd.read_csv(journal_variants_path)
JOURNAL_TRANSLATIONS_DICT = dict(
    dict(zip(journal_variants["title_variant"], journal_variants["journal"]))
)
JOURNAL_TRANSLATIONS_DICT = {
    k.lower(): v.lower() for k, v in JOURNAL_TRANSLATIONS_DICT.items()
}

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


def set_container_title(records_df: pd.DataFrame) -> None:
    # Set container title
    records_df.loc[records_df[ENTRYTYPE] == ARTICLE, CONTAINER_TITLE] = records_df[
        JOURNAL
    ]
    records_df.loc[
        records_df[ENTRYTYPE].isin([INPROCEEDINGS, PROCEEDINGS, INBOOK]),
        CONTAINER_TITLE,
    ] = records_df[BOOKTITLE]
    records_df.loc[records_df[ENTRYTYPE] == BOOK, CONTAINER_TITLE] = records_df[TITLE]
    records_df[CONTAINER_TITLE].fillna("", inplace=True)


def get_container_title_short(ct_array: np.array) -> np.array:
    return np.array(
        [
            "".join(item[0] for item in ct.split() if item.isalpha())
            if ct != "nan"
            else ""
            for ct in ct_array
        ]
    )


def get_author_format_case(authors: typing.List[str], original_string: str) -> str:
    # TODO : non-latin, empty (after replacing special characters)
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

    authors_list = re.split(r"(?=[A-Z])", authors)  # .replace(".", ""))
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


def prep_authors(authors_array: np.array, *, debug: bool = False) -> np.array:
    def preprocess_author(authors: str, *, debug: bool) -> str:
        authors = str(authors)

        if authors in ["Anonymous"]:
            return ""

        # Many databases do not handle accents properly...
        authors = (
            remove_accents(input_str=authors)
            .replace("ue", "u")
            .replace("oe", "o")
            .replace("ae", "a")
        )

        authors = re.sub(r"\d", "", authors)
        if authors.lower() in ["nan", "anonymous"]:
            return ""

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
            temp_authors_list = []
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

        # PayenJ.-L.IzopetJ.Galindo-MigeotV.Lauwers-Cances
        elif format_case == "no_spaces_at_al":
            authors_str = ""
            for element in authors_list:
                if re.match(r"^[A-Z][a-z]+", element):
                    authors_str += element + " "
                else:
                    authors_str += ", " + element + " and "
            authors_str = authors_str.rstrip(" and ")

        # Vernia FilippoDi Ruscio MirkoStefanelli GianpieroViscido AngeloFrieri GiuseppeLatella Giovanni
        elif format_case == "missing_spaces_between_words":
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

        else:
            # For debugging:
            # print(f"{format_case}: {original_string}")
            authors_str = " and ".join(authors_list)

        authors_str = authors_str.replace(" ,", ",")
        authors_str = authors_str.replace("anonymous", "").replace("jr", "")
        authors_str = re.sub(r"[^A-Za-z0-9, ]+", "", authors_str)
        return authors_str.lower()

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


def remove_erratum_suffix(title: str) -> str:
    erratum_phrases = ["erratum appears in ", "erratum in "]
    for phrase in erratum_phrases:
        if phrase in title.lower():
            title = title[: title.lower().rfind(phrase) - 2]

    title = re.sub(r" review \d+ refs$", "", title)

    return title


TITLE_STOPWORDS = [
    "a",
    "an",
    "the",
    "in",
    "of",
    "on",
    "for",
    "from",
    "does",
    "do",
    "and",
    "are",
    "on",
    "with",
    "to",
    "or",
    "as",
    "by",
    "their",
    "the",
]


# flake8: noqa: E501
# pylint: disable=line-too-long
def prep_title(title_array: np.array) -> np.array:
    # Remove language and contents after if "Russian" or "Chinese" followed by a newline
    title_array = np.array(
        [
            re.sub(
                r"\. (Russian|Chinese|Spanish|Czech|Italian|Polish|Dutch|Ukrainian|German|French|Japanese|Slovak|Hungarian|Portuguese English|Turkish|Norwegian|Portuguese)(\r?\n)?.*$",
                "",
                title,
                flags=re.IGNORECASE,
            )
            if ". " in title
            else title
            for title in title_array
        ]
    )

    title_array = np.array(
        [
            title.replace("-like", "like")
            .replace("co-", "co")
            .replace("post-", "post")
            .replace("three-dimensional", "threedimensional")
            .replace("+", " plus ")
            for title in title_array
        ]
    )

    # Replace 'withdrawn' at the beginning and '(review') at the end (case insensitive)
    title_array = np.array(
        [
            re.sub(
                r"^(withdrawn[.:] )|^(proceedings: )|^(reprint)|( \(review\))$|( \(vol \d+.*\))",
                "",
                title,
                flags=re.IGNORECASE,
            )
            for title in title_array
        ]
    )

    # Replace roman numbers (title similarity is sensitive to numbers)
    title_array = np.array(
        [
            re.sub(
                r"\biv\b",
                " 4 ",
                re.sub(
                    r"\biii\b",
                    " 3 ",
                    re.sub(
                        r"\bii\b",
                        " 2 ",
                        re.sub(r"\bi\b", " 1 ", title, flags=re.IGNORECASE),
                        flags=re.IGNORECASE,
                    ),
                    flags=re.IGNORECASE,
                ),
                flags=re.IGNORECASE,
            )
            for title in title_array
        ]
    )

    # Remove html tags
    title_array = np.array([re.sub(r"<.*?>", " ", title) for title in title_array])
    # Replace html special entities
    title_array = np.array([html.unescape(title) for title in title_array])

    # Remove language tags added by some databases (at the end)
    title_array = np.array(
        [re.sub(r"\. \[[A-Z][a-z]*\]$", "", title) for title in title_array]
    )

    # Remove trailing "1" if it is not preceded by "part"
    title_array = np.array(
        [
            re.sub(r"1$", "", title) if "part" not in title[-10:].lower() else title
            for title in title_array
        ]
    )
    # Remove erratum suffix
    # https://www.nlm.nih.gov/bsd/policy/errata.html
    title_array = np.array([remove_erratum_suffix(title) for title in title_array])

    # Replace words in parentheses at the end
    title_array = np.array(
        [re.sub(r"\s*\([^)]*\)\s*$", "", value) for value in title_array]
    )

    # Remove '[Review] [33 refs]' and ' [abstract no: 134]' ignoring case
    title_array = np.array(
        [
            re.sub(
                r"\[Review\] \[\d+ refs\]| \[abstract no: \d+\]",
                "",
                title,
                flags=re.IGNORECASE,
            )
            for title in title_array
        ]
    )

    # Replace brackets (often used in formulae)
    title_array = np.array(
        [re.sub(r"([A-Za-z])\(([0-9]*)\)", r"\1\2", title) for title in title_array]
    )

    # Replace special characters
    title_array = np.array(
        [re.sub(r"[^A-Za-z0-9,\[\]]+", " ", title.lower()) for title in title_array]
    )

    # Remove common stopwords
    title_array = np.array(
        [
            " ".join(word for word in title.split() if word not in TITLE_STOPWORDS)
            for title in title_array
        ]
    )

    # Apply parse function to replace numbers
    title_array = np.array([parse(title) for title in title_array])

    # Replace spaces between digits
    title_array = np.array(
        [
            re.sub(r"(\d) (\d)", r"\1\2", title).rstrip(" ].").lstrip("[ ")
            for title in title_array
        ]
    )

    # Replace multiple spaces with a single space
    title_array = np.array(
        [re.sub(r"\s+", " ", title).rstrip().lstrip() for title in title_array]
    )
    return title_array


JOURNAL_STOPWORDS = [
    "of",
    "for",
    "the",
    "and",
    "de",
    "d",
    "et",
    "in",
    "i",
    "&",
    "to",
    "on",
    "die",
    "part",
    "annual",
    "und",
    "für",
    "fur",
    "der",
]

JOURNAL_ABBREV = {
    "amer": "am",
    "soci": "soc",
    "expe": "exp",
    "mole": "mol",
    "scie": "sci",
    "brit": "br",
    "bole": "bol",
    "inte": "int",
    "arqu": "arq",
    "polo": "pol",
    "vete": "vet",
    "desi": "des",
    "mede": "med",
    "tera": "ter",
    "huma": "hum",
    "revu": "rev",
    "natu": "nat",
    "move": "mov",
    "cana": "can",
    "euro": "eur",
    "adva": "adv",
    "medi": "med",
    "anna": "ann",
    "revi": "rev",
    "rese": "res",
    "bmj br med j": "bmj",
    "br med j": "bmj",
}


def prep_container_title(ct_array: np.array) -> np.array:
    def get_abbrev(ct: str) -> str:
        # Use abbreviated versions
        # journal of infection and chemotherapy
        # j infect chemother
        ct = str(ct)

        # Replace trailing "the" (ignore case)
        ct = re.sub(r"\sthe\s*$", "", ct, flags=re.IGNORECASE)

        ct = (
            ct.lower()
            .replace(" neuro ", " neuro")
            .replace("-", "")
            .replace("journal", "j")
        )

        if "plos one" not in ct:
            ct = parse(ct)  # replace numbers

        ct = " ".join(word[:4] for word in ct.split() if word not in JOURNAL_STOPWORDS)
        # use the same abbreviations (container_title is used for blocking)
        for original, replacement in JOURNAL_ABBREV.items():
            ct = ct.replace(original, replacement)

        # Replace trailing "supp" or leading "proc"
        ct = re.sub(r"^proc\s|\ssupp$", "", ct)
        return ct

    ct_array = np.array(
        [
            re.sub("proceedings of the", "", value.split(".")[0], flags=re.IGNORECASE)
            if "date of publication" in value.lower()
            or "conference start" in value.lower()
            else re.sub("proceedings of the", "", value, flags=re.IGNORECASE)
            for value in ct_array
        ]
    )

    def replace_journal_names(value: str) -> str:
        if (
            not any(char in value for char in "=.[")
            and len(value) < 70
            and "journal" in value.lower()
        ):
            return value
        else:
            for key, val in JOURNAL_TRANSLATIONS_DICT.items():
                if " " not in key:
                    continue

                if key in value.replace(".", " ").lower():
                    return val
            return value

    ct_array = np.array([replace_journal_names(value) for value in ct_array])

    ct_array = np.array(
        [
            # |(\. )
            re.split(r"(\.\d+)|(: )|( - )", value)[0]
            if re.search(r"(\.\d+)|(\. )|(: )|( - )", value)
            else value
            for value in ct_array
        ]
    )

    ct_array = np.array(
        [re.sub(r"\s*\[Electronic Resource\]$", "", value) for value in ct_array]
    )

    # If spaces were accidentally removed, restore them (looking for capital letters)
    # ct_array = np.array(
    #     [
    #         re.sub(r"(?<=\w)([A-Z])", r" \1", value)
    #         if "plos" not in value.lower()
    #         else value
    #         for value in ct_array
    #     ]
    # )
    # Note : distinguish confernces before (see digital_work)

    # Replace words in parentheses at the end
    ct_array = np.array(
        [re.sub(r"\s*\([^)]*\)\s*$|('s)", "", value) for value in ct_array]
    )

    # ct_array = np.array([value.replace(".", " ") for value in ct_array])
    ct_array = np.array(
        [re.sub(r"^the\s|^(l')|", "", value, flags=re.IGNORECASE) for value in ct_array]
    )
    ct_array = np.array([re.sub(r"[^A-Za-z ]+", " ", value) for value in ct_array])
    ct_array = np.array(
        [
            re.sub(r"^\s*(st|nd|rd|th) ", "", value, flags=re.IGNORECASE)
            for value in ct_array
        ]
    )

    return np.array([get_abbrev(ct) for ct in ct_array])


def prep_year(year_array: np.array) -> np.array:
    def process_year(value: str) -> str:
        try:
            int_value = int(float(value))

            if not 1900 < int_value < 2100:
                return ""

        except ValueError:
            return ""
        return str(int_value)

    return np.array([process_year(year) for year in year_array])


def prep_volume(volume_array: np.array) -> np.array:
    volume_array = np.array(
        [
            re.search(r"(\d+) \(.*\)", volume).group(1)  # type: ignore
            if re.search(r"(\d+) \(.*\)", volume) is not None
            # pages included: "6 51-6"
            else re.search(r"(\d+) .*", volume).group(1)  # type: ignore
            if re.search(r"(\d+) \d+-\d+", volume) is not None
            else volume
            for volume in volume_array
        ]
    )
    volume_array = np.array(
        [
            re.search(r"(\d+) suppl \d+", volume.lower()).group(1)  # type: ignore
            if re.search(r"(\d+) suppl \d+", volume.lower()) is not None
            else volume
            for volume in volume_array
        ]
    )
    volume_array = np.array(
        [
            re.sub(r"[^\d\(\)]", "", volume)
            # if len(volume) < 4 and any(char.isdigit() for char in volume)
            # else volume
            for volume in volume_array
        ]
    )

    volume_array = np.array(
        [
            re.search(r"(\d+)", volume).group(0)  # type: ignore
            if re.search(r"(\d+)", volume) is not None
            else volume.replace("(", "").replace(")", "")
            for volume in volume_array
        ]
    )
    return np.array(
        [
            "" if volume == "nan" or len(volume) > 100 else volume
            for volume in volume_array
        ]
    )


def prep_number(number_array: np.array) -> np.array:
    number_array = np.array(
        [re.sub(r"[A-Za-z.]*", "", number) for number in number_array]
    )
    number_array = np.array(
        [
            # pages included: "6 51-6"
            re.search(r"(\d+) .*", number).group(1)  # type: ignore
            if re.search(r"(\d+) \d+-\d+", number) is not None
            else number
            for number in number_array
        ]
    )

    number_array = np.array(
        [
            number.replace(" ", "").replace("(", "").replace(")", "")
            for number in number_array
        ]
    )

    return np.array(
        ["" if number in ["nan", "var.pagings"] else number for number in number_array]
    )


month_dict = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def prep_pages(pages_array: np.array) -> np.array:
    def process_page(value: str) -> str:
        if value.isalpha():
            return ""

        # Fix Excel errors (e.g., "08-11" is converted to "08-Nov")
        for month, num in month_dict.items():
            if month in value.lower():
                value = value.lower().replace(month, num)
                break

        def roman_to_int(s: str) -> int:
            rom_val = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
            int_val = 0
            for i in range(len(s)):
                if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
                    int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
                else:
                    int_val += rom_val[s[i]]
            return int_val

        # Check if the value is a roman numeral range
        roman_numeral_range = re.match(r"([IVXLCDM]+)-([IVXLCDM]+)", value, re.I)
        if roman_numeral_range:
            # Convert the roman numerals to integers
            from_page = roman_to_int(roman_numeral_range.group(1).upper())
            to_page = roman_to_int(roman_numeral_range.group(2).upper())
            return f"{from_page}-{to_page}"

        # Remove leading zeros in groups of digits
        value = re.sub(r"\b0+([0-9]+)", r"\1", value)

        value = re.sub(r"[A-Za-z. ]*", "", value)
        if re.match(r"^\d+\s*-?-\s*\d+$", value):
            from_page_str, to_page_str = re.findall(r"(\d+)", value)
            if from_page_str == to_page_str:
                return from_page_str
            if len(from_page_str) > len(to_page_str):
                return (
                    f"{from_page_str}-{from_page_str[:-len(to_page_str)]}{to_page_str}"
                )
            else:
                return f"{from_page_str}-{to_page_str}"
        if value in [
            " ",
            None,
            "nan",
            "na",
            "no pages",
            "no pagination",
            "var.pagings",
        ]:
            return ""
        # re sub everything except numbers and dashes
        return re.sub(r"[^0-9-]", "", value).lstrip("-").rstrip("-")

    return np.vectorize(process_page)(pages_array)


def prep_abstract(abstract_array: np.array) -> np.array:
    abstract_array = np.array(
        [re.sub(r"<.*?>", " ", abstract.lower()) for abstract in abstract_array]
    )

    abstract_array = np.array(
        [
            re.sub(r"^aims\s|^objectives|^background", "", abstract)
            for abstract in abstract_array
        ]
    )

    abstract_array = np.array(
        [
            abstract[: abstract.rfind(". copyright")]
            if ". copyright" in abstract[-300:]
            else abstract[: abstract.rfind("©")]
            if "©" in abstract[-200:]
            else re.sub(r"(\s*\d{4}\s*)?the authors[.?]$", "", abstract)
            if "the authors" in abstract[-100:]
            else abstract[: abstract.rfind("springer-verlag")]
            if "springer-verlag" in abstract[-100:]
            else re.sub(r"\s*\d{4}.*$", "", abstract)
            if re.search(r"\.\s*\d{4}.*$", abstract)
            else re.sub(r" \(c\) \d{4}.*\.$", "", abstract)
            if re.search(r"\. \(c\) \d{4}.*\.$", abstract)
            else re.sub(r"\.\(abstract truncated at 400 words\)$", "", abstract)
            if ".(abstract truncated at 400 words)" in abstract[-80:]
            else abstract
            for abstract in abstract_array
        ]
    )

    # Remove "abstract " at the beginning
    abstract_array = np.array(
        [re.sub(r"^abstract ", "", abstract) for abstract in abstract_array]
    )

    # Remove trailing date
    abstract_array = np.array(
        [re.sub(r"\s*\(\d{4}\)$", "", abstract) for abstract in abstract_array]
    )

    abstract_array = np.array(
        [re.sub(r"[^A-Za-z0-9 .,]", "", abstract) for abstract in abstract_array]
    )
    abstract_array = np.array(
        [re.sub(r"\s+", " ", abstract) for abstract in abstract_array]
    )
    return np.array(
        [
            "" if abstract == "nan" else abstract.lower().rstrip(" .").lstrip(" .")
            for abstract in abstract_array
        ]
    )


def prep_doi(doi_array: np.array) -> np.array:
    doi_array = np.array(
        [re.sub(r"http://dx.doi.org/", "", doi.lower()) for doi in doi_array]
    )
    doi_array = np.array([re.sub(r"-", "_", doi) for doi in doi_array])
    doi_array = np.array([re.sub(r"\[doi\]", "", doi) for doi in doi_array])
    doi_array = np.array([re.sub(r"[\r\n]+", " ; ", doi) for doi in doi_array])

    doi_array = np.array(
        [
            doi.split(";")[1].lstrip()
            if ";" in doi and doi.split(";")[1].lstrip().startswith("10.")
            else doi.split(";")[0].lstrip()
            if ";" in doi and doi.split(";")[0].lstrip().startswith("10.")
            else doi
            for doi in doi_array
        ]
    )
    doi_array = np.array(
        [doi.split("[pii];")[1] if "[pii];" in doi else doi for doi in doi_array]
    )
    doi_array = np.array([urllib.parse.unquote(doi) for doi in doi_array])
    doi_array = np.array([doi if doi.startswith("10.") else "" for doi in doi_array])

    return np.array(
        ["" if doi == "nan" else doi.replace(".", "").rstrip() for doi in doi_array]
    )


def prep_isbn(isbn_array: np.array) -> np.array:
    isbn_array = np.array([re.sub(r"[\r\n]+", ";", isbn) for isbn in isbn_array])
    isbn_array = np.array(
        [
            re.search(r"\b\d{4}-?\d{3}(\d|X)\b", isbn).group()  # type: ignore
            if re.search(r"\b\d{4}-?\d{3}(\d|X)\b", isbn)
            else isbn
            for isbn in isbn_array
        ]
    )
    return np.array(["" if isbn == "nan" else isbn.lower() for isbn in isbn_array])


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
    ISBN: prep_isbn,
}


def process_df_split(split_df: pd.DataFrame) -> pd.DataFrame:
    split_df.replace(
        to_replace={
            "UNKNOWN": "",
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

    # TODO : integrate into prep_author if the author_full (minimally processed) is effective
    split_df[AUTHOR] = select_authors(split_df[AUTHOR].values)

    split_df.loc[split_df[PAGES] == split_df[YEAR], PAGES] = ""

    if BOOKTITLE in split_df.columns:
        split_df = split_df.drop(columns=[BOOKTITLE])
    if JOURNAL in split_df.columns:
        split_df = split_df.drop(columns=[JOURNAL])

    split_df = split_df.fillna("")

    return split_df


def prep(records_df: pd.DataFrame, *, cpu: int = -1) -> pd.DataFrame:
    """Prepare records for dedupe"""

    print(f"Loaded {records_df.shape[0]:,} records")

    print("Prep started at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    start_time = time.time()

    if 0 == records_df.shape[0]:
        return {}

    assert all(f in records_df.columns for f in [ENTRYTYPE, TITLE, AUTHOR, YEAR])

    if ID not in records_df.columns:
        records_df[ID] = range(1, len(records_df) + 1)

    if STATUS not in records_df:
        records_df[STATUS] = "md_processed"
        print("Warning: setting missing status")

    records_df = records_df[
        ~(
            records_df[STATUS].isin(
                [
                    "md_imported",
                    "md_needs_manual_preparation",
                ]
            )
        )
    ]

    records_df[TITLE] = records_df[TITLE].replace(["#NAME?", "UNKNOWN", ""], np.nan)
    if records_df[TITLE].isnull().any():
        print(
            "Warning: Some records have empty title field. These records will be dropped."
        )
        records_df = records_df.dropna(subset=[TITLE])

    # if columns are of type float, we need to avoid casting "3.0" to "30"
    for col in records_df.columns:
        if records_df[col].dtype == float:
            records_df[col] = records_df[col].apply(
                lambda x: str(int(x)) if x == x else ""
            )

    optional_fields = [
        JOURNAL,
        BOOKTITLE,
        SERIES,
        VOLUME,
        NUMBER,
        PAGES,
        ABSTRACT,
        ISBN,
        DOI,
        SEARCH_SET,
    ]
    for optional_field in optional_fields:
        if optional_field not in records_df:
            records_df[optional_field] = ""

    records_df.drop(
        labels=list(
            records_df.columns.difference(
                [
                    ID,
                    ENTRYTYPE,
                    AUTHOR,
                    TITLE,
                    YEAR,
                    JOURNAL,
                    CONTAINER_TITLE,
                    BOOKTITLE,
                    VOLUME,
                    NUMBER,
                    PAGES,
                    STATUS,
                    ABSTRACT,
                    URL,
                    ISBN,
                    DOI,
                    SEARCH_SET,
                ]
            )
        ),
        axis=1,
        inplace=True,
    )

    records_df[
        [
            STATUS,
            AUTHOR,
            TITLE,
            JOURNAL,
            YEAR,
            VOLUME,
            NUMBER,
            PAGES,
            ABSTRACT,
            DOI,
            ISBN,
            SEARCH_SET,
        ]
    ] = records_df[
        [
            STATUS,
            AUTHOR,
            TITLE,
            JOURNAL,
            YEAR,
            VOLUME,
            NUMBER,
            PAGES,
            ABSTRACT,
            DOI,
            ISBN,
            SEARCH_SET,
        ]
    ].astype(
        str
    )

    # TODO : extract
    if cpu == -1:
        # -2
        cpu = os.cpu_count() if os.cpu_count() else 1  # type: ignore

    if records_df.shape[0] < 100:
        # don't split (otherwise, a vectorizeon size 0 inputs is raised)
        cpu = 1

    df_split = np.array_split(records_df, cpu)

    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu) as executor:
        results = executor.map(process_df_split, df_split)

    records_df = pd.concat(list(results))

    records_df = records_df.assign(
        author_first=records_df[AUTHOR].str.split().str[0],
        title_short=records_df[TITLE].apply(lambda x: " ".join(x.split()[:10])),
        container_title_short=get_container_title_short(
            records_df[CONTAINER_TITLE].values
        ),
    )

    records_df[ID] = records_df[ID].astype(str)
    records_df.loc[records_df[SEARCH_SET] == "nan", SEARCH_SET] = ""
    records_df.loc[records_df[TITLE] == "nan", TITLE] = ""
    records_df.loc[records_df[ABSTRACT] == "nan", ABSTRACT] = ""
    records_df.loc[records_df[YEAR] == "nan", YEAR] = ""
    records_df.loc[records_df[CONTAINER_TITLE] == "nan", CONTAINER_TITLE] = ""

    end_time = time.time()
    print(f"Prep completed after: {end_time - start_time:.2f} seconds")

    return records_df
