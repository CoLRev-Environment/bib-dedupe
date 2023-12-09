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


# note: for volume/number/pages, the similarities of 0.8/... may not be very helpful considering that we mainly have similarities of 0 or 1

# Queries are better for debugging (understanding which conditions do/do not apply)
# https://jakevdp.github.io/PythonDataScienceHandbook/03.12-performance-eval-and-query.html

duplicate_conditions = [
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.6 &  {match(Fields.VOLUME, Fields.PAGES)} &  {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.6 &  {match(Fields.NUMBER, Fields.PAGES)} &  {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.6 &  {match(Fields.VOLUME, Fields.NUMBER)} & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.6 &  {match(Fields.VOLUME, Fields.PAGES)})",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.75 & {match(Fields.VOLUME, Fields.PAGES)} &  {Fields.ABSTRACT} > 0.8)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.75 & {match(Fields.NUMBER, Fields.PAGES)} &  {Fields.ABSTRACT} > 0.8)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.75 & {match(Fields.VOLUME, Fields.NUMBER)} & {Fields.ABSTRACT} > 0.8)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.8 &  {match(Fields.VOLUME)} & {Fields.ABSTRACT} > 0.95)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.8 &  {match(Fields.ABSTRACT)})",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.CONTAINER_TITLE} > 0.7 &  {match(Fields.NUMBER, Fields.PAGES)})",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.9 &  {match(Fields.VOLUME, Fields.PAGES)})",
    f"({Fields.AUTHOR} > 0.7 &  {Fields.TITLE} > 0.85 & {match(Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES)})",
    f"({Fields.AUTHOR} > 0.7 &  {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.YEAR, Fields.DOI)})",
    f"({Fields.AUTHOR} > 0.7 &  {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.YEAR, Fields.ABSTRACT)})",
    f"({Fields.AUTHOR} > 0.85 & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.PAGES)})",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.NUMBER} > 0.9 & {Fields.PAGES} > 0.9 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.9 &  {Fields.VOLUME} > 0.9 & {Fields.NUMBER} > 0.9 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.95 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
    # Incomplete data (if one of the fields is empty, at least there is no contradiction)
    f"({Fields.AUTHOR} > 0.9 &  {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.95 & {non_contradicting(Fields.YEAR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({Fields.AUTHOR} > 0.8 &  {Fields.ABSTRACT} > 0.98 & {match(Fields.CONTAINER_TITLE, Fields.TITLE)} & {non_contradicting(Fields.YEAR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({Fields.TITLE} > 0.8 & {match(Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.ABSTRACT, Fields.DOI)})",
    f"({Fields.TITLE} > 0.7 & {match(Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.ABSTRACT, Fields.DOI)})",
    f"({Fields.TITLE} > 0.8 & {Fields.ABSTRACT} > 0.96 & {match(Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.YEAR, Fields.DOI)})",
    f"({Fields.TITLE} > 0.85 & {match(Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.YEAR, Fields.DOI)} & {non_contradicting(Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.ABSTRACT)})",
    f"({Fields.TITLE} > 0.5 & {match(Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR, Fields.DOI)})",
    f"({Fields.TITLE} == 0.0 & {match(Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR, Fields.DOI)})",  # typically for number-mismatches in title
    f"({Fields.AUTHOR} > 0.65 & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.PAGES, Fields.YEAR, Fields.DOI)} & {non_contradicting(Fields.NUMBER, Fields.ABSTRACT)})",
    f"({Fields.AUTHOR} > 0.8 &  {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.DOI)})",
    f"({Fields.AUTHOR} > 0.8 & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.NUMBER, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.DOI)})",
    f"({Fields.CONTAINER_TITLE} > 0.85 & {match(Fields.AUTHOR, Fields.TITLE, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.NUMBER, Fields.DOI)})",
    f"({Fields.CONTAINER_TITLE} > 0.8 & {match(Fields.TITLE, Fields.AUTHOR, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.NUMBER, Fields.DOI)})",
    f"({Fields.CONTAINER_TITLE} > 0.8 & {match(Fields.TITLE, Fields.AUTHOR, Fields.VOLUME, Fields.NUMBER, Fields.YEAR)} & {non_contradicting(Fields.PAGES, Fields.ABSTRACT, Fields.DOI)})",
    f"({match(Fields.AUTHOR, Fields.TITLE, Fields.VOLUME, Fields.PAGES, Fields.YEAR)} & {non_contradicting(Fields.CONTAINER_TITLE, Fields.NUMBER, Fields.ABSTRACT, Fields.DOI)})",
    f"({match(Fields.AUTHOR, Fields.TITLE, Fields.CONTAINER_TITLE, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR)} & {non_contradicting(Fields.VOLUME, Fields.DOI)})",  # number can differ
    f"({match(Fields.AUTHOR, Fields.TITLE, Fields.VOLUME, Fields.YEAR, Fields.DOI)} & {non_contradicting(Fields.CONTAINER_TITLE, Fields.NUMBER, Fields.PAGES, Fields.ABSTRACT)})",
    f"({match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.YEAR, Fields.DOI)} & {non_contradicting(Fields.AUTHOR, Fields.NUMBER, Fields.PAGES, Fields.ABSTRACT)})",
    f"({match(Fields.AUTHOR, Fields.TITLE, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR, Fields.DOI)} & {non_contradicting(Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER)})",
    f"({match(Fields.AUTHOR, Fields.TITLE, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR)} & {non_contradicting(Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.DOI)})",
    f"({match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR,Fields.DOI)} & {non_contradicting(Fields.AUTHOR)})",
    f"({Fields.PAGES} > 0.75 & {match(Fields.AUTHOR, Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.YEAR)} & {non_contradicting(Fields.ABSTRACT, Fields.DOI)})",
    f"({empty(Fields.AUTHOR)} & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI, Fields.YEAR)})",
    f"({empty(Fields.AUTHOR)} & {match(Fields.TITLE, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR)})",
    f"({empty(Fields.CONTAINER_TITLE)} & {match(Fields.TITLE, Fields.AUTHOR, Fields.VOLUME, Fields.NUMBER, Fields.PAGES, Fields.DOI)})",
    f"({cross_match(Fields.VOLUME, Fields.NUMBER)} & {match(Fields.TITLE, Fields.AUTHOR, Fields.CONTAINER_TITLE, Fields.PAGES, Fields.ABSTRACT, Fields.YEAR)} & {non_contradicting(Fields.DOI)})",
    f'({both_entrytypes("inproceedings")} & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.TITLE} > 0.9 & {Fields.AUTHOR} > 0.8 & {Fields.YEAR} > 0.9)',
]

non_duplicate_conditions = [
    f"({mismatch(Fields.DOI, Fields.VOLUME, Fields.NUMBER)})",
    f"({mismatch(Fields.DOI, Fields.VOLUME, Fields.PAGES)})",
    f"({mismatch(Fields.VOLUME, Fields.NUMBER, Fields.PAGES)})",
    f"({mismatch(Fields.VOLUME, Fields.NUMBER, Fields.YEAR)})",
    f"({mismatch(Fields.YEAR, Fields.CONTAINER_TITLE, Fields.PAGES)})",
    f"({Fields.YEAR} == 0 & ({mismatch(Fields.VOLUME)} | {mismatch(Fields.PAGES)}))",
    f"({mismatch(Fields.YEAR, Fields.DOI, Fields.PAGES)})",
    f"({mismatch(Fields.YEAR, Fields.PAGES)} & {empty(Fields.AUTHOR, Fields.DOI, Fields.VOLUME, Fields.NUMBER, Fields.ABSTRACT)})",
    f"({mismatch(Fields.PAGES, Fields.ABSTRACT, Fields.YEAR)} & {empty(Fields.DOI)})",
    f"({Fields.DOI} < 0.99 & {Fields.DOI} > 0.01 & ~({match(Fields.AUTHOR, Fields.TITLE, Fields.YEAR, Fields.CONTAINER_TITLE, Fields.VOLUME, Fields.NUMBER, Fields.PAGES)}))",
    f"({Fields.ABSTRACT} < 0.98 & {Fields.ABSTRACT} > 0.6 & {Fields.YEAR} < 0.99 & {Fields.VOLUME} < 0.99 & volume_1 != '' & volume_2 != '')",
    f"({Fields.VOLUME} < 1 & {Fields.NUMBER} < 1 & {Fields.PAGES} < 1 & volume_1 != '' & volume_2 != '' & number_1 != '' & number_2 != '' & pages_1 != '' & pages_2 != '')",
    f"({Fields.CONTAINER_TITLE} < 0.7 & {empty(Fields.NUMBER, Fields.VOLUME)} & pages_1 != pages_2 )",
    f"({Fields.YEAR} < 0.97 & {Fields.TITLE} < 0.99 & {empty(Fields.NUMBER, Fields.VOLUME)} & pages_1 != pages_2 )",
    f"({Fields.YEAR} < 0.97 & volume_1 != volume_2 & {empty(Fields.NUMBER)} & pages_1 != pages_2 )",
    f'(title_1.str.contains("editor") & ~{non_contradicting(Fields.NUMBER)} & {Fields.ENTRYTYPE}_1 != "inproceedings" & title_1.str.len() < 60)',
    f'(title_1.str.contains("editor") & {Fields.VOLUME} < 1 & {Fields.ENTRYTYPE}_1 != "inproceedings" & title_1.str.len() < 60)',
    f'(title_1.str.contains("editor") & {Fields.YEAR} < 1 & {Fields.ENTRYTYPE}_1 != "inproceedings" & title_1.str.len() < 60)',
    f'(title_2.str.contains("editor") & ~{non_contradicting(Fields.NUMBER)} & {Fields.ENTRYTYPE}_2 != "inproceedings" & title_2.str.len() < 60)',
    f'(title_2.str.contains("editor") & {Fields.VOLUME} < 1 & {Fields.ENTRYTYPE}_2 != "inproceedings" & title_2.str.len() < 60)',
    f'(title_2.str.contains("editor") & {Fields.YEAR} < 1 & {Fields.ENTRYTYPE}_2 != "inproceedings" & title_2.str.len() < 60)',
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
