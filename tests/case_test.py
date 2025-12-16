from typing import Any
from typing import Dict
from typing import Iterable
from typing import Set

import pandas as pd
import pytest

import bib_dedupe.cluster
from bib_dedupe.bib_dedupe import block
from bib_dedupe.bib_dedupe import match
from bib_dedupe.bib_dedupe import prep


def _make_records_df(rec1: Dict[str, Any], rec2: Dict[str, Any]) -> pd.DataFrame:
    """Create a tiny records DataFrame with two BibTeX-style records."""
    rec1_full = {"record_id": "r1", **rec1}
    rec2_full = {"record_id": "r2", **rec2}
    return pd.DataFrame([rec1_full, rec2_full])


def _in_same_cluster(
    duplicate_id_sets: Iterable[Iterable[str]], a: str, b: str
) -> bool:
    """Return True if ids `a` and `b` appear together in at least one duplicate cluster."""
    target: Set[str] = {a, b}
    for group in duplicate_id_sets:
        if target.issubset(set(group)):
            return True
    return False


@pytest.mark.parametrize(
    "bib_record_1, bib_record_2, expected_match",
    [
        (
            {
                "ENTRYTYPE": "article",
                "ID": "1",
                "doi": "10.1073/PNAS.1604234114",
                "author": "Abrahao, Bruno and Parigi, Paolo and Gupta, Alok and Cook, Karen S.",
                "title": "Reputation offsets trust judgments based on social biases among Airbnb users",
                "journal": "Proceedings of the National Academy of Sciences",
                "number": "37",
                "pages": "9848--9853",
                "volume": "114",
                "year": "2017",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "2",
                "author": "B. Abrahao; P. Parigi; A. Gupta; K. S. Cook",
                "year": "2017",
                "title": "Reputation offsets trust judgments based on social biases among Airbnb users",
            },
            True,
        ),
        (
            {
                "ENTRYTYPE": "article",
                "ID": "1",
                "author": "Smith, John",
                "title": "Learning-based scheduling for digital work platforms",
                "year": "2020",
                "journal": "Journal of Digital Work Studies",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "2",
                "author": "Smith, John",
                "title": "Learning-based scheduling for digital work platforms",
                "year": "2020",
                "journal": "Workshoper of Digital Work Studies",
            },
            False,
        ),
        # Tan et al. 2004 vs 2005 (same review, different issue/year/doi suffix)
        (
            {
                "ENTRYTYPE": "article",
                "ID": "id_0022176",
                "author": "Tan A.Schulze A.O'Donnell C. P.Davis P. G.",
                "year": "2004",
                "title": "AIR VERSUS OXYGEN FOR RESUSCITATION OF INFANTS AT BIRTH",
                "journal": "Cochrane Database Syst Rev",
                "number": "3",
                "pages": "Cd002273",
                "doi": "10.1002/14651858.CD002273.pub2",
                "isbn": "1361-6137",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "id_0021834",
                "author": "Tan A.Schulze A.O'Donnell C. P.Davis P. G.",
                "year": "2005",
                "title": "AIR VERSUS OXYGEN FOR RESUSCITATION OF INFANTS AT BIRTH",
                "journal": "Cochrane Database Syst Rev",
                "number": "2",
                "pages": "Cd002273",
                "doi": "10.1002/14651858.CD002273.pub3",
                "isbn": "1361-6137",
            },
            True,
        ),
        # Li et al. 2019 (exact same DOI; abstract formatting differs)
        (
            {
                "ENTRYTYPE": "article",
                "ID": "id_0001432",
                "author": "Li Z. M.Kong C. Y.Zhang S. L.Han B.Zhang Z. Y.Wang L. S.",
                "year": "2019",
                "title": "ALCOHOL AND HBV SYNERGISTICALLY PROMOTE HEPATIC STEATOSIS",
                "journal": "Ann Hepatol",
                "volume": "18",
                "number": "6",
                "pages": "913-917",
                "doi": "10.1016/j.aohep.2019.04.013",
                "isbn": "1665-2681 (Print)\n1665-2681",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "id_0025776",
                "author": "Li Z. M.Kong C. Y.Zhang S. L.Han B.Zhang Z. Y.Wang L. S.",
                "year": "2019",
                "title": "ALCOHOL AND HBV SYNERGISTICALLY PROMOTE HEPATIC STEATOSIS",
                "journal": "Ann Hepatol",
                "volume": "18",
                "number": "6",
                "pages": "913-917",
                "doi": "10.1016/j.aohep.2019.04.013",
                "isbn": "1665-2681",
            },
            True,
        ),
        # Adeli & Lewis 2008 (same DOI; multiple IDs/“search_set” variants)
        (
            {
                "ENTRYTYPE": "article",
                "ID": "id_0000728",
                "author": "Adeli K.Lewis G. F.",
                "year": "2008",
                "title": "Intestinal lipoprotein overproduction in insulin-resistant states",
                "journal": "Curr Opin Lipidol",
                "volume": "19",
                "number": "3",
                "pages": "221-8",
                "doi": "10.1097/MOL.0b013e3282ffaf82",
                "isbn": "0957-9672 (Print)\n0957-9672",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "id_0000728B",
                "author": "Adeli K.Lewis G. F.",
                "year": "2008",
                "title": "Intestinal lipoprotein overproduction in insulin-resistant states",
                "journal": "Curr Opin Lipidol",
                "volume": "19",
                "number": "3",
                "pages": "221-8",
                "doi": "10.1097/MOL.0b013e3282ffaf82",
                "isbn": "0957-9672 (Print)\n0957-9672",
            },
            True,
        ),
        (
            {
                "ENTRYTYPE": "article",
                "ID": "id_0000728B",
                "author": "Adeli K.Lewis G. F.",
                "year": "2008",
                "title": "Intestinal lipoprotein overproduction in insulin-resistant states",
                "journal": "Curr Opin Lipidol",
                "volume": "19",
                "number": "3",
                "pages": "221-8",
                "doi": "10.1097/MOL.0b013e3282ffaf82",
                "isbn": "0957-9672 (Print)\n0957-9672",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "id_0000728NEW",
                "author": "Adeli K.Lewis G. F.",
                "year": "2008",
                "title": "Intestinal lipoprotein overproduction in insulin-resistant states",
                "journal": "Curr Opin Lipidol",
                "volume": "19",
                "number": "3",
                "pages": "221-8",
                "doi": "10.1097/MOL.0b013e3282ffaf82",
                "isbn": "0957-9672 (Print)\n0957-9672",
            },
            True,
        ),
        # Sauer & Seuring 2023 (misc vs article representation; same DOI)
        (
            {
                "ENTRYTYPE": "misc",
                "ID": "SauerSeuring2023",
                "author": "Sauer, Philipp C and Seuring, Stefan",
                "year": "2023",
                "title": "How to conduct systematic literature reviews in management research: a guide in 6 steps and 14 decisions",
                "doi": "10.1007/S11846-023-00668-3",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "SauerSeuring2023B",
                "author": "Sauer, Philipp C. and Seuring, Stefan",
                "year": "2023",
                "title": "How to conduct systematic literature reviews in management research: a guide in 6 steps and 14 decisions",
                "journal": "Review of Managerial Science",
                "volume": "17",
                "number": "5",
                "pages": "1899--1933",
                "doi": "10.1007/S11846-023-00668-3",
            },
            True,
        ),
        # Clark et al. 2025 (misc vs article; same DOI)
        (
            {
                "ENTRYTYPE": "misc",
                "ID": "ClarkBartonAlbarqoEtAl2025",
                "author": "Clark, Justin; Barton, Belinda; Albarqo, Loai; Byambasuren, Oyungerel; Jowsey, Tanisha; Keogh, Justin; Liang, Tian; Moro, Christian; O'neill, Hayley; Jones, Mark",
                "year": "2025",
                "title": "Generative artificial intelligence use in evidence synthesis: A systematic review",
                "doi": "10.1017/RSM.2025.16",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "ClarkBartonAlbarqouniEtAl2025",
                "author": "Clark, Justin; Barton, Belinda; Albarqouni, Loai; Byambasuren, Oyungerel; Jowsey, Tanisha; Keogh, Justin; Liang, Tian; Moro, Christian; O’Neill, Hayley; Jones, Mark",
                "year": "2025",
                "title": "Generative artificial intelligence use in evidence synthesis: A systematic review",
                "journal": "Research Synthesis Methods",
                "volume": "16",
                "number": "4",
                "pages": "601--619",
                "doi": "10.1017/RSM.2025.16",
            },
            True,
        ),
        # Add further (bib_record_1, bib_record_2, expected_match) tuples here
    ],
)
def test_individual_cases_match(bib_record_1, bib_record_2, expected_match) -> None:
    """Check if two BibTeX-like records are deduplicated as expected."""
    records_df = _make_records_df(bib_record_1, bib_record_2)

    prep_df = prep(records_df)
    pairs_df = block(records_df=prep_df)
    pairs_df.to_csv("EXPORT.csv")
    matched_df = match(pairs_df, verbosity_level=2)
    print(matched_df)

    duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)
    print(duplicate_id_sets)

    actual_match = _in_same_cluster(
        duplicate_id_sets, bib_record_1["ID"], bib_record_2["ID"]
    )

    assert actual_match == expected_match
