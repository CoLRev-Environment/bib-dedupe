#! /usr/bin/env python
"""Preparation of misaligned schemata"""
import re

import pandas as pd


_MONTH_TOKENS = {
    "jan",
    "january",
    "feb",
    "february",
    "mar",
    "march",
    "apr",
    "april",
    "may",
    "jun",
    "june",
    "jul",
    "july",
    "aug",
    "august",
    "sep",
    "sept",
    "september",
    "oct",
    "october",
    "nov",
    "november",
    "dec",
    "december",
}


def _strip_no_pagination(text: str) -> str:
    """Remove '(no pagination)' fragments without setting pages."""
    if not text:
        return ""
    # remove any occurrence like "(no pagination)" with flexible whitespace/case
    text = re.sub(r"\(\s*no\s+pagination\s*\)", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _is_monthish(token: str) -> bool:
    """Return True if token looks like a month/season/date label (to be ignored)."""
    if not token:
        return False
    t = token.strip().lower()
    # remove punctuation for month detection
    t_clean = re.sub(r"[^a-z0-9 ]", " ", t)
    parts = [p for p in t_clean.split() if p]
    if not parts:
        return False
    # if any part is a month token -> treat as monthish
    if any(p in _MONTH_TOKENS for p in parts):
        return True
    # patterns like "3 aug" (month abbrev without parentheses)
    if len(parts) == 2 and parts[1] in _MONTH_TOKENS and parts[0].isdigit():
        return True
    return False


def _normalize_supplement(token: str) -> str:
    """Normalize common supplement formats lightly (keep informative text)."""
    if not token:
        return ""

    t = token.strip()
    t = re.sub(r"\s+", " ", t)

    # SUPPL. 1 -> SUPPL.1 ; SUPPL.1 -> SUPPL.1
    t = re.sub(r"(?i)\bSUPPL\.?\s*(\d+)\b", r"SUPPL.\1", t)

    # "Supplement3" -> "Supplement 3"
    t = re.sub(r"(?i)\bSupplement\s*([0-9]+)\b", r"Supplement \1", t)
    t = re.sub(r"(?i)\bSupplement([0-9]+)\b", r"Supplement \1", t)

    # "SPEC.ISS 1" / "Spec.Iss 1" -> "Spec.Iss 1"
    t = re.sub(r"(?i)\bSPEC\.?\s*ISS\.?\s*(\d+)\b", r"Spec.Iss \1", t)

    return t.strip()


def fix_schema_misalignments(split_df: pd.DataFrame) -> None:
    """
    Fix common schema misalignments where volume/number/pages contain mixed content.

    Updated rules (per request):
    - '(no pagination)' is removed wherever it appears, but pages MUST NOT be set.
    - Month-like tokens (JAN, FEBRUARY 2012, '(7 JUL)', etc.) are removed/ignored.
    - "Strange large issue" values are not treated specially (left as-is if parsed).
    - Function mutates split_df in-place and returns None.
    """
    if split_df.empty:
        return

    # ensure columns exist
    for col in ("volume", "number", "pages", "year"):
        if col not in split_df.columns:
            split_df[col] = ""

    # helper to get safe string series
    def s(col: str) -> pd.Series:
        return split_df[col].fillna("").astype(str).str.strip()

    # 1) strip '(no pagination)' everywhere (volume/number/pages)
    split_df["volume"] = s("volume").map(_strip_no_pagination)
    split_df["number"] = s("number").map(_strip_no_pagination)
    split_df["pages"] = s("pages").map(_strip_no_pagination)

    num = s("number")
    pag = s("pages")
    yr = s("year")

    # 2) If pages is like "(1)" or "(4)" -> move into number if empty, clear pages
    # Also handle "(1) (no pagination)" already stripped to "(1)" above.
    m_pages_issue = pag.str.extract(r"^\(\s*(?P<iss>[^)]+?)\s*\)$")
    mask_pages_issue = m_pages_issue["iss"].notna()
    if mask_pages_issue.any():
        issue_val = m_pages_issue["iss"].fillna("").astype(str).str.strip()
        # ignore monthish issue labels
        mask_set = mask_pages_issue & (num == "") & (~issue_val.map(_is_monthish))
        split_df.loc[mask_set, "number"] = issue_val[mask_set].map(
            _normalize_supplement
        )
        split_df.loc[mask_pages_issue, "pages"] = ""  # clear pages (don't set to 1)
        # refresh
        num = s("number")
        pag = s("pages")

    # 3) Volume-only "(4)" -> issue without volume: set number if empty; clear volume
    # Also handle "(7 JUL)" monthish -> drop
    vol_now = s("volume")
    m_only_paren = vol_now.str.extract(r"^\(\s*(?P<tok>[^)]+?)\s*\)$")
    mask_only_paren = m_only_paren["tok"].notna()
    if mask_only_paren.any():
        tok = m_only_paren["tok"].fillna("").astype(str).str.strip()
        mask_set = mask_only_paren & (num == "") & (~tok.map(_is_monthish))
        split_df.loc[mask_set, "number"] = tok[mask_set].map(_normalize_supplement)
        # always clear volume if it was only "(...)" (monthish or not)
        split_df.loc[mask_only_paren, "volume"] = ""
        num = s("number")

    # 4) Year stored where volume should be: "2017 (10)" or "2017"
    # If year field empty, copy year. If parentheses after year look like issue, move to number.
    vol_now = s("volume")
    m_year = vol_now.str.extract(r"^(?P<year>\d{4})(?:\s*\(\s*(?P<iss>[^)]+?)\s*\))?$")
    mask_year = m_year["year"].notna()
    if mask_year.any():
        yval = m_year["year"].fillna("").astype(str).str.strip()
        iss = m_year["iss"].fillna("").astype(str).str.strip()

        # set year if empty
        mask_set_year = mask_year & (yr == "") & (yval != "")
        split_df.loc[mask_set_year, "year"] = yval[mask_set_year]

        # set number from iss if number empty and iss exists and not monthish
        mask_set_num = mask_year & (num == "") & (iss != "") & (~iss.map(_is_monthish))
        split_df.loc[mask_set_num, "number"] = iss[mask_set_num].map(
            _normalize_supplement
        )

        # clear volume (because it was a year)
        split_df.loc[mask_year, "volume"] = ""

        num = s("number")
        yr = s("year")

    # 5) Main pattern: "V (X)" where X may include nested parentheses like "2(2)"
    vol_now = s("volume")

    # OLD (breaks on nested parens):
    # m_vol_issue = vol_now.str.extract(r"^(?P<vol>[A-Za-z0-9]+)\s*\(\s*(?P<iss>[^)]+?)\s*\)$")

    # NEW (captures everything up to the last ')'):
    m_vol_issue = vol_now.str.extract(
        r"^(?P<vol>[A-Za-z0-9]+)\s*\(\s*(?P<iss>.+)\s*\)$"
    )

    mask_vol_issue = m_vol_issue["vol"].notna()
    if mask_vol_issue.any():
        v = m_vol_issue["vol"].fillna("").astype(str).str.strip()
        iss = m_vol_issue["iss"].fillna("").astype(str).str.strip()

        # always set volume to the leading part
        split_df.loc[mask_vol_issue, "volume"] = v[mask_vol_issue]

        # set number only if empty and issue isn't monthish
        mask_set_num = (
            mask_vol_issue & (num == "") & (iss != "") & (~iss.map(_is_monthish))
        )
        split_df.loc[mask_set_num, "number"] = iss[mask_set_num].map(
            _normalize_supplement
        )

        num = s("number")

    # 6) If any residual "(no pagination)" became empty-only markers, ensure cleaned
    split_df["volume"] = s("volume")
    split_df["number"] = s("number")
    split_df["pages"] = s("pages")

    # 7) If a field is now literally "no pagination" (without parens), drop it too (rare)
    for col in ("volume", "number", "pages"):
        split_df.loc[
            split_df[col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("no pagination"),
            col,
        ] = ""

    return
