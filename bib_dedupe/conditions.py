#! /usr/bin/env python
"""Matching rules for dedupe"""
from bib_dedupe.constants import Fields

# flake8: noqa: E501
# pylint: disable=line-too-long


def mismatch(*keys: str) -> str:
    return "&".join(
        f" ({key}_1 != {key}_2 & {key}_1 != '' & {key}_2 != '') " for key in keys
    )


def cross_match(key1: str, key2: str) -> str:
    # e.g., volume and number switched
    return f" (({key1}_1 == {key2}_2 & ({key1}_2 == '' | {key2}_1 == '')) | ({key1}_2 == {key2}_1 & ({key1}_1 == '' | {key2}_2 == ''))) "


def match(*args: str, threshold: float = 1.0) -> str:
    if threshold == 1.0:
        return "&".join(f" ({arg} == {threshold}) " for arg in args)
    return "&".join(f" ({arg} > {threshold}) " for arg in args)


def non_contradicting(*keys: str) -> str:
    return " & ".join(
        f" ( {key}_1 == {key}_2  | {key}_1 == '' | {key}_2 == '' ) " for key in keys
    )


def both_entrytypes(entrytype: str) -> str:
    return f"({Fields.ENTRYTYPE}_1 == '{entrytype}' & {Fields.ENTRYTYPE}_2 == '{entrytype}')"


def empty(*keys: str) -> str:
    return " & ".join(f"({key}_1 == '' & {key}_2 == '')" for key in keys)


def pages_forthcoming() -> str:
    return f"({Fields.PAGES}_1.str.startswith('1-') | {Fields.PAGES}_2.str.startswith('1-'))"


au10_ti10_ct10 = f" {match(Fields.AUTHOR, Fields.TITLE, Fields.CONTAINER_TITLE)} "
au10_ti10_ctNC = f" {match(Fields.AUTHOR, Fields.TITLE)} & {non_contradicting(Fields.CONTAINER_TITLE)} "
auNC_ti10_ct10 = f" {match(Fields.CONTAINER_TITLE, Fields.TITLE)} & {non_contradicting(Fields.AUTHOR)} "

au07_ti10_ct10 = (
    f" {match(Fields.TITLE, Fields.CONTAINER_TITLE)} & {Fields.AUTHOR} > 0.7 "
)
au08_ti10_ct10 = (
    f" {match(Fields.TITLE, Fields.CONTAINER_TITLE)} & {Fields.AUTHOR} > 0.8 "
)

au10_ti10_ct08 = (
    f" {match(Fields.TITLE, Fields.AUTHOR)} & {Fields.CONTAINER_TITLE} > 0.8 "
)

au10_ti09_ct10 = (
    f" {match(Fields.CONTAINER_TITLE, Fields.AUTHOR)} & {Fields.TITLE} > 0.9 "
)

au095_ti09_ct075 = f" ({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.75) "

au10_ti08_ct10 = (
    f" ({match(Fields.AUTHOR, Fields.CONTAINER_TITLE)} & {Fields.TITLE} > 0.8 ) "
)


# Notes:
# - structure of conditions:
#   - author/title/container-title first (they require continuous similarities, they rarely have missing data, and field-misassignments are very rare (e.g., author in title field))
#   - volume/number/pages/year/doi/abstract (most require binary similarities, they can have missing data (see non_contradicting()), and misplacements are possible (e.g., number in volume field))

# - "contained_in ..." is not supported by query(). -> covered in similarities
# - for volume/number/pages, the similarities of 0.8/... may not be very helpful considering that we mainly have similarities of 0 or 1
# - Queries are better for debugging (understanding which conditions do/do not apply)
#   https://jakevdp.github.io/PythonDataScienceHandbook/03.12-performance-eval-and-query.html

duplicate_conditions = [
    # TODO : default should be non-contradicting. explicitly state what may differ, how much should match
    # The first condition allows all non_contradicting fields to have one or both values missing.
    f"({au10_ti10_ct10} & {match(Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.DOI)})",  # number can differ
    f"({au10_ti10_ct10} & {match(Fields.VOLUME, Fields.NUMBER, Fields.YEAR)} & {Fields.PAGES} > 0.75 & {non_contradicting(Fields.ABSTRACT, Fields.DOI)})",
    f"({au10_ti10_ct10} & {match(Fields.NUMBER)} & {non_contradicting(Fields.VOLUME, Fields.PAGES, Fields.DOI)} & {Fields.YEAR} > 0.95)",
    # TODO : unit-test cross-match
    f"({au10_ti10_ct10} & {cross_match(Fields.VOLUME, Fields.NUMBER)} & {match(Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.DOI, Fields.ABSTRACT)})",
    f"({au10_ti10_ct10} & {Fields.PAGES} == 1  & {Fields.YEAR} > 0.9 & {non_contradicting(Fields.VOLUME, Fields.NUMBER, Fields.DOI)} & {Fields.ABSTRACT} > 0.95)",
    f"({au10_ti10_ct10} & {non_contradicting(Fields.VOLUME, Fields.NUMBER)} & {Fields.YEAR} > 0.9 & {pages_forthcoming()})",
    f"({au10_ti10_ct10} & {match(Fields.NUMBER, Fields.YEAR)} & {non_contradicting(Fields.DOI, Fields.VOLUME, Fields.ABSTRACT)})",
    f"({au10_ti10_ct08} & {non_contradicting(Fields.YEAR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({au07_ti10_ct10} & {non_contradicting(Fields.YEAR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({au08_ti10_ct10} & {non_contradicting(Fields.YEAR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({au08_ti10_ct10} & {match(Fields.VOLUME, Fields.PAGES)})",
    f"({au08_ti10_ct10} & {match(Fields.DOI)})",
    f"({au08_ti10_ct10} & {non_contradicting(Fields.YEAR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({au10_ti09_ct10} & {non_contradicting(Fields.YEAR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({au10_ti09_ct10} & {match(Fields.YEAR)} & {non_contradicting(Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({au10_ti08_ct10} & {match(Fields.VOLUME, Fields.YEAR)} & {non_contradicting(Fields.NUMBER, Fields.PAGES, Fields.DOI, Fields.ABSTRACT)})",
    f"({au10_ti08_ct10} & {match(Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI, Fields.ABSTRACT)})",
    f"({au10_ti08_ct10} & {match(Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.DOI)} & {Fields.ABSTRACT} > 0.96)",
    f"({au095_ti09_ct075} & {non_contradicting(Fields.YEAR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({au095_ti09_ct075} & {match(Fields.NUMBER, Fields.PAGES)})",
    f"({au095_ti09_ct075} & {match(Fields.VOLUME, Fields.NUMBER)})",
    f"({au095_ti09_ct075} & {match(Fields.VOLUME, Fields.PAGES)})",
    f"({au095_ti09_ct075} & {match(Fields.VOLUME)} & {Fields.ABSTRACT} > 0.9)",
    f"({au095_ti09_ct075} & {match(Fields.ABSTRACT)})",
    #
    f"({Fields.AUTHOR} > 0.8 & {Fields.TITLE} > 0.9 & {match(Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES)})",
    f"({Fields.AUTHOR} > 0.8 & {Fields.TITLE} > 0.9 & {match(Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.YEAR, Fields.DOI, Fields.ABSTRACT)})",
    f"({Fields.AUTHOR} > 0.8 & {Fields.TITLE} > 0.9 & {match(Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES)} & {non_contradicting(Fields.DOI)})",
    f"({Fields.AUTHOR} > 0.8 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.9 & {non_contradicting(Fields.YEAR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({Fields.AUTHOR} > 0.8 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.9 & {match(Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.DOI)})",
    # no AUTHOR
    f"({auNC_ti10_ct10} & {match(Fields.VOLUME, Fields.YEAR)} & {non_contradicting(Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({auNC_ti10_ct10} & {match(Fields.VOLUME, Fields.YEAR)} & {non_contradicting(Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({auNC_ti10_ct10} & {match(Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.DOI)})",
    f"({non_contradicting(Fields.AUTHOR)} & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.YEAR)} & {non_contradicting(Fields.DOI, Fields.ABSTRACT, Fields.NUMBER, Fields.PAGES)})",
    f"({empty(Fields.AUTHOR)} & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.NUMBER, Fields.ABSTRACT, Fields.DOI)})",
    f"({empty(Fields.AUTHOR)} & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.DOI)})",
    f"({empty(Fields.AUTHOR)} & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)})",
    f"({Fields.AUTHOR} > 0.5 & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)}  & {non_contradicting(Fields.DOI, Fields.ABSTRACT)})",
    f"({match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)}  & {non_contradicting(Fields.DOI, Fields.ABSTRACT)})",
    # no CONTAINER_TITLE
    f"({au10_ti10_ctNC} & {match(Fields.VOLUME, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.NUMBER, Fields.ABSTRACT, Fields.DOI)})",
    f"({au10_ti10_ctNC} & {match(Fields.VOLUME, Fields.YEAR)} & {non_contradicting(Fields.NUMBER, Fields.PAGES, Fields.ABSTRACT, Fields.DOI)})",
    f"({au10_ti10_ctNC} & {match(Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.NUMBER, Fields.DOI)})",
    f"({au10_ti10_ctNC} & {match(Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.NUMBER, Fields.DOI)})",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 & {match(Fields.VOLUME, Fields.PAGES, Fields.ISBN)})",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 & {match(Fields.VOLUME, Fields.PAGES)} & {Fields.ABSTRACT} > 0.9)",
    f"({match(Fields.AUTHOR, Fields.TITLE)} & {match(Fields.VOLUME, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.NUMBER, Fields.ABSTRACT, Fields.DOI)})",
    f"({match(Fields.AUTHOR, Fields.TITLE)} & {match(Fields.VOLUME, Fields.NUMBER, Fields.YEAR)} & {non_contradicting(Fields.PAGES, Fields.DOI, Fields.ABSTRACT)})",
    f"({match(Fields.AUTHOR, Fields.TITLE)} & {match(Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.DOI, Fields.ABSTRACT)})",
    f"({match(Fields.AUTHOR, Fields.TITLE)} & {match(Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.DOI, Fields.ABSTRACT)})",
    f"({match(Fields.AUTHOR, Fields.TITLE)} & {match(Fields.VOLUME, Fields.NUMBER, Fields.YEAR)} & {non_contradicting(Fields.PAGES, Fields.DOI, Fields.ABSTRACT)})",
    f"({empty(Fields.CONTAINER_TITLE)} & {match(Fields.TITLE, Fields.AUTHOR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES)} & {non_contradicting(Fields.DOI)})",
    # no TITLE
    f"({Fields.TITLE} == 0.0 & {match(Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.DOI)} & {Fields.ABSTRACT} > 0.95)",  # typically for number-mismatches in title
    f"({Fields.TITLE} == 0.0 & {match(Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR, Fields.ABSTRACT)} & {non_contradicting(Fields.DOI)})",  # typically for number-mismatches in title
    f"({Fields.TITLE} > 0.5 & {match(Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.DOI, Fields.ABSTRACT)})",
    # Special cases
    f'({both_entrytypes("inproceedings")} & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.TITLE} > 0.9 & {Fields.AUTHOR} > 0.8 & {Fields.YEAR} > 0.9)',
]

non_duplicate_conditions = [
    f'({mismatch(Fields.TITLE)} & ({Fields.PAGE_RANGES_ADJACENT} == "adjacent" | {Fields.PAGE_RANGES_ADJACENT} == "non_overlapping"))',
    f"({mismatch(Fields.DOI)} & ~({non_contradicting(Fields.AUTHOR, Fields.TITLE, Fields.YEAR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES)}))",
    f"({mismatch(Fields.DOI, Fields.VOLUME, Fields.NUMBER)})",
    f"({mismatch(Fields.DOI, Fields.VOLUME, Fields.PAGES)})",
    f"({mismatch(Fields.VOLUME, Fields.NUMBER, Fields.PAGES)})",
    f"({mismatch(Fields.VOLUME, Fields.NUMBER, Fields.YEAR)})",
    f"({mismatch(Fields.YEAR, Fields.CONTAINER_TITLE)} & ~({match(Fields.NUMBER)} | {match(Fields.PAGES)} | {match(Fields.VOLUME)} | {match(Fields.DOI)}))",
    f"({mismatch(Fields.YEAR, Fields.CONTAINER_TITLE, Fields.PAGES)})",
    f"({Fields.YEAR} == 0 & ({mismatch(Fields.VOLUME)} | {mismatch(Fields.PAGES)}))",
    f"({mismatch(Fields.YEAR, Fields.DOI, Fields.PAGES)})",
    f"({mismatch(Fields.YEAR, Fields.PAGES)} & {empty(Fields.AUTHOR, Fields.DOI, Fields.VOLUME, Fields.NUMBER, Fields.ABSTRACT)})",
    f"({mismatch(Fields.PAGES, Fields.ABSTRACT, Fields.YEAR)} & {empty(Fields.DOI)})",
    f"({Fields.YEAR} < 0.97 & {Fields.TITLE} < 0.99 & {empty(Fields.NUMBER, Fields.VOLUME)} & {mismatch(Fields.PAGES)} )",
    f"({Fields.YEAR} < 0.97 & {mismatch(Fields.VOLUME, Fields.PAGES)} & {empty(Fields.NUMBER)} )",
    f"({Fields.ABSTRACT} < 0.98 & {Fields.ABSTRACT} > 0.6 & {Fields.YEAR} < 0.99 & {mismatch(Fields.VOLUME)})",
    f"({Fields.CONTAINER_TITLE} < 0.7 & {empty(Fields.NUMBER, Fields.VOLUME)} & {mismatch(Fields.PAGES)} )",
    f'(title_1.str.contains("editor") & ~{non_contradicting(Fields.NUMBER)} & {Fields.ENTRYTYPE}_1 != "inproceedings" & title_1.str.len() < 60)',
    f'(title_1.str.contains("editor") & {mismatch(Fields.VOLUME)} & {Fields.ENTRYTYPE}_1 != "inproceedings" & title_1.str.len() < 60)',
    f'(title_1.str.contains("editor") & {mismatch(Fields.YEAR)} & {Fields.ENTRYTYPE}_1 != "inproceedings" & title_1.str.len() < 60)',
    f'(title_2.str.contains("editor") & ~{non_contradicting(Fields.NUMBER)} & {Fields.ENTRYTYPE}_2 != "inproceedings" & title_2.str.len() < 60)',
    f'(title_2.str.contains("editor") & {mismatch(Fields.VOLUME)} & {Fields.ENTRYTYPE}_2 != "inproceedings" & title_2.str.len() < 60)',
    f'(title_2.str.contains("editor") & {mismatch(Fields.YEAR)} & {Fields.ENTRYTYPE}_2 != "inproceedings" & title_2.str.len() < 60)',
    f"({both_entrytypes('inproceedings')} & {Fields.CONTAINER_TITLE} < 0.9 & {Fields.TITLE} <  0.9)",
    f"({both_entrytypes('inproceedings')} & {Fields.CONTAINER_TITLE} < 0.9 & {Fields.YEAR} <  0.99)",
]

# conditions for updated papers
updated_pair_conditions = [
    # Note: could check for identical titles, slightly different abstracts
    # f'((container_title_1 == "coch data syst rev" & container_title_2 == "coch data syst rev") & ({Fields.TITLE} > 0.95) & ({Fields.YEAR} < 1) & (doi_1 != doi_2))',
    '((container_title_1 == "coch data syst rev" & container_title_2 == "coch data syst rev") & (doi_1.str.slice(0, 25) == doi_2.str.slice(0, 25)) & (doi_1 != doi_2))',
    # f'((container_title_1 == "coch data syst rev" & container_title_2 == "coch data syst rev") & ({Fields.TITLE} > 0.95) & ({Fields.NUMBER} < 1) & (doi_1 != doi_2))',
    '((container_title_1 == "coch data syst rev" & container_title_2 == "coch data syst rev") & (doi_1.str.slice(0, 25) == doi_2.str.slice(0, 25)) & (doi_1 != doi_2))',
    f'((container_title_1 == "bmj clin evid" & container_title_2 == "bmj clin evid") & ({Fields.TITLE} > 0.95) & {Fields.YEAR} < 1)',
    f'((container_title_1 == "bmj clin evid" & container_title_2 == "bmj clin evid") & ({Fields.TITLE} > 0.95) & {Fields.DOI} < 1)',
    f'((container_title_1 == "meth mol biol" & container_title_2 == "meth mol biol") & ({Fields.TITLE} > 0.98) & {Fields.DOI} < 1 & {Fields.YEAR} < 0.8)',
]
