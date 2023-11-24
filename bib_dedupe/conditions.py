#! /usr/bin/env python
"""Matching rules for dedupe"""
from colrev.constants import Fields

# flake8: noqa: E501
# pylint: disable=line-too-long


# Queries are better for debugging (understanding which conditions do/do not apply)
# https://jakevdp.github.io/PythonDataScienceHandbook/03.12-performance-eval-and-query.html
# pylint: disable=line-too-long
duplicate_conditions = [
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.DOI} > 0.99)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.8 & {Fields.VOLUME} > 0.85 & {Fields.ABSTRACT} > 0.95)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.75 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.8)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.75 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.8)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.75 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.8)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.8 & {Fields.ABSTRACT} > 0.9)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.NUMBER} > 0.9 & {Fields.PAGES} > 0.9)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.VOLUME} > 0.9 & {Fields.PAGES} > 0.9)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.9 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.9 & {Fields.NUMBER} > 0.9 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.ABSTRACT} > 0.95 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.NUMBER} > 0.9 & {Fields.PAGES} > 0.9 & {Fields.ISBN} > 0.99)",
    f"({Fields.AUTHOR} > 0.95 & title_partial_ratio > 0.8 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.DOI} > 0.99)",
    f"({Fields.AUTHOR} > 0.99 & title_partial_ratio > 0.7 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.YEAR} > 0.99 & {Fields.VOLUME} > 0.99 & {Fields.NUMBER} > 0.99 & {Fields.DOI} > 0.99)",
    f"({Fields.AUTHOR} > 0.8 & {Fields.TITLE} > 0.99 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.DOI} > 0.99)",
    f"({Fields.AUTHOR} > 0.7 & {Fields.TITLE} > 0.85 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.VOLUME} > 0.99 & {Fields.NUMBER} > 0.99 & {Fields.PAGES} > 0.99)",
    f"({Fields.AUTHOR} > 0.7 & {Fields.TITLE} > 0.99 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.VOLUME} > 0.99 & {Fields.NUMBER} > 0.99 & {Fields.YEAR} > 0.99 & {Fields.DOI} > 0.99)",
    f"({Fields.AUTHOR} > 0.7 & {Fields.TITLE} > 0.99 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.VOLUME} > 0.99 & {Fields.NUMBER} > 0.99 & {Fields.YEAR} > 0.99 & {Fields.ABSTRACT} > 0.99)",
    f"({Fields.AUTHOR} > 0.85 & {Fields.TITLE} > 0.99 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.VOLUME} > 0.99 & {Fields.PAGES} > 0.99)",
    f"({Fields.AUTHOR} > 0.99 & {Fields.TITLE} > 0.7 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.VOLUME} > 0.99 & {Fields.NUMBER} > 0.99 & {Fields.PAGES} > 0.99 & {Fields.YEAR} > 0.99)",
    f'({Fields.AUTHOR} > 0.99 & {Fields.TITLE} > 0.99 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.VOLUME} > 0.99 & {Fields.YEAR} > 0.99 & number_1 == "" & number_2 == "")',
    f"({Fields.TITLE} > 0.99 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.VOLUME} > 0.99 & {Fields.NUMBER} > 0.99 & {Fields.PAGES} > 0.99 & {Fields.YEAR} > 0.99 & {Fields.DOI} > 0.99)",
    f'({Fields.ENTRYTYPE}_1 == "inproceedings" & {Fields.ENTRYTYPE}_2 == "inproceedings" & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.TITLE} > 0.9 & {Fields.AUTHOR} > 0.8 & {Fields.YEAR} > 0.9)',
    # Incomplete data (if one of the fields is empty, at least there is no contradiction)
    f"({Fields.AUTHOR} == 1 & {Fields.TITLE} == 1 & {Fields.CONTAINER_TITLE} == 1 & {Fields.YEAR} == 1 & {Fields.NUMBER} == 1 & (volume_1 == '' | volume_2 == '') & ({Fields.PAGES} == 1 | {Fields.PAGES} == 0))",
    f"({Fields.AUTHOR} == 1 & {Fields.TITLE} == 1 & {Fields.CONTAINER_TITLE} == 1 & {Fields.YEAR} == 1 & {Fields.NUMBER} == 1 & (pages_1 == '' | pages_2 == '') & ({Fields.VOLUME} == 1 | {Fields.VOLUME} == 0))",
    f"({Fields.AUTHOR} == 1 & {Fields.TITLE} == 1 & {Fields.CONTAINER_TITLE} == 1 & {Fields.YEAR} == 1 & {Fields.PAGES} == 1 & (volume_1 == '' | volume_2 == '') & (number_1 == '' | number_2 == ''))",
]

non_duplicate_conditions = [
    f"({Fields.DOI} < 0.99 & {Fields.DOI} > 0.01 & ~({Fields.AUTHOR} > 0.99 & {Fields.TITLE} > 0.99 & {Fields.YEAR} > 0.99 & {Fields.CONTAINER_TITLE} > 0.99 & {Fields.VOLUME} > 0.99 & {Fields.NUMBER} > 0.99 & {Fields.PAGES} > 0.99))",
    f"({Fields.ABSTRACT} < 0.98 & {Fields.ABSTRACT} > 0.6 & {Fields.YEAR} < 0.99 & {Fields.VOLUME} < 0.99 & volume_1 != '' & volume_2 != '')",
    f'(title_1.str.contains("editor") & {Fields.NUMBER} < 1 & {Fields.ENTRYTYPE}_1 != "inproceedings" & title_1.str.len() < 60)',
    f'(title_1.str.contains("editor") & {Fields.VOLUME} < 1 & {Fields.ENTRYTYPE}_1 != "inproceedings" & title_1.str.len() < 60)',
    f'(title_1.str.contains("editor") & {Fields.YEAR} < 1 & {Fields.ENTRYTYPE}_1 != "inproceedings" & title_1.str.len() < 60)',
    f'(title_2.str.contains("editor") & {Fields.NUMBER} < 1 & {Fields.ENTRYTYPE}_2 != "inproceedings" & title_2.str.len() < 60)',
    f'(title_2.str.contains("editor") & {Fields.VOLUME} < 1 & {Fields.ENTRYTYPE}_2 != "inproceedings" & title_2.str.len() < 60)',
    f'(title_2.str.contains("editor") & {Fields.YEAR} < 1 & {Fields.ENTRYTYPE}_2 != "inproceedings" & title_2.str.len() < 60)',
    '(title_1.str.endswith("part 1") & (title_2.str.endswith("part 2"))) | (title_1.str.endswith("part 2") & (title_2.str.endswith("part 1")))',
    '(title_1.str.startswith("correction to") & ~title_2.str.startswith("correction to")) | (title_1.str.startswith("corrigendum to") & ~title_2.str.startswith("corrigendum to"))',
    '(title_1.str.startswith("withdrawn ") & ~title_2.str.startswith("withdrawn ")) | (~title_1.str.startswith("withdrawn ") & title_2.str.startswith("withdrawn "))',
    '(~title_1.str.contains("response") & title_2.str.contains("response")) | (title_1.str.contains("response") & ~title_2.str.contains("response"))',
    f"({Fields.VOLUME} < 1 & {Fields.NUMBER} < 1 & {Fields.PAGES} < 1 & volume_1 != '' & volume_2 != '' & number_1 != '' & number_2 != '' & pages_1 != '' & pages_2 != '')",
]

# conditions for updated papers
updated_pair_conditions = [
    # Note: could check for identical titles, slightly different abstracts
    f'((container_title_1 == "bmj clin evid" & container_title_2 == "bmj clin evid") & {Fields.YEAR} < 1)',
    f'((container_title_1 == "coch data syst revi" & container_title_2 == "coch data syst revi") & {Fields.YEAR} < 1)',
    f'((container_title_1 == "coch data syst revi" & container_title_2 == "coch data syst revi") & {Fields.DOI} < 1)',
    f'((container_title_1 == "coch data syst revi" & container_title_2 == "coch data syst revi") & {Fields.NUMBER} < 1)',
    f'((container_title_1 == "bmj clin evid" & container_title_2 == "bmj clin evid") & {Fields.DOI} < 1)',
]
