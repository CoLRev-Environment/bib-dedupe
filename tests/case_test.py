from pathlib import Path
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

# flake8: noqa


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
                "journal": "Journal of Digital Studies",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "2",
                "author": "Smith, John",
                "title": "Learning-based scheduling for digital work platforms",
                "year": "2020",
                "journal": "Workshop of Digital Studies",
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
        # Attili et al. 2018 vs Annabi & McGann 2019
        # Same DOI in the data, but clearly different papers (title/author/year differ) -> must NOT match
        (
            {
                "ENTRYTYPE": "article",
                "ID": "AttiliMathewSugumaran2018",
                "author": "Attili, V. S. Prakash and Mathew, Saji K. and Sugumaran, Vijayan",
                "year": "2018",
                "title": "Understanding Information Privacy Assimilation in IT Organizations using Multi-site Case Studies",
                "journal": "Communications of the Association for Information Systems",
                "volume": "42",
                "doi": "10.17705/1CAIS.04204",
                "url": "https://aisel.aisnet.org/cais/vol42/iss1/4",
                "language": "eng",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "AnnabiMcGann2019",
                "author": "Annabi, Hala and McGann, Sean T.",
                "year": "2019",
                "title": "MISunderstood - A Longitudinal Analysis of Major MISperceptions",
                "journal": "Communications of the Association for Information Systems",
                "volume": "44",
                "pages": "537--571",
                "doi": "10.17705/1CAIS.04204",
                "url": "https://aisel.aisnet.org/cais/vol44/iss1/27",
                "language": "eng",
            },
            False,
        ),
        # Clary et al. 2022 vs generic CAIS landing page record (truncated DOI/publisher page) -> must NOT match
        (
            {
                "ENTRYTYPE": "article",
                "ID": "ClaryDickVanSlykeEtAl2022",
                "author": "Clary, Grant and Dick, Geoffrey and Van Slyke, Craig and Clary, W. Grant and Akbulut, Asli Yagmur",
                "year": "2022",
                "title": "The After Times: College Students’ Desire to Continue with Distance Learning Post Pandemic",
                "journal": "Communications of the Association for Information Systems",
                "volume": "50",
                "pages": "122--142",
                "doi": "10.17705/1CAIS.05003",
                "url": "https://aisel.aisnet.org/cais/vol50/iss1/3",
                "language": "eng",
            },
            {
                "ENTRYTYPE": "online",
                "ID": "UnknownUNKNOWN",
                "author": "UNKNOWN",
                "title": "Communications of the Association for Information Systems",
                "doi": "10.17705/1CAIS.",  # truncated / not a resolvable article DOI
                "url": "https://aisel.aisnet.org/cais",
                "language": "eng",
            },
            False,
        ),
        # Zhang 2003 (CAIS vol 12, has DOI/title/year) vs PDF-only record with UNKNOWN title/year (vol 56) -> must NOT match
        (
            {
                "ENTRYTYPE": "article",
                "ID": "Zhang2003",
                "author": "Zhang, Dongsong",
                "year": "2003",
                "title": "Delivery of Personalized and Adaptive Content to Mobile Devices - A Framework and Enabling Technology",
                "journal": "Communications of the Association for Information Systems",
                "volume": "12",
                "pages": "183--202",
                "doi": "10.17705/1CAIS.01213",
                "url": "https://aisel.aisnet.org/cais/vol12/iss1/13",
                "language": "eng",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "ZhangLuoQiEtAlUNKNOWN",
                "author": "Zhang, Pengcheng and Luo, Xiaopeng and Qi, Jiayin and Li, Jia",
                "year": "UNKNOWN",
                "title": "UNKNOWN",
                "journal": "Communications of the Association for Information Systems",
                "volume": "56",
                "number": "UNKNOWN",
                # no doi/url on purpose (pdf-only / md_needs_manual_preparation-style)
            },
            False,
        ),
        # Milovich 2019 (CAIS vol 44, has DOI/title/year) vs PDF-only record with UNKNOWN title/year (vol 54) -> must NOT match
        (
            {
                "ENTRYTYPE": "article",
                "ID": "Milovich2019",
                "author": "Milovich, Michael",
                "year": "2019",
                "title": "From Technology Revolution to Digital Revolution - An Interview with F. Warren McFarlan from the Harvard Business School",
                "journal": "Communications of the Association for Information Systems",
                "volume": "44",
                "pages": "152--167",
                "doi": "10.17705/1CAIS.04407",
                "url": "https://aisel.aisnet.org/cais/vol44/iss1/7",
                "language": "eng",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "MilovichRiemenschneiderReychavEtAlUNKNOWN",
                "author": "Milovich, Michael and Riemenschneider, Cynthia and Reychav, Iris and Gewald, Heiko",
                "year": "UNKNOWN",
                "title": "UNKNOWN",
                "journal": "Communications of the Association for Information Systems",
                "volume": "54",
                "number": "UNKNOWN",
                # no doi/url on purpose (pdf-only / md_needs_manual_preparation-style)
            },
            False,
        ),
        # Douglas/Cronan/Jensen 2010 vs Jafar/Furner 2010 (same title/year/venue, different authors)
        (
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "0000006232",
                "author": "Douglas, David E and Cronan, Paul and Jensen, Bradley",
                "title": "Tutorial and Workshop Proposal for AMCIS 2009",
                "booktitle": "Americas Conference on Information Systems",
                "year": "2010",
            },
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "0000010292",
                "author": "Jafar, Musa J and Furner, Christopher",
                "title": "Tutorial and Workshop Proposal for AMCIS 2009",
                "booktitle": "Americas Conference on Information Systems",
                "year": "2010",
            },
            False,
        ),
        # ReynosoManuelLizbethEtAl2010 vs ReynosoManuelCalzadaDeLunaEtAl2013
        (
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "0000005436",
                "author": "Reynoso, Gómez and Manuel, Juan and Lizbeth, Estela and Andrade, Muñoz and Macías Díaz, Jorge Eduardo",
                "year": "2010",
                "title": "UNKNOWN",
                "booktitle": "Americas Conference on Information Systems",
            },
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "0000009531",
                "author": "Reynoso, Gómez and Manuel, Juan and Calzada De Luna, Américo C and Lizbeth, Estela and Andrade, Muñoz",
                "year": "2013",
                "title": "Medición Experimental del Desempeño de las Aplicaciones Bajo Ambientes de Red",
                "booktitle": "Americas Conference on Information Systems",
            },
            False,
        ),
        # TODO: https://chatgpt.com/c/6964c5b3-a084-8327-96de-82a57d4a7ce5
        (
            {
                "ENTRYTYPE": "article",
                "ID": "1",
                "author": "Paré, Guy and Wagner, Gerit and Prester, Julian",
                "title": "How to develop and frame impactful review articles: key recommendations",
                "journal": "Journal of Decision Systems",
                "year": "2024",
                "volume": "33",
                "number": "4",
                "pages": "566--582",
                "doi": "10.1080/12460125.2023.2197701",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "2",
                "author": "Paré, Guy and Wagner, Gerit and Prester, Julian",
                "title": "How to develop and frame impactful review articles: key recommendations",
                "journal": "Journal of Decision Systems",
                "year": "2023",
                "pages": "1--17",
            },
            True,
        ),
        # Erroneous conference merge
        (
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "0000008147",
                "author": "Patel, Nandish V",
                "year": "1999",
                "title": "Developing Tailorable Information Systems through Deferred System's Design",
                "booktitle": "Americas Conference on Information Systems",
            },
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "011979",
                "author": "Patel, Nadya Shaznay and Avnit, Karin and Koh, Jeffrey T K V and Lim, Jawn and Tay, Peter and Supian, Hedirman and Kwan, Jeffrey Tzu and Koh, Valino and Chai, Kay",
                "year": "2025",
                "title": "UNKNOWN",
                "booktitle": "Americas Conference on Information Systems",
            },
            False,
        ),
        # Erroneous conference merge
        (
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "0000002611",
                "author": "Hall, Laura L",
                "year": "1999",
                "title": "Just-in-Time Learning: Web-Based/Internet Delivered Instruction",
                "booktitle": "Americas Conference on Information Systems",
            },
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "0000005291",
                "author": "Hall, Gillian",
                "year": "1995",
                "title": "Negotiation in Database Schema Integration",
                "booktitle": "Americas Conference on Information Systems",
            },
            False,
        ),
        # Erroneous conference merge
        (
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "0000006472",
                "author": "Hall, Dianne and Lee, Kangbok and Han, Sumin and In, Joonhwan",
                "year": "2020",
                "title": "UNKNOWN",
                "booktitle": "Americas Conference on Information Systems",
            },
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "0000005291",
                "author": "Hall, Gillian",
                "year": "1995",
                "title": "Negotiation in Database Schema Integration",
                "booktitle": "Americas Conference on Information Systems",
            },
            False,
        ),
        # different pdfs
        (
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "powell_1999_a_proposed_study",
                "author": "Powell, Anne L",
                "year": "1999",
                "title": "A Proposed Study on Commitment in Virtual Teams",
                "booktitle": "Americas Conference on Information Systems",
            },
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "powell_1999_commitment_virtual_team",
                "author": "Powell, Anne L",
                "year": "1999",
                "title": "Commitment in a Virtual Team",
                "booktitle": "Americas Conference on Information Systems",
            },
            False,
        ),
        # LR and ERF
        (
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "sekar_tech_noteboom_2024_lit_review",
                "author": "Sekar, Aravindh and Tech, Deb and Noteboom, Cherie",
                "year": "2024",
                "title": "Exploring the Impact of Blockchain Integration on Inventory Accuracy and Supply Chain Efficiency -A Literature Review",
                "booktitle": "Americas Conference on Information Systems",
            },
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "sekar_tech_2024_erf_paper",
                "author": "Sekar, Aravindh and Tech, Deb",
                "year": "2024",
                "title": "Exploratory Study on the Impact of Blockchain Adoption on Inventory Accuracy and Supply Chain Efficiency Emergent Research Forum (ERF) Paper",
                "booktitle": "Americas Conference on Information Systems",
            },
            False,
        ),
        # similar title
        (
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "lowry_2002_process_structure",
                "author": "Lowry, Paul Benjamin",
                "year": "2002",
                "title": "Research on process structure for distributed, asynchronous collaborative writing groups",
                "booktitle": "Americas Conference on Information Systems",
            },
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "lowry_2002_proximity_choices",
                "author": "Lowry, Paul Benjamin",
                "year": "2002",
                "title": "Research on proximity choices for distributed, asynchronous collaborative writing groups",
                "booktitle": "Americas Conference on Information Systems",
            },
            False,
        ),
        # different years
        (
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "vaishnav_goel_2025_cognitive_load_subtitle",
                "author": "Vaishnav, Lakshika and Goel, Sanjay",
                "year": "2025",
                "title": "The Impact of Cognitive Load on Responses to Security Alerts: Investigating Human Errors",
                "booktitle": "Americas Conference on Information Systems",
            },
            {
                "ENTRYTYPE": "inproceedings",
                "ID": "vaishnav_goel_2024_cognitive_load",
                "author": "Vaishnav, Lakshika and Goel, Sanjay",
                "year": "2024",
                "title": "The Impact of Cognitive Load on Responses to Security Alerts",
                "booktitle": "Americas Conference on Information Systems",
            },
            False,
        ),
        # Book reviews can be frequent. needs additional information (book title)
        # TODO : in prep-title or similarity: if the title is only "BOOK TITLE", do not match
        (
            {
                "ENTRYTYPE": "article",
                "ID": "1",
                "author": "UNKNOWN",
                "title": "Book review",
                "journal": "European Journal of Information Systems",
                "volume": "4",
                "number": "2",
                "year": "1995",
            },
            {
                "ENTRYTYPE": "article",
                "ID": "2",
                "author": "Hammer, Michael and Champy, James",
                "title": "Book review: Edited by TONY CORNFORD Reengineering the Corporation: A Manifesto for Business Revolution",
                "journal": "European Journal of Information Systems",
                "volume": "4",
                "number": "2",
                "year": "1995",
            },
            False,
        ),
        # Add further (bib_record_1, bib_record_2, expected_match) tuples here
    ],
)
def test_individual_cases_match(
    bib_record_1: dict, bib_record_2: dict, expected_match: bool
) -> None:
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
    if actual_match == expected_match:
        Path("EXPORT.csv").unlink()

    assert actual_match == expected_match
