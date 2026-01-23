#! /usr/bin/env python
"""Preparation of title field"""
from __future__ import annotations

import html
import re
from typing import Callable, Iterable, List

import numpy as np
from number_parser import parse


TITLE_STOPWORDS = {
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
    "with",
    "to",
    "or",
    "as",
    "by",
    "their",
}

# --- Precompiled regex patterns (faster + cleaner) ---

LANG_TRAILING_RE = re.compile(
    r"\. (Russian|Chinese|Spanish|Czech|Italian|Polish|Dutch|Ukrainian|German|French|Japanese|Slovak|Hungarian|Portuguese English|Turkish|Norwegian|Portuguese)(\r?\n)?.*$",
    flags=re.IGNORECASE,
)

BOILERPLATE_RE = re.compile(
    r"^(withdrawn[.:] )|^(proceedings: )|^(reprint)|( \(review\))$|( \(vol \d+.*\))",
    flags=re.IGNORECASE,
)

HTML_TAG_RE = re.compile(r"<.*?>")
LANG_TAG_END_RE = re.compile(r"\. \[[A-Z][a-z]*\]$")

REVIEW_ABSTRACT_RE = re.compile(
    r"\[Review\] \[\d+ refs\]| \[abstract no: \d+\]",
    flags=re.IGNORECASE,
)

PARENS_AT_END_RE = re.compile(r"\s*\([^)]*\)\s*$")
BRACKET_FORMULA_RE = re.compile(r"([A-Za-z])\(([0-9]*)\)")

NON_ALNUM_KEEP_BRACKETS_RE = re.compile(r"[^A-Za-z0-9,\[\]]+")
SPACES_RE = re.compile(r"\s+")
DIGIT_SPACE_DIGIT_RE = re.compile(r"(\d) (\d)")

ERRATUM_REFS_RE = re.compile(r" review \d+ refs$", flags=re.IGNORECASE)

AUTHORS_PERSONAL_COPY_RE = re.compile(
    r"^\s*author[’']s personal copy[\s\-\–—:;,.]*|[\s\-\–—:;,.]*author[’']s personal copy\s*$",
    flags=re.IGNORECASE,
)

ROMAN_REPLACEMENTS = [
    (re.compile(r"\biv\b", flags=re.IGNORECASE), " 4 "),
    (re.compile(r"\biii\b", flags=re.IGNORECASE), " 3 "),
    (re.compile(r"\bii\b", flags=re.IGNORECASE), " 2 "),
    (re.compile(r"\bi\b", flags=re.IGNORECASE), " 1 "),
]


# --- Small helpers ---

def remove_erratum_suffix(title: str) -> str:
    lowered = title.lower()
    for phrase in ("erratum appears in ", "erratum in "):
        if phrase in lowered:
            title = title[: lowered.rfind(phrase) - 2]
            lowered = title.lower()
    return ERRATUM_REFS_RE.sub("", title)


def remove_authors_personal_copy(title: str) -> str:
    return AUTHORS_PERSONAL_COPY_RE.sub("", title).strip()


def _strip_trailing_lang_if_has_dotspace(title: str) -> str:
    # preserve your original condition: only apply if ". " in title
    if ". " in title:
        return LANG_TRAILING_RE.sub("", title)
    return title


def _normalize_tokens(title: str) -> str:
    return (
        title.replace("-like", "like")
        .replace("co-", "co")
        .replace("post-", "post")
        .replace("three-dimensional", "threedimensional")
        .replace("+", " plus ")
    )


def _replace_roman_numerals(title: str) -> str:
    for pattern, repl in ROMAN_REPLACEMENTS:
        title = pattern.sub(repl, title)
    return title


def _remove_trailing_one_unless_part(title: str) -> str:
    if title.endswith("1") and "part" not in title[-10:].lower():
        return title[:-1]
    return title


def _remove_stopwords(title: str) -> str:
    return " ".join(w for w in title.split() if w not in TITLE_STOPWORDS)


def _final_trim(title: str) -> str:
    # join digits, trim brackets/punct, normalize spaces
    title = DIGIT_SPACE_DIGIT_RE.sub(r"\1\2", title).rstrip(" ].").lstrip("[ ")
    title = SPACES_RE.sub(" ", title).strip()
    return title

PRESENTER_INFO_ONLY_RE = re.compile(
    r"^\s*(presenter information)(\s+presenter information)*\s*$",
    flags=re.IGNORECASE,
)

def drop_known_junk_titles(title: str) -> str:
    # If the whole title is just boilerplate (often duplicated), drop it
    if PRESENTER_INFO_ONLY_RE.match(title):
        return ""
    return title


# --- Main pipeline ---

def prep_title(title_array: np.ndarray) -> np.ndarray:
    transforms: List[Callable[[str], str]] = [
        _strip_trailing_lang_if_has_dotspace,
        drop_known_junk_titles,
        remove_authors_personal_copy,
        _normalize_tokens,
        lambda t: BOILERPLATE_RE.sub("", t),
        _replace_roman_numerals,
        lambda t: HTML_TAG_RE.sub(" ", t),
        html.unescape,
        lambda t: LANG_TAG_END_RE.sub("", t),
        _remove_trailing_one_unless_part,
        remove_erratum_suffix,
        lambda t: PARENS_AT_END_RE.sub("", t),
        lambda t: REVIEW_ABSTRACT_RE.sub("", t),
        lambda t: BRACKET_FORMULA_RE.sub(r"\1\2", t),
        lambda t: NON_ALNUM_KEEP_BRACKETS_RE.sub(" ", t.lower()),
        _remove_stopwords,
        parse,
        _final_trim,
    ]

    # One pass through the pipeline per title
    def run_pipeline(title: str) -> str:
        for fn in transforms:
            title = fn(title)
        return title

    # Use fromiter to avoid repeatedly constructing arrays
    return np.fromiter((run_pipeline(t) for t in title_array), dtype=object)
