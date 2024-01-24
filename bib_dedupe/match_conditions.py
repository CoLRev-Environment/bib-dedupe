#! /usr/bin/env python
"""Matching rules for dedupe"""
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import CONTAINER_TITLE
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import ENTRYTYPE
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGE_RANGES_ADJACENT
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR

# flake8: noqa: E501
# pylint: disable=line-too-long


def mismatch(*keys: str) -> str:
    return "&".join(
        f" ({key}_1 != {key}_2 & {key}_1 != '' & {key}_2 != '') " for key in keys
    )


def match(*args: str, threshold: float = 1.0) -> str:
    if threshold == 1.0:
        return "&".join(f" ({arg} == {threshold}) " for arg in args)
    return "&".join(f" ({arg} > {threshold}) " for arg in args)


def non_contradicting(*keys: str) -> str:
    return " & ".join(
        f" ( {key}_1 == {key}_2  | {key}_1 == '' | {key}_2 == '' ) " for key in keys
    )


def both_entrytypes(entrytype: str) -> str:
    return f"({ENTRYTYPE}_1 == '{entrytype}' & {ENTRYTYPE}_2 == '{entrytype}')"


au07_ti10_ct10 = f" {match(TITLE, CONTAINER_TITLE)} & {AUTHOR} > 0.7 "
au10_ti07_ct10 = f" ({match(AUTHOR, CONTAINER_TITLE)} & {TITLE} > 0.7 ) "
au10_ti10_ct07 = f" {match(TITLE, AUTHOR)} & {CONTAINER_TITLE} > 0.7 "
au095_ti09_ct075 = f" ({AUTHOR} > 0.95 & {TITLE} > 0.9 &  {CONTAINER_TITLE} > 0.75) "
au08_ti09_ct09 = f" ({AUTHOR} > 0.8 & {TITLE} > 0.9 & {CONTAINER_TITLE} > 0.9) "
au09_ti09_ctXX = f" ({AUTHOR} > 0.9 & {TITLE} > 0.9) "
auXX_ti095_ct095 = f" ({TITLE} > 0.95 & {CONTAINER_TITLE} > 0.95) "
au10_tiXX_ct10 = f" ({match(AUTHOR)} & {match(CONTAINER_TITLE)}) "
au10_ti10_ctNC = f" {match(AUTHOR, TITLE)} & {non_contradicting(CONTAINER_TITLE)} "

# Notes:
# - structure of conditions:
#   - author/title/container-title first (they require continuous similarities, they rarely have missing data, and field-misassignments are very rare (e.g., author in title field))
#   - volume/number/pages/year/doi/abstract (most require binary similarities, they can have missing data (see non_contradicting()), and misplacements are possible (e.g., number in volume field))
#   - VOLUME, NUMBER, PAGES, generally be non_contradicting (because they have missing values). similarities of 0.8/... may not be very helpful considering that we mainly have similarities of 0 or 1
#   - especially for doi and abstract, non_contradicting is preferred.

# - "contained_in ..." is not supported by query(). -> covered in similarities
# - Queries are better for debugging (understanding which conditions do/do not apply)
#   https://jakevdp.github.io/PythonDataScienceHandbook/03.12-performance-eval-and-query.html

duplicate_conditions = [
    # Substantial differences in one of AUTHOR/TITLE/CONTAINER_TITLE
    f"({au07_ti10_ct10} & {match(VOLUME, PAGES)})",
    f"({au07_ti10_ct10} & {non_contradicting(VOLUME, NUMBER, PAGES, YEAR, DOI)})",
    f"({au10_ti07_ct10} & {non_contradicting(NUMBER, PAGES, YEAR, DOI)})",
    f"({au10_ti10_ct07} & {non_contradicting(VOLUME, NUMBER, PAGES, YEAR, DOI)})",
    # Differences across AUTHOR/TITLE/CONTAINER_TITLE
    f"({au08_ti09_ct09} & {non_contradicting(VOLUME, NUMBER, YEAR, DOI)} & {PAGES} > 0.75 )",
    f"({au08_ti09_ct09} & {non_contradicting(VOLUME, NUMBER, PAGES, DOI)})",
    f"({au095_ti09_ct075} & {non_contradicting(VOLUME, NUMBER, PAGES, YEAR, DOI)})",
    f"({au095_ti09_ct075} & {match(NUMBER, PAGES)})",
    f"({au095_ti09_ct075} & {match(VOLUME, NUMBER)})",
    f"({au095_ti09_ct075} & {match(VOLUME, PAGES)})",
    f"({au095_ti09_ct075} & {match(VOLUME)} & {ABSTRACT} > 0.9)",
    f"({au095_ti09_ct075} & {match(YEAR, ABSTRACT)})",
    # Special cases
    f'({au095_ti09_ct075} & {both_entrytypes("inproceedings")} & {match(YEAR)})',  # Inproceedings
    f"({au07_ti10_ct10} & {DOI} > 0.9)",  # Updates
    # no AUTHOR
    f"({auXX_ti095_ct095} & {non_contradicting(VOLUME, NUMBER, PAGES, YEAR, DOI)})",
    f"({auXX_ti095_ct095} & {match(VOLUME, NUMBER, PAGES, YEAR)} & {non_contradicting(DOI, ABSTRACT)})",
    # no CONTAINER_TITLE
    f"({au10_ti10_ctNC} & {match(VOLUME, YEAR)} & {non_contradicting(NUMBER, PAGES, DOI, ABSTRACT)})",
    f"({au09_ti09_ctXX} & {match(PAGES, DOI)} & {non_contradicting(VOLUME, NUMBER, ABSTRACT)} & {YEAR} > 0.9)",
    f"({au09_ti09_ctXX} & ({match(NUMBER)} & {non_contradicting(PAGES)} | {non_contradicting(NUMBER)} & {match(PAGES)}) & {non_contradicting(VOLUME, YEAR, DOI, ABSTRACT)})",
    f"({au09_ti09_ctXX} & {match(VOLUME, PAGES)})",
    f"({au09_ti09_ctXX} & {match(PAGES, YEAR)} & {non_contradicting(VOLUME, NUMBER, DOI)})",
    # no TITLE
    f"({au10_tiXX_ct10} & {match(VOLUME, NUMBER, PAGES, YEAR)} & {non_contradicting(DOI)} & ({ABSTRACT} > 0.95 | {non_contradicting(ABSTRACT)}))",  # typically for number-mismatches in title
]

non_duplicate_conditions = [
    f"({mismatch(YEAR)} & ~({match(VOLUME)} | {match(NUMBER)} | {match(PAGES)} | {match(DOI)} | {match(CONTAINER_TITLE)}))",
    f'({mismatch(TITLE)} & ({PAGE_RANGES_ADJACENT} == "adjacent" | {PAGE_RANGES_ADJACENT} == "non_overlapping"))',
    f"(~(doi_1 == '' | doi_2 == '') & {DOI} < 0.8 & ~({non_contradicting(AUTHOR, TITLE, YEAR, CONTAINER_TITLE, VOLUME, NUMBER, PAGES)}))",
    f"({mismatch(VOLUME, NUMBER, PAGES)})",
    # Editorials: minor differences in volume/number/pages can be meaningful
    f'(title_1.str.contains("editor") & title_1.str.len() < 60 & ( {mismatch(VOLUME)} | {mismatch(NUMBER)} | {mismatch(PAGES)}))',
]
