#! /usr/bin/env python
"""Preparation of misaligned schemata"""
from __future__ import annotations

import re

import pandas as pd


# --- precompiled regex --------------------------------------------------------

RE_NO_PAGINATION = re.compile(r"\(\s*no\s+pagination\s*\)", flags=re.IGNORECASE)

# Months / month-like tokens (incl. abbreviations)
MONTHS = (
    "jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|"
    "aug|august|sep|sept|september|oct|october|nov|november|dec|december"
)
RE_MONTHISH = re.compile(
    rf"(?ix)\b(?:{MONTHS})\b"  # any month token
    rf"|^\s*\d{{1,2}}\s+(?:{MONTHS})\s*$"  # e.g., "3 aug"
)

RE_ONLY_PARENS = re.compile(r"^\(\s*(?P<tok>[^)]+?)\s*\)$")
RE_PAGES_PARENS = RE_ONLY_PARENS  # same structure
RE_YEAR_IN_VOL = re.compile(r"^(?P<year>\d{4})(?:\s*\(\s*(?P<iss>[^)]+?)\s*\))?$")
RE_VOL_ISSUE = re.compile(r"^(?P<vol>[A-Za-z0-9]+)\s*\(\s*(?P<iss>.+)\s*\)$")

RE_MULTI_WS = re.compile(r"\s+")

# supplement normalization regex
RE_SUPPL = re.compile(r"(?i)\bSUPPL\.?\s*(\d+)\b")
RE_SUPPLEMENT = re.compile(r"(?i)\bSupplement\s*([0-9]+)\b")
RE_SUPPLEMENT_JOINED = re.compile(r"(?i)\bSupplement([0-9]+)\b")
RE_SPEC_ISS = re.compile(r"(?i)\bSPEC\.?\s*ISS\.?\s*(\d+)\b")


def _normalize_supplement_scalar(token: str) -> str:
    """Normalize common supplement formats lightly (keep informative text)."""
    if not token:
        return ""
    t = RE_MULTI_WS.sub(" ", token.strip())
    t = RE_SUPPL.sub(r"SUPPL.\1", t)
    t = RE_SUPPLEMENT.sub(r"Supplement \1", t)
    t = RE_SUPPLEMENT_JOINED.sub(r"Supplement \1", t)
    t = RE_SPEC_ISS.sub(r"Spec.Iss \1", t)
    return t.strip()


def fix_schema_misalignments(split_df: pd.DataFrame) -> None:
    """
    Fix common schema misalignments where volume/number/pages contain mixed content.

    Rules:
    - '(no pagination)' is removed wherever it appears, but pages MUST NOT be set.
    - Month-like tokens are removed/ignored.
    - Function mutates split_df in-place and returns None.
    """
    if split_df.empty:
        return

    for col in ("volume", "number", "pages", "year"):
        if col not in split_df.columns:
            split_df[col] = ""

    # Normalize to trimmed strings once
    for col in ("volume", "number", "pages", "year"):
        split_df[col] = split_df[col].fillna("").astype(str).str.strip()

    # 1) strip '(no pagination)' everywhere, but only if it exists
    for col in ("volume", "number", "pages"):
        s = split_df[col]
        if s.str.contains("no pagination", case=False, na=False).any():
            s = s.str.replace(RE_NO_PAGINATION, "", regex=True)
            s = s.str.replace(RE_MULTI_WS, " ", regex=True).str.strip()
            split_df[col] = s

    # convenience views (these are Series views; re-read when you mutate a column)
    pag = split_df["pages"]
    vol = split_df["volume"]

    # Helper: vectorized monthish check
    def monthish_mask(series: pd.Series) -> pd.Series:
        # normalize punctuation to spaces before matching (vectorized)
        cleaned = series.str.lower().str.replace(r"[^a-z0-9 ]", " ", regex=True)
        cleaned = cleaned.str.replace(RE_MULTI_WS, " ", regex=True).str.strip()
        return cleaned.str.contains(RE_MONTHISH, regex=True, na=False)

    # 2) pages like "(1)" -> move into number if empty, clear pages
    if pag.str.contains(r"^\(", na=False).any():
        extracted = pag.str.extract(RE_PAGES_PARENS)
        mask_paren = extracted["tok"].notna()
        if mask_paren.any():
            tok = extracted["tok"].fillna("").str.strip()
            set_mask = mask_paren & (split_df["number"] == "") & (~monthish_mask(tok))
            if set_mask.any():
                split_df.loc[set_mask, "number"] = tok[set_mask].map(
                    _normalize_supplement_scalar
                )
            split_df.loc[mask_paren, "pages"] = ""

    # refresh
    vol = split_df["volume"]

    # 3) volume-only "(4)" -> set number if empty; clear volume (always)
    if vol.str.contains(r"^\(", na=False).any():
        extracted = vol.str.extract(RE_ONLY_PARENS)
        mask_only = extracted["tok"].notna()
        if mask_only.any():
            tok = extracted["tok"].fillna("").str.strip()
            set_mask = mask_only & (split_df["number"] == "") & (~monthish_mask(tok))
            if set_mask.any():
                split_df.loc[set_mask, "number"] = tok[set_mask].map(
                    _normalize_supplement_scalar
                )
            split_df.loc[mask_only, "volume"] = ""

    # refresh
    vol = split_df["volume"]

    # 4) year stored where volume should be: "2017 (10)" or "2017"
    if vol.str.contains(r"^\d{4}", na=False, regex=True).any():
        extracted = vol.str.extract(RE_YEAR_IN_VOL)
        mask_year = extracted["year"].notna()
        if mask_year.any():
            yval = extracted["year"].fillna("").str.strip()
            iss = extracted["iss"].fillna("").str.strip()

            set_year = mask_year & (split_df["year"] == "") & (yval != "")
            if set_year.any():
                split_df.loc[set_year, "year"] = yval[set_year]

            set_num = (
                mask_year
                & (split_df["number"] == "")
                & (iss != "")
                & (~monthish_mask(iss))
            )
            if set_num.any():
                split_df.loc[set_num, "number"] = iss[set_num].map(
                    _normalize_supplement_scalar
                )

            split_df.loc[mask_year, "volume"] = ""

    # refresh
    vol = split_df["volume"]

    # 5) main pattern: "V (X)" including nested parentheses in X
    # Only run if we see "(" somewhere
    if vol.str.contains(r"\(", na=False).any():
        extracted = vol.str.extract(RE_VOL_ISSUE)
        mask_vi = extracted["vol"].notna()
        if mask_vi.any():
            v = extracted["vol"].fillna("").str.strip()
            iss = extracted["iss"].fillna("").str.strip()

            split_df.loc[mask_vi, "volume"] = v[mask_vi]

            set_num = (
                mask_vi
                & (split_df["number"] == "")
                & (iss != "")
                & (~monthish_mask(iss))
            )
            if set_num.any():
                split_df.loc[set_num, "number"] = iss[set_num].map(
                    _normalize_supplement_scalar
                )

    # 6) final cleanup: collapse whitespace again (cheap)
    for col in ("volume", "number", "pages"):
        split_df[col] = (
            split_df[col]
            .fillna("")
            .astype(str)
            .str.replace(RE_MULTI_WS, " ", regex=True)
            .str.strip()
        )

    # 7) drop literal "no pagination"
    for col in ("volume", "number", "pages"):
        mask = split_df[col].str.lower().eq("no pagination")
        if mask.any():
            split_df.loc[mask, col] = ""
