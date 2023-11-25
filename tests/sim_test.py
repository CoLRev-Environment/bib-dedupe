import pytest

from bib_dedupe.sim import calculate_author_similarity
from bib_dedupe.sim import calculate_container_similarity
from bib_dedupe.sim import calculate_page_similarity
from bib_dedupe.sim import calculate_title_similarity
from bib_dedupe.sim import calculate_year_similarity

# flake8: noqa: E501
# pylint: disable=line-too-long


@pytest.mark.parametrize(
    "container_title_1, container_title_2, expected_output",
    [
        ("jama", "j amer medi asso", 1.0),
        ("nati medi j chin", "zhon yi xue za zhi", 1.0),
        # (
        #     "Frontiers in Cellular Neuroscience", "Molecular Psychiatry", 0.0
        # ),
    ],
)
def test_calculate_container_similarity(
    container_title_1: str, container_title_2: str, expected_output: float
) -> None:
    result = calculate_container_similarity(container_title_1, container_title_2)
    assert result == expected_output


@pytest.mark.parametrize(
    "container_title_1, container_title_2, expected_output",
    [
        (
            "comparison of several drugs in treating acute barbiturate depression in the dog 1 single drugs",
            "comparison of several drugs in treating acute barbiturate depression in the dog 2 pairs of drugs",
            0.0,
        ),
        (
            "effects of low and high dose tranylcypromine on [3h]tryptamine binding sites in the rat hippocampus and striatum",
            "effects of low and high dose tranylcypromine on tryptamine binding sites in the rat hippocampus and striatum",
            1.0,
        ),
        (
            "the use of a modified4 damp radioligand binding assay with increased selectivity for muscarinic m3 receptor shows that cortical chrm3 levels are not altered in mood disorders",
            "the use of a modified [3h]4 damp radioligand binding assay with increased selectivity for muscarinic m3 receptor shows that cortical chrm3 levels are not altered in mood disorders",
            1.0,
        ),
        (
            "antidepressant like effects of a novel 5 ht3 receptor antagonist 6z in acute and chronic murine models of depression",
            "antidepressant like effects of a novel 5 ht 3 receptor antagonist 6z in acute and chronic murine models of depression",
            1.0,
        ),
        (
            "definitive cardiac stimulation a comparative study between transvenous and transmediastinal approach",
            "definitive cardiac stimulation a comparative study between transvenous and transmediastinal approach la estimulacion cardiaca definitiva los resultados obtenidos por la via transvenosa y",
            1.0,
        ),
        (
            "role of b1 receptors in the endothelial protective effect of ischaemic preconditioning",
            "role of b1 receptors in the endothelial protective effect of ischaemic preconditioning french implication des recepteurs b1 aux kinines dans la protection endotheliale produite par le preconditionnement ischemique",
            1.0,
        ),
        (
            "55 6 [ 11 c]methyl 36 diazabicyclo[32 0]heptan 3 yl pyridin 2 yl 1h indole as a potential pet radioligand for imaging cerebral alpha7 nachr in mice",
            "55 6 [11c]methyl 36 diazabicyclo[32 0]heptan 3 yl pyridin 2 yl 1h indole as a potential pet radioligand for imaging cerebral a7 nachr in mice",
            0.984375,
        ),
        (
            "preclinical and the first clinical studies on [11c]chiba 1001 for mapping a7 nicotinic receptors by positron emission tomography",
            "preclinical and the first clinical studies on [ 11 c]chiba 1001 for mapping alpha7 nicotinic receptors by positron emission tomography",
            0.9826086956521739,
        ),
    ],
)
def test_calculate_title_similarity(
    container_title_1: str, container_title_2: str, expected_output: float
) -> None:
    result = calculate_title_similarity(container_title_1, container_title_2)
    assert result == expected_output


@pytest.mark.parametrize(
    "author_1, author_full_1, author_2, author_full_2, expected_output",
    [
        (
            "perricone bivona jackson vanderheide",
            "perricone, a j and bivona, b j and jackson, f r and vander heide, r s",
            "perricone bivona jackson heide",
            "perricone, a j and bivona, b j and jackson, f r and heide, r s v",
            0.9624060150375939,
        ),
        ("abdukeyum owen mclennan", "", "abdukeyum owen mclennans", "", 1.0),
        (
            "meng brown ao rowland nordeen banerjee harken",
            "",
            "miki itoh sunaga miura",
            "",
            0.3902439024390244,
        ),
    ],
)
def test_calculate_author_similarity(
    author_1: str,
    author_full_1: str,
    author_2: str,
    author_full_2: str,
    expected_output: float,
) -> None:
    result = calculate_author_similarity(
        author_1, author_full_1, author_2, author_full_2
    )
    assert result == expected_output


@pytest.mark.parametrize(
    "year_1, year_2, expected_output",
    [
        ("2000", "2000", 1.0),
        ("2000", "2001", 0.95),
        ("2000", "2002", 0.8),
        ("2000", "2003", 0.0),
        ("asdf", "2023", 0.0),
    ],
)
def test_calculate_year_similarity(
    year_1: str,
    year_2: str,
    expected_output: float,
) -> None:
    result = calculate_year_similarity(year_1, year_2)
    assert result == expected_output


@pytest.mark.parametrize(
    "pages_1, pages_2, expected_output",
    [
        ("1-10", "1-10", 1.0),
        ("1-10", "11-20", 0.6666666666666667),  # TODO
        ("", "", 1.0),
    ],
)
def test_calculate_page_similarity(
    pages_1: str,
    pages_2: str,
    expected_output: float,
) -> None:
    result = calculate_page_similarity(pages_1, pages_2)
    assert result == expected_output
