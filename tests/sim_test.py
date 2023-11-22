import pandas as pd
import pytest

from bib_dedupe.sim import calculate_container_similarity
from bib_dedupe.sim import calculate_title_similarity

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
    row = pd.Series(
        {"container_title_1": container_title_1, "container_title_2": container_title_2}
    )
    result = calculate_container_similarity(row)
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
            0.9497206703910615,
        ),
    ],
)
def test_calculate_title_similarity(
    container_title_1: str, container_title_2: str, expected_output: float
) -> None:
    row = pd.Series({"title_1": container_title_1, "title_2": container_title_2})
    result = calculate_title_similarity(row)
    assert result == expected_output
