import pytest

from bib_dedupe.sim import page_ranges_adjacent
from bib_dedupe.sim import sim_abstract
from bib_dedupe.sim import sim_author
from bib_dedupe.sim import sim_container_title
from bib_dedupe.sim import sim_number
from bib_dedupe.sim import sim_page
from bib_dedupe.sim import sim_title
from bib_dedupe.sim import sim_volume
from bib_dedupe.sim import sim_year

# flake8: noqa: E501
# pylint: disable=line-too-long


@pytest.mark.parametrize(
    "container_title_1, container_title_2, expected_output",
    [
        ("jama", "j amer medi asso", 1.0),
        ("j hear lung tran", "tran", 0.4),
        ("inte conf info syst", "icis", 1.0),
        (
            "paci asia conf info syst",
            "paci asia conf info syst oppo chal digi soci are we read paci",
            1.0,
        ),
        ("j clin onco", "j clin onco offi j am soci clin onco", 1.0),
        ("surg endo", "surg endo othe inte tech", 1.0),
        ("j trau inju infe crit care", "j trau", 1.0),
        ("euro resp j conf", "am j resp crit care med conf", 0.0)
        # (
        #     "Frontiers in Cellular Neuroscience", "Molecular Psychiatry", 0.0
        # ),
    ],
)
def test_sim_container_title(
    container_title_1: str, container_title_2: str, expected_output: float
) -> None:
    result = sim_container_title(container_title_1, container_title_2)
    assert result == expected_output


@pytest.mark.parametrize(
    "title_1, title_2, expected_output",
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
        # (
        #     "definitive cardiac stimulation a comparative study between transvenous and transmediastinal approach",
        #     "definitive cardiac stimulation a comparative study between transvenous and transmediastinal approach la estimulacion cardiaca definitiva los resultados obtenidos por la via transvenosa y",
        #     1.0,
        # ),
        # (
        #     "role of b1 receptors in the endothelial protective effect of ischaemic preconditioning",
        #     "role of b1 receptors in the endothelial protective effect of ischaemic preconditioning french implication des recepteurs b1 aux kinines dans la protection endotheliale produite par le preconditionnement ischemique",
        #     1.0,
        # ),
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
        (
            "protective effect pacing reperfusion induced ventricular arrhythmias isolated rat hearts",
            "protective effect pacing reperfusion induced ventricular arrhythmias isolated rat hearts effet protecteur de l entrainement electrosystolique sur les arythmies ventriculaires induites par la reperfusion dans les coeurs de rat isoles",
            1.0,
        ),
        (
            "behavioral fluorodeoxyglucose micro positron emission tomography imaging study rat chronic mild stress model depression",
            "behavioral [f 18] fluorodeoxyglucose micro positron emission tomography imaging study rat chronic mild stress model depression",
            1.0,
        ),
        (
            "systematic analysis safety prescribing anti rheumatic immunosuppressive biologic drugs men trying conceive",
            "systematic analysis safety prescribing anti rheumatic immunosuppressive biologic drugs pregnant women autoimmune rheumatic disease",
            0.0,
        ),
        (
            "influence childhood abuse adult stressful life events temperaments depressive symptoms nonclinical general adult population",
            "moderator effects affective temperaments childhood abuse adult stressful life events depressive symptoms nonclinical general adult population",
            0.7954545454545454,
        ),
        (
            "immature hearts respond metabolically different remote ischemic preconditioning than mature hearts tracer study",
            "adverse effects remote ischemic preconditioning immature heart",
            0.8064516129032258,
        ),
        (
            "infection inflammatory mechanisms reprinted journal clinical periodontology vol 40 pg s1 s72013",
            "infection inflammatory mechanisms",
            1.0,
        ),
        (
            "comparison human papillomavirus dna testing repeat papanicolaou test women low grade cervical cytologic abnormalities randomized trial hpv effectiveness lowgrade paps help stud",
            "comparison human papillomavirus dna testing repeat papanicolaou test women low grade cervical cytologic abnormalities randomized trial",
            1.0,
        ),
        # (
        #     "simultaneous ltp non",
        #     "simultaneous ltp non nmda ltd nmda receptor mediated responses nucleus accumbens",
        #     1.0,
        # ),
        (
            "learned helplessness model depression",
            "psychiatric progress learned helplessness model depression",
            1.0,
        ),
        (
            "comment re assessment safety silver household water treatment rapid systematic review mammalian vivo genotoxicity studies",
            "re assessment safety silver household water treatment rapid systematic review mammalian vivo genotoxicity studies",
            0.0,
        ),
        (
            "re assessment safety silver household water treatment rapid systematic review mammalian vivo genotoxicity studies",
            "author s response comment re assessment safety silver household water treatment rapid systematic review mammalian vivo genotoxicity studies",
            0.0,
        ),
        (
            "thrombomodulin atypical hemolytic uremic syndrome",
            "thrombomodulin atypical hemolytic uremic syndrome authors reply",
            0.0,
        ),
        (
            "open label, multi center clinical trial eculizumab pediatric patients atypical hemolytic uremic syndrome",
            "open label, multi center clinical trial eculizumab adult patients atypical hemolytic uremic syndrome",
            0.0,
        ),
        # ("cardiac vascular remodelling effect antihypertensive agents",
        #  "session 2 cardiac vascular remodelling effect antihypertensive agents",
        #  1.0),
        ("", "", 0.0),
    ],
)
def test_sim_title(title_1: str, title_2: str, expected_output: float) -> None:
    result = sim_title(title_1, title_2)
    assert result == expected_output


@pytest.mark.parametrize(
    "author_1, author_full_1, author_2, author_full_2, expected_output",
    [
        (
            "perricone bivona jackson vanderheide",
            "perricone, a j and bivona, b j and jackson, f r and vander heide, r s",
            "perricone bivona jackson heide",
            "perricone, a j and bivona, b j and jackson, f r and heide, r s v",
            1.0,
        ),
        ("abdukeyum owen mclennan", "", "abdukeyum owen mclennans", "", 1.0),
        (
            "meng brown ao rowland nordeen banerjee harken",
            "",
            "miki itoh sunaga miura",
            "",
            0.3902439024390244,
        ),
        (
            "chen gong zhong chen zhang wu yang",
            "Chen J. M.Gong X. Q.Zhong J. G.Chen S. C.Zhang G. Y.Wu Z. G.Yang Y. J.",
            "jinming xiaoqi jigen sicong guoyuan zhonggui yongji",
            "Jin-Ming C.Xiao-Qi G.Ji-Gen Z.Si-Cong C.Guo-Yuan Z.Zhong-Gui W.Yong-Ji Y.",
            1.0,
        ),
        (
            "manthei vanwylen",
            "Manthei S. A.Van Wylen D. G.",
            "vanwylen manthei",
            "Van Wylen D. G. L.Manthei S. A.",
            0.9285714285714286,
        ),
        ("jabeen", "JabeenHaleem D.", "haleem", "HaleemD.J.", 1.0),
    ],
)
def test_sim_author(
    author_1: str,
    author_full_1: str,
    author_2: str,
    author_full_2: str,
    expected_output: float,
) -> None:
    result = sim_author(author_1, author_full_1, author_2, author_full_2)
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
def test_sim_year(
    year_1: str,
    year_2: str,
    expected_output: float,
) -> None:
    result = sim_year(year_1, year_2)
    assert result == expected_output


@pytest.mark.parametrize(
    "pages_1, pages_2, expected_output",
    [
        ("1-10", "1-10", 1.0),
        ("1-10", "11-20", 0.6666666666666667),  # TODO
        ("", "", 0),
        ("417-429", "29", 1.0),
    ],
)
def test_sim_page(
    pages_1: str,
    pages_2: str,
    expected_output: float,
) -> None:
    result = sim_page(pages_1, pages_2)
    assert result == expected_output


@pytest.mark.parametrize(
    "pages_1, pages_2, expected_output",
    [
        ("1-10", "11-20", "adjacent"),
        ("1-10", "1-10", ""),
        ("", "", ""),
        ("417-429", "29", ""),
        ("707-715", "716-723", "adjacent"),
        ("369-390", "351-368", "adjacent"),
        ("1-10", "20-30", "non_overlapping"),  # testing non_overlapping condition
    ],
)
def test_page_ranges_adjacent(
    pages_1: str,
    pages_2: str,
    expected_output: str,  # changed from bool to str to match the expected output
) -> None:
    row = {"pages_1": pages_1, "pages_2": pages_2}
    result = page_ranges_adjacent(row)
    assert result == expected_output


@pytest.mark.parametrize(
    "number_1, number_2, expected_output",
    [
        ("1", "1", 1.0),
        ("1", "2", 0.0),
        ("", "", 0.0),
    ],
)
def test_sim_number(
    number_1: str,
    number_2: str,
    expected_output: float,
) -> None:
    result = sim_number(number_1, number_2)
    assert result == expected_output


@pytest.mark.parametrize(
    "volume_1, volume_2, expected_output",
    [
        ("1", "1", 1.0),
        ("1", "2", 0.0),
        ("", "", 0.0),
    ],
)
def test_sim_volume(
    volume_1: str,
    volume_2: str,
    expected_output: float,
) -> None:
    result = sim_volume(volume_1, volume_2)
    assert result == expected_output


@pytest.mark.parametrize(
    "abstract_1, abstract_2, expected_output",
    [
        (
            "chronically administered alprazolam and adinazolam attenuated the hyperactivity of bilaterally bulbectomized rats when placed in a stressful novel environment open field apparatus. these drugs had no effect on the activities of sham operated animals under the same experimental conditions. in other studies in these laboratories clinically effective antidepressant drugs have been shown to have a qualitatively similar effect to alprazolam and adinazolam. chronically administered diazepam and phenobarbitone did not affect the hyperactivity of bulbectomized rats in the open field apparatus. no difference could be found between the behaviour of bulbectomized rats and the sham operated controls when the animals were placed in a novel nonstressful environment hole board apparatus and ymaze. chronic treatment of either the lesioned or nonlesioned animals with alprazolam or adinazolam did not cause any change in the behaviour of the animals in these situations. this suggests that the behaviour of the rat on the hole board is not a reliable indication of antianxiety activity for chronically administered benzodiazepines. when unstarved lesioned and nonlesioned animals were given a choice of five palatable foods for a period of 1 h slight differences in preference for the type of food chosen could be detected. thus unsweetened biscuit cream crackers was the most preferred choice of the sham operated rats while cheese and chocolate were the least preferred. bulbectomized rats showed a more varied food choice with processed meat corned beef and raisins being preferred to biscuit in two out of four groups. chronic treatment with either alprazolam or adinazolam did not appear to affect the food preference.abstract truncated at 250 words",
            "chronically administered alprazolam and adinazolam attenuated the hyperactivity of bilaterally bulbectomized rats when placed in a stressful novel environment open field apparatus. these drugs had no effect on the activities of sham operated animals under the same experimental conditions. in other studies in these laboratories clinically effective antidepressant drugs have been shown to have a qualitatively similar effect to alprazolam and adinazolam. chronically administered diazepam and phenobarbitone did not affect the hyperactivity of bulbectomized rats in the open field apparatus. no difference could be found between the behaviour of bulbectomized rats and the sham operated controls when the animals were placed in a novel nonstressful environment hole board apparatus and ymaze. chronic treatment of either the lesioned or nonlesioned animals with alprazolam or adinazolam did not cause any change in the behaviour of the animals in these situations. this suggests that the behaviour of the rat on the hole board is not a reliable indication of antianxiety activity for chronically administered benzodiazepines. when unstarved lesioned and nonlesioned animals were given a choice of five palatable foods for a period of 1 h slight differences in preference for the type of food chosen could be detected. thus unsweetened biscuit cream crackers was the most preferred choice of the sham operated rats while cheese and chocolate were the least preferred. bulbectomized rats showed a more varied food choice with processed meat corned beef and raisins being preferred to biscuit in two out of four groups. chronic treatment with either alprazolam or adinazolam did not appear to affect the food preference. detailed studies of the effects of chronic alprazolam and adinazolam treatment on the steady state concentrations of noradrenaline dopamine and 5ht in the amygdaloid cortex and midbrain regions showed that only the highest and sedative dose of alprazolam reduced the 5ht concentration in the amygdaloid cortex of the bulbectomized animals. chronically administered diazepam and phenobarbitone also decreased the 5ht concentration while adinazolam was without effect. no change in the turnover of the biogenic amines could be detected following the chronic administration of these drugs. despite this apparent lack of effect of alprazolam and adinazolam on the concentrations of brain monoamines studies by others have shown that those drugs reduce the activity of cortical betaadrenoceptors and enhance those of 5ht receptors in the limbic system. this suggests that the triazolo benzodiazepines have a neuropharmacological profile which is qualitatively similar to that of other atypical antidepressants",
            1.0,
        ),
        ("This is a test abstract.", "This is a test abstract.", 1.0),
        (
            "This is a test abstract.",
            "This is a different abstract.",
            0.8301886792452831,
        ),
        ("", "", 0.0),
    ],
)
def test_sim_abstract(
    abstract_1: str,
    abstract_2: str,
    expected_output: float,
) -> None:
    result = sim_abstract(abstract_1, abstract_2)
    assert result == expected_output
