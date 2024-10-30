#! /usr/bin/env python
"""Preparation of container_title field"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
from number_parser import parse

from bib_dedupe.constants.entrytypes import ARTICLE
from bib_dedupe.constants.entrytypes import BOOK
from bib_dedupe.constants.entrytypes import INBOOK
from bib_dedupe.constants.entrytypes import INPROCEEDINGS
from bib_dedupe.constants.entrytypes import PROCEEDINGS
from bib_dedupe.constants.fields import BOOKTITLE
from bib_dedupe.constants.fields import CONTAINER_TITLE
from bib_dedupe.constants.fields import ENTRYTYPE
from bib_dedupe.constants.fields import JOURNAL
from bib_dedupe.constants.fields import TITLE

current_dir = Path(__file__).parent
journal_variants_path = current_dir / "journal_variants.csv"
journal_variants = pd.read_csv(journal_variants_path)
JOURNAL_TRANSLATIONS_DICT = dict(
    dict(zip(journal_variants["title_variant"], journal_variants["journal"]))
)
JOURNAL_TRANSLATIONS_DICT = {
    k.lower(): v.lower() for k, v in JOURNAL_TRANSLATIONS_DICT.items()
}


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
    records_df[CONTAINER_TITLE] = records_df[CONTAINER_TITLE].fillna("")


def get_container_title_short(ct_array: np.array) -> np.array:
    return np.array(
        [
            "".join(item[0] for item in ct.split() if item.isalpha())
            if ct != "nan"
            else ""
            for ct in ct_array
        ]
    )


def prep_container_title(ct_array: np.array) -> np.array:
    def get_abbrev(ct: str) -> str:
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
    # Note : distinguish conferences before (see digital_work)

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
