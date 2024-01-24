#! /usr/bin/env python
"""Preparation of title field"""
import html
import re

import numpy as np
from number_parser import parse


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


def remove_erratum_suffix(title: str) -> str:
    erratum_phrases = ["erratum appears in ", "erratum in "]
    for phrase in erratum_phrases:
        if phrase in title.lower():
            title = title[: title.lower().rfind(phrase) - 2]

    title = re.sub(r" review \d+ refs$", "", title)

    return title


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
