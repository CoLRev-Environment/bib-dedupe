#! /usr/bin/env python
"""Match for dedupe"""
import pprint

import pandas as pd
from colrev.constants import Colors
from colrev.constants import Fields

import bib_dedupe.util


# flake8: noqa: E501
# pylint: disable=line-too-long
def match(pairs: pd.DataFrame, *, merge_updated_papers: bool, debug: bool) -> dict:
    p_printer = pprint.PrettyPrinter(indent=4, width=140, compact=False)

    # Queries are better for debugging (understanding which conditions do/do not apply)
    # https://jakevdp.github.io/PythonDataScienceHandbook/03.12-performance-eval-and-query.html
    # pylint: disable=line-too-long
    queries = [
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9 & {Fields.ISBN} > 0.99)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.DOI} > 0.99)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.7 & {Fields.VOLUME} > 0.85 & {Fields.ABSTRACT} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.75 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.8)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.75 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ABSTRACT} > 0.8)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.75 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.8)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8 & {Fields.ABSTRACT} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.7 & {Fields.ABSTRACT} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.NUMBER} > 0.9 & {Fields.PAGES} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.CONTAINER_TITLE} > 0.6 & {Fields.VOLUME} > 0.9 & {Fields.PAGES} > 0.9)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.9 & {Fields.VOLUME} > 0.8 & {Fields.NUMBER} > 0.8)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.CONTAINER_TITLE} > 0.9 & {Fields.NUMBER} > 0.8 & {Fields.PAGES} > 0.8)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.VOLUME} > 0.9 & {Fields.NUMBER} > 0.9 & {Fields.ISBN} > 0.99)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.95 & {Fields.VOLUME} > 0.8 & {Fields.PAGES} > 0.8 & {Fields.ISBN} > 0.99)",
        f"({Fields.AUTHOR} > 0.9 & {Fields.TITLE} > 0.9 & {Fields.ABSTRACT} > 0.9 & {Fields.ISBN} > 0.99)",
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
        # Incomplete cases
        f"({Fields.AUTHOR} == 1 & {Fields.TITLE} == 1 & {Fields.CONTAINER_TITLE} == 1 & {Fields.YEAR} == 1 & {Fields.NUMBER} == 1 & (volume_1 == '' | volume_2 == '') & ({Fields.PAGES} == 1 | {Fields.PAGES} == 0))",
        f"({Fields.AUTHOR} == 1 & {Fields.TITLE} == 1 & {Fields.CONTAINER_TITLE} == 1 & {Fields.YEAR} == 1 & {Fields.NUMBER} == 1 & (pages_1 == '' | pages_2 == '') & ({Fields.VOLUME} == 1 | {Fields.VOLUME} == 0))",
        f"({Fields.AUTHOR} == 1 & {Fields.TITLE} == 1 & {Fields.CONTAINER_TITLE} == 1 & {Fields.YEAR} == 1 & {Fields.PAGES} == 1 & (volume_1 == '' | volume_2 == '') & (number_1 == '' | number_2 == ''))",
    ]

    if debug:
        if pairs.shape[0] != 0:
            p_printer.pprint(pairs.iloc[0].to_dict())
            for item in [
                Fields.AUTHOR,
                Fields.TITLE,
                Fields.CONTAINER_TITLE,
                Fields.VOLUME,
                Fields.NUMBER,
                Fields.PAGES,
                Fields.ABSTRACT,
                Fields.YEAR,
                Fields.DOI,
            ]:
                similarity = pairs.loc[0, item]
                if similarity > 0.9:
                    print(
                        f"{Colors.GREEN}Similarity {item:<20}: {similarity:.2f}{Colors.END}"
                    )
                elif similarity > 0.6:
                    print(
                        f"{Colors.ORANGE}Similarity {item:<20}: {similarity:.2f}{Colors.END}"
                    )
                else:
                    print(
                        f"{Colors.RED}Similarity {item:<20}: {similarity:.2f}{Colors.END}"
                    )

            print("True merge conditions:")
            for query in queries:
                if pairs.query(query).shape[0] > 0:
                    print(f"{Colors.GREEN}{query}{Colors.END}")
                else:
                    print(f"{Colors.RED}{query}{Colors.END}")

    true_pairs = pairs.query("|".join(queries))

    # exclude conditions
    queries = [
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
    ]

    if debug:
        print("Exclude conditions:")
        for query in queries:
            if pairs.query(query).shape[0] != 0:
                print(f"{Colors.RED}{query}{Colors.END}")
            else:
                print(query)

    true_pairs = true_pairs.query("~(" + " | ".join(queries) + ")")

    true_pairs = true_pairs.drop_duplicates()

    updated_paper_pairs = pd.DataFrame()

    # conditions for updated papers
    update_queries = [
        # Note: could check for identical titles, slightly different abstracts
        f'((container_title_1 == "bmj clin evid" & container_title_2 == "bmj clin evid") & {Fields.YEAR} < 1)',
        f'((container_title_1 == "coch data syst revi" & container_title_2 == "coch data syst revi") & {Fields.YEAR} < 1)',
        f'((container_title_1 == "coch data syst revi" & container_title_2 == "coch data syst revi") & {Fields.DOI} < 1)',  # maybe add the following:  & (doi_1.str.contains("pub") | doi_2.str.contains("pub"))
        f'((container_title_1 == "coch data syst revi" & container_title_2 == "coch data syst revi") & {Fields.NUMBER} < 1)',
        f'((container_title_1 == "bmj clin evid" & container_title_2 == "bmj clin evid") & {Fields.DOI} < 1)',
    ]

    if debug:
        print("Conditions for updated paper versions:")
        for update_query in update_queries:
            if pairs.query(update_query).shape[0] != 0:
                print(f"{Colors.RED}{update_query}{Colors.END}")
            else:
                print(update_query)

    updated_paper_pairs = true_pairs.query("(" + " | ".join(update_queries) + ")")
    if merge_updated_papers:
        true_pairs = true_pairs.query("~(" + " | ".join(update_queries) + ")")

    updated_paper_pair_origin_sets = [
        row["colrev_origin_1"].split(";") + row["colrev_origin_2"].split(";")
        for _, row in updated_paper_pairs.iterrows()
    ]
    updated_paper_pairs_origin_sets = bib_dedupe.util.connected_components(
        origin_sets=updated_paper_pair_origin_sets
    )

    maybe_pairs = pd.DataFrame()

    print("TODO : continue here!")

    # TODO : the prevented-same-source merges should go into the manual list
    # TODO : integrate __prevent_invalid_merges here?!
    # TODO : for maybe_pairs, create a similarity score over all fields (catching cases where the entrytypes/fiels are highly erroneous)
    # TODO : think: how do we measure similarity for missing values?

    # true_pairs = true_pairs.drop_duplicates()

    # # Get potential duplicates for manual deduplication
    # maybe_pairs = pairs[
    #     (pairs[Fields.TITLE] > 0.85) & (pairs['author'] > 0.75) |
    #     (pairs[Fields.TITLE] > 0.8) & (pairs[Fields.ABSTRACT] > 0.8) |
    #     (pairs[Fields.TITLE] > 0.8) & (pairs[Fields.ISBN] > 0.99) |
    #     (pairs[Fields.TITLE] > 0.8) & (pairs[Fields.CONTAINER_TITLE] > 0.8) |
    #     (pd.isna(pairs[Fields.DOI]) | (pairs[Fields.DOI] > 0.99) | (pairs[Fields.DOI] == 0)) &
    #     ~((pd.to_numeric(pairs['year1'], errors='coerce') - pd.to_numeric(pairs['year2'], errors='coerce') > 1) |
    #     (pd.to_numeric(pairs['year2'], errors='coerce') - pd.to_numeric(pairs['year1'], errors='coerce') > 1))
    # ]

    # # # Get pairs required for manual dedup which are not in true pairs
    # # maybe_pairs = maybe_pairs[~maybe_pairs.set_index(['record_ID1', 'record_ID2']).index.isin(true_pairs.set_index(['record_ID1', 'record_ID2']).index)]

    # # # Add in problem doi matching pairs and different year data in ManualDedup
    # # important_mismatch = pd.concat([true_pairs_mismatch_doi, year_mismatch_major])
    # important_mismatch = true_pairs_mismatch_doi
    # maybe_pairs = pd.concat([maybe_pairs, important_mismatch])
    # maybe_pairs = maybe_pairs.drop_duplicates()

    origin_sets = [
        row["colrev_origin_1"].split(";") + row["colrev_origin_2"].split(";")
        for _, row in true_pairs.iterrows()
    ]
    duplicate_origin_sets = bib_dedupe.util.connected_components(
        origin_sets=origin_sets
    )

    return {
        "duplicate_origin_sets": duplicate_origin_sets,
        "true_pairs": true_pairs,
        "maybe_pairs": maybe_pairs,
        "updated_paper_pairs": updated_paper_pairs_origin_sets,
    }
