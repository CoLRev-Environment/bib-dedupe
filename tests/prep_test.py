import numpy as np
import pytest

from bib_dedupe.prep import get_abbrev_container_title
from bib_dedupe.prep import prep_abstract
from bib_dedupe.prep import prep_authors
from bib_dedupe.prep import prep_container_title
from bib_dedupe.prep import prep_isbn
from bib_dedupe.prep import prep_number
from bib_dedupe.prep import prep_pages
from bib_dedupe.prep import prep_title
from bib_dedupe.prep import prep_volume

# flake8: noqa: E501
# pylint: disable=line-too-long


@pytest.mark.parametrize(
    "input_author, expected_output",
    [
        (
            "Carignani, Andrea and Negri, Lorenzo",
            "carigi, andrea and negri, lorenzo",
        ),
        ("Andrea, C. and Lorenzo, N.", "andrea, c and lorenzo, n"),  # note
        (
            "VianaA.F.MacielI.S.DornellesF.N.FigueiredoC.P.SiqueiraJ.M.CamposM.M.CalixtoJ.B.",
            "viana, a f and maciel, i s and dornelles, f n and figueiredo, c p and siqueira, j m and campos, m m and calixto, j b",
        ),
        (
            "Saito S.Shiozaki A.Nakashima A.Sakai M.Sasaki Y.",
            "saito, s and shiozaki, a and nakashima, a and sakai, m and sasaki, y",
        ),
        (
            "Broadley K.Burton A. C.Avgar T.Boutin S.",
            "broadley, k and burton, a c and avgar, t and boutin, s",
        ),
        (
            "Mahi-Birjand M.Yaghoubi S.Abdollahpour-Alitappeh M.Keshtkaran Z.Bagheri N.Pirouzi A.Khatami M.Sineh Sepehr K.Peymani P.Karimzadeh I.",
            "mahibirjand, m and yaghoubi, s and abdollahpouralitappeh, m and keshtkaran, z and bagheri, n and pirouzi, a and khatami, m and sineh sepehr, k and peymani, p and karimzadeh, i",
        ),
        (
            "Vernia FilippoDi Ruscio MirkoStefanelli GianpieroViscido AngeloFrieri GiuseppeLatella Giovanni",
            "vernia, filippo and ruscio, mirko and stefanelli, gianpiero and viscido, angelo and frieri, giuseppe and latella, giovanni",
        ),
        (
            "Jackson JacklynWilliams RebeccaMcEvoy MarkMacDonald-Wicks LesleyPatterson Amanda",
            "jackson, jacklyn and williams, rebecca and mcevoy, mark and macdonaldwicks, lesley and patterson, amanda",
        ),
        ("KAMOUN PP", "kamoun, pp"),
        (
            "Fewtrell LornaMajuru BatsiraiHunter Paul R.",
            "fewtrell, lorna and majuru, batsirai and hunter, paul r",
        ),
        (
            "Durg SharanbasappaDhadde Shivsharan B.Vandal RavichandraShivakumar Badamaranahalli S.Charan Chabbanahalli S.",
            "durg, sharanbasappa and dhadde, shivsharan b and vandal, ravichandra and shivakumar, badamaranahalli s and charan, chabbanahalli s",
        ),
        (
            "Broughton Kathleen M.Sussman Mark A.",
            "broughton, kathleen m and sussman, mark a",
        ),
        (
            "Vila Olaia F.Qu YihuaiVunjak-Novakovic Gordana",
            "vila, olaia f and qu, yihuai and vunjaknovakovic, gordana",
        ),
        (
            "Koop A. C.Bossers G. P. L.Ploegstra M. J.Hagdorn Q. A. J.Berger R. M. F.Sillje H. H. W.Bartelds B.",
            "koop, a c and bossers, g p l and ploegstra, m j and hagdorn, q a j and berger, r m f and sillje, h h w and bartelds, b",
        ),
        (
            "Chan Wai-Jo JocelinMcLachlan Andrew J.Hanrahan Jane R.Harnett Joanna E.",
            "chan, waijo jocelin and mclachlan, andrew j and hanrahan, jane r and harnett, joanna e",
        ),
        ("Verwaijen D.Van Damme R.", "verwaijen, d and vandamme, r"),  #
        (
            "Madersbacher S.Berger I.Ponholzer A.Marszalek M.",
            "madersbacher, s and berger, i and ponholzer, a and marszalek, m",
        ),
        (
            "Bouwense S. A.de Vries M.Schreuder L. T.Olesen S. S.Frokjaer J. B.Drewes A. M.van Goor H.Wilder-Smith O. H.",
            "bouwense, s a and devries, m and schreuder, l t and olesen, s s and frokjaer, j b and drewes, a m and vangoor, h and wildersmith, o h",
        ),
        (
            "Buchaim Daniela VieiraCassaro Claudia VilalvaTadashi Cosin Shindo Joao VitorDella Coletta Bruna BotteonPomini Karina Torresde Oliveira Rosso Marcelie PriscilaGuissoni Campos Leila MariaFerreira Rui Seabra Jr.Barraviera BeneditoBuchaim Rogerio Leone",
            "buchaim, daniela vieira and cassaro, claudia vilalva and tadashi cosin, shindo joao vitor and della coletta, bruna botteon and pomini karina torresde, oliveira rosso marcelie priscila and guissoni campos, leila maria and ferreira rui, seabra jr and barraviera, benedito and buchaim, rogerio leone",
        ),
        (
            "Siqueira-Lima Pollyana S.Silva Juliane C.Quintans Jullyana S. S.Antoniolli Angelo R.Shanmugam SaravananBarreto Rosana S. S.Santos Marcio R. V.Almeida Jackson R. G. S.Bonjardim Leonardo R.Menezes Irwin R. A.Quintans-Junior Lucindo J.",
            "siqueiralima pollyana, s and silva juliane, c and quintans jullyana, s s and antoniolli angelo, r and shanmugam sarava barreto rosana, s s and santos marcio, r v and almeida jackson, r g s and bonjardim leonardo, r and menezes irwin, r a and quintansjunior lucindo, j",
        ),
        ("Agarwal, Ritu", "agarwal, ritu"),
        ("Avgerou, Chrisanthi", "avgerou, chrisanthi"),
        ("Van Bokhoven H.", "vanbokhoven, h"),
        ("Tejedor Jorge A.", "tejedor, jorge a"),
        (
            "PayenJ.-L.IzopetJ.Galindo-MigeotV.Lauwers-CancesV.ZarskiJ.-P.SeigneurinJ.-M.DussaixE.VoigtJ.-J.SelvesJ.BarangeK.PuelJ.PascalJ.-P.",
            "payen, jl and izopet, j and galindomigeot, v and lauwerscances, v and zarski, jp and seigneurin, jm and dussaix, e and voigt, jj and selves, j and barange, k and puel, j and pascal, jp",
        ),
        (
            "ChenJ.-L.ShiB.-Y.XiangH.HouW.-J.QinX.-M.TianJ.-S.DuG.-H.",
            "chen, jl and shi, by and xiang, h and hou, wj and qin, xm and tian, js and du, gh",
        ),
        (
            "HuY.ZhouX.-J.LiuP.DongX.-Z.MuL.-H.ChenY.-B.LiuM.-Y.YuB.-Y.",
            "hu, y and zhou, xj and liu, p and dong, xz and mu, lh and chen, yb and liu, my and yu, by",
        ),
        (
            "Swedish Council on Health Technology Assessment",
            "swedish council on health technology assessment",
        ),
        # ("Kumar BharatReilly M. A.", "kumar, bharat and reilly, m a"),
        (
            "KimS.-H.HanJ.SeogD.-H.ChungJ.-Y.KimN.HongPark Y.LeeS.K.",
            "kim, sh and han, j and seog, dh and chung, jy and kim, n and hong park, y and lee, s k",
        ),
        (
            "van der Grift Edgar A.van der Ree Rodney",
            "vandergrift, edgar a and vanderree, rodney",
        ),
        (
            "Pasker-de Jong PCMWielink Gvan der Valk PGMvan der Wilt GJ",
            "paskerdejong, pc m and wielink, g and vandervalk, pg m and vanderwilt, gj",
        ),
        (
            "de Aguiar Pastore Silva J.Emilia de Souza Fabre M.Waitzberg D. L.",
            "deaguiar pastore, silva j and emilia desouza, fabre m and waitzberg, d l",
        ),
        ("FedotovaI.O.", "fedotova, io"),
        ("", ""),
    ],
)
def test_prep_authors(input_author: str, expected_output: str) -> None:
    result = prep_authors(np.array([input_author]), debug=True)
    print(result[0])
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_title, expected_output",
    [
        (
            "Frontiers in Cellular Neuroscience.9 (DEC) (no pagination) 2015.Article Number: 490.Date of Publication: 22 Dec 2015.",
            "Frontiers in Cellular Neuroscience",
        ),
        (
            "Molecular Psychiatry.9 (3) ()(pp 224) 2004.Date of Publication: March 2004.",
            "Molecular Psychiatry",
        ),
        (
            "Cochrane Database of Systematic Reviews",
            "Cochrane Database of Systematic Reviews",
        ),  # NOTE: important for matching rules
    ],
)
def test_prep_container_title(input_title: str, expected_output: str) -> None:
    result = prep_container_title(np.array([input_title]))
    print(result[0])
    assert np.all(result[0] == expected_output)


@pytest.mark.parametrize(
    "input_title, expected_output",
    [
        ("journal of infection and chemotapy", "j infe chem"),
        ("Frontiers in Cellular Neuroscience", "fron cell neur"),
        ("The Journal of the American Medical Association", "j amer medi asso"),
        ("The New England Journal of Medicine", "new engl j medi"),
        (
            "Frontiers in Cellular Neuroscience.9 (DEC) (no pagination) 2015.Article Number: 490.Date of Publication: 22 Dec 2015.",
            "fron cell neur",
        ),
        ("JOURNAL OF EVIDENCE-BASED DENTAL PRACTICE", "j evid base dent prac"),
        (
            "Cochrane Database of Systematic Reviews",
            "coch data syst revi",
        ),  # NOTE: important for matching rules
    ],
)
def test_get_abbrev_container_title(input_title: str, expected_output: str) -> None:
    result = get_abbrev_container_title(np.array([input_title]))
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_title, expected_output",
    [
        (
            "Comparison of several drugs in treating acute barbiturate depression in the dog. II. Pairs of drugs",
            "comparison of several drugs in treating acute barbiturate depression in the dog 2 pairs of drugs",
        ),
        (
            "Mental and somatic diseases are interlaced in elderly with multiple diseases. [Swedish]",
            "mental and somatic diseases are interlaced in elderly with multiple diseases",
        ),
        (
            "Effect of new polyprenol drug ropren on anxiety-depressive-like behavior: Neurochemical mechanisms of antidepressant effect on Alzheimer type dementia model in rats. [Russian]",
            "effect of new polyprenol drug ropren on anxiety depressive like behavior neurochemical mechanisms of antidepressant effect on alzheimer type dementia model in rats",
        ),
        (
            "Antidepressant Effects of Ketamine Are Not Related to (1)(8)F-FDG Metabolism or Tyrosine Hydroxylase Immunoreactivity in the Ventral Tegmental Area of Wistar Rats",
            "antidepressant effects of ketamine are not related to 18 f fdg metabolism or tyrosine hydroxylase immunoreactivity in the ventral tegmental area of wistar rats",
        ),
        (
            "Antidepressant Effects of Ketamine Are Not Related to 18F-FDG Metabolism or Tyrosine Hydroxylase Immunoreactivity in the Ventral Tegmental Area of Wistar Rats",
            "antidepressant effects of ketamine are not related to 18f fdg metabolism or tyrosine hydroxylase immunoreactivity in the ventral tegmental area of wistar rats",
        ),
        (
            "Effects of low- and high-dose tranylcypromine on [3H]tryptamine binding sites in the rat hippocampus and striatum",
            "effects of low and high dose tranylcypromine on [3h]tryptamine binding sites in the rat hippocampus and striatum",
        ),
        (
            "Update on the diagnosis and treatment of human papillomavirus infection. [Review] [33 refs]",
            "update on the diagnosis and treatment of human papillomavirus infection",
        ),
        (
            "Control of malignant pleural effusing in breast cancer: a randomized trial of bleomycoin versus interferon alfa [abstract no: 134]",
            "control of malignant pleural effusing in breast cancer a randomized trial of bleomycoin versus interferon alfa",
        ),
    ],
)
def test_prep_title(input_title: str, expected_output: str) -> None:
    result = prep_title(np.array([input_title]))
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_volume, expected_output",
    [
        ("9 (3) ()(pp 224) 2004", "9"),
        ("10 (4) ()(pp 300) 2005", "10"),
        ("1)", "1"),
        ("187 ( Pt 1)", "187"),
        ("77 Suppl 1", "77"),
    ],
)
def test_prep_volume(input_volume: str, expected_output: str) -> None:
    result = prep_volume(np.array([input_volume]))
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_number, expected_output",
    [
        ("SUPPL.2", "2"),
        ("Suppl2", "2"),
    ],
)
def test_prep_number(input_number: str, expected_output: str) -> None:
    result = prep_number(np.array([input_number]))
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_pages, expected_output",
    [
        ("S41-S52", "41-52"),
        ("1--10", "1-10"),
        ("100-200", "100-200"),
        ("120-40", "120-140"),
        ("120--40", "120-140"),
        ("pp.12 - 13", "12-13"),
        ("July", ""),
        # TODO:
        # ("II-III", "2-3")
    ],
)
def test_prep_pages(input_pages: str, expected_output: str) -> None:
    result = prep_pages(np.array([input_pages]))
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_abstract, expected_output",
    [
        ("This is a test abstract.", "this is a test abstract"),
        ("Another abstract for testing.", "another abstract for testing"),
        (
            "The present study evaluated 17beta-estradiol (17betaE<inf>2</inf>) (2.5 mg/kg sc) effects on bilateral OBX-induced behavioral changes and oxidative stress. OBX in male Wistar rats produced an increase in lipid peroxidation products and a decline in reduced glutathione (GSH) content and glutathione peroxidase (GSH-Px) activity together with an increase in caspase-3 activity. Additionally OBX triggered changes of behavior such as an enhancement of immobility time in the forced swim test and hyperactivity in the open field test. These changes were reversed by treatment with 17betaE<inf>2</inf> (14 days). Our results reveled that 17betaE<inf>2</inf> has a protective effect against oxidative stress cell damage and behavioral changes induced by OBX and present antidepressant and antianxiety properties. ÃÂ© 2008 Tasset et al publisher and licensee Dove Medical Press Ltd",
            "the present study evaluated 17betaestradiol 17betae 2 2.5 mgkg sc effects on bilateral obxinduced behavioral changes and oxidative stress. obx in male wistar rats produced an increase in lipid peroxidation products and a decline in reduced glutathione gsh content and glutathione peroxidase gshpx activity together with an increase in caspase3 activity. additionally obx triggered changes of behavior such as an enhancement of immobility time in the forced swim test and hyperactivity in the open field test. these changes were reversed by treatment with 17betae 2 14 days. our results reveled that 17betae 2 has a protective effect against oxidative stress cell damage and behavioral changes induced by obx and present antidepressant and antianxiety properties",
        ),
    ],
)
def test_prep_abstract(input_abstract: str, expected_output: str) -> None:
    result = prep_abstract(np.array([input_abstract]))
    print(expected_output)
    print(result[0])
    print(result[0] == expected_output)
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_isbn, expected_output",
    [
        (
            """1469-493X (electronic)
1469-493X""",  #
            "1469-493x (electronic);1469-493x",
        ),
        (
            """0145-6008 (Print)
0145-6008""",
            "0145-6008 (print);0145-6008",
        ),
        ("978-3-16-148410-1", "978-3-16-148410-1"),
    ],
)
def test_prep_isbn(input_isbn: str, expected_output: str) -> None:
    result = prep_isbn(np.array([input_isbn]))
    assert result[0] == expected_output
