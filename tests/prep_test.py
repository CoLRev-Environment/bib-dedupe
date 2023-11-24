import numpy as np
import pytest

from bib_dedupe.prep import prep_abstract
from bib_dedupe.prep import prep_authors
from bib_dedupe.prep import prep_container_title
from bib_dedupe.prep import prep_doi
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
            "carignani, andrea and negri, lorenzo",
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
            "siqueiralima pollyana, s and silva juliane, c and quintans jullyana, s s and antoniolli angelo, r and shanmugam saravanan barreto rosana, s s and santos marcio, r v and almeida jackson, r g s and bonjardim leonardo, r and menezes irwin, r a and quintansjunior lucindo, j",
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
            "fron cell neur",
        ),
        (
            "Molecular Psychiatry.9 (3) ()(pp 224) 2004.Date of Publication: March 2004.",
            "mole psyc",
        ),
        (
            "50Th Annual Hawaii International Conference On System Sciences",
            "hawa inte conf syst scie",
        ),
        ("J Mol Med (Berl)", "j mol med"),
        (
            "Cochrane Database of Systematic Reviews",
            "coch data syst revi",
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
        (
            "Delayed cardioprotective effects of wy-14643 are associated with inhibition of mmp-2 and modulation of bcl-2 family proteins through PPAR-alpha activation in rat hearts subjected to global ischaemia-reperfusion1",
            "delayed cardioprotective effects of wy 14643 are associated with inhibition of mmp 2 and modulation of bcl 2 family proteins through ppar alpha activation in rat hearts subjected to global ischaemia reperfusion",
        ),
        (
            "Consequences of brief ischemia: stunning preconditioning and their clinical implications: part 1",
            "consequences of brief ischemia stunning preconditioning and their clinical implications part 1",
        ),
        (
            "Protein kinase C and G(i/o) proteins are involved in adenosine- and ischemic preconditioning-mediated renal protection",
            "protein kinase c and g i o proteins are involved in adenosine and ischemic preconditioning mediated renal protection",
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
        ("6 51-6", "6"),
    ],
)
def test_prep_volume(input_volume: str, expected_output: str) -> None:
    result = prep_volume(np.array([input_volume]))
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_number, expected_output",
    [("SUPPL.2", "2"), ("Suppl2", "2"), ("6 51-6", "6")],
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
        ("v-vii", "5-7")
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
        ("Another abstract for testing. The Authors.", "another abstract for testing"),
        (
            "Another abstract for testing. 2013 The Authors.",
            "another abstract for testing",
        ),
        (
            "The present study evaluated 17beta-estradiol (17betaE<inf>2</inf>) (2.5 mg/kg sc) effects on bilateral OBX-induced behavioral changes and oxidative stress. OBX in male Wistar rats produced an increase in lipid peroxidation products and a decline in reduced glutathione (GSH) content and glutathione peroxidase (GSH-Px) activity together with an increase in caspase-3 activity. Additionally OBX triggered changes of behavior such as an enhancement of immobility time in the forced swim test and hyperactivity in the open field test. These changes were reversed by treatment with 17betaE<inf>2</inf> (14 days). Our results reveled that 17betaE<inf>2</inf> has a protective effect against oxidative stress cell damage and behavioral changes induced by OBX and present antidepressant and antianxiety properties. ÃÂ© 2008 Tasset et al publisher and licensee Dove Medical Press Ltd",
            "the present study evaluated 17betaestradiol 17betae 2 2.5 mgkg sc effects on bilateral obxinduced behavioral changes and oxidative stress. obx in male wistar rats produced an increase in lipid peroxidation products and a decline in reduced glutathione gsh content and glutathione peroxidase gshpx activity together with an increase in caspase3 activity. additionally obx triggered changes of behavior such as an enhancement of immobility time in the forced swim test and hyperactivity in the open field test. these changes were reversed by treatment with 17betae 2 14 days. our results reveled that 17betae 2 has a protective effect against oxidative stress cell damage and behavioral changes induced by obx and present antidepressant and antianxiety properties",
        ),
        (
            "Many Veterans exposed to physical and psychological trauma experience symptoms of posttraumatic stress disorder (PTSD). As the etiology of PTSD symptoms is complex a better understanding of the underlying biological mechanisms may improve preventative care and treatment for PTSD. Recent findings from the fields of neuroimaging and epigenetics offer important insights into the potential brain structures and biochemical pathways of modified gene expression associated with PTSD. We combined neuroimaging and epigenetic measures to assess current PTSD symptoms by measuring overall hippocampal volume and methylation of the glucocorticoid receptor (GR) gene (promoter region). Multiple regression analyses indicated that the hippocampal volume/GR methylation interaction was a predictor of PTSD symptoms. Our findings suggest that neuroimaging and epigenetic measures contribute interactively to PTSD symptoms. Incorporation of these metrics may aid in the identification and treatment of PTSD patients. Copyright This is an open access article free of all copyright and may be freely reproduced distributed transmitted modified built upon or otherwise used by anyone for any lawful purpose. The work is made available under the Creative Commons CC0 public domain dedication.",
            "many veterans exposed to physical and psychological trauma experience symptoms of posttraumatic stress disorder ptsd. as the etiology of ptsd symptoms is complex a better understanding of the underlying biological mechanisms may improve preventative care and treatment for ptsd. recent findings from the fields of neuroimaging and epigenetics offer important insights into the potential brain structures and biochemical pathways of modified gene expression associated with ptsd. we combined neuroimaging and epigenetic measures to assess current ptsd symptoms by measuring overall hippocampal volume and methylation of the glucocorticoid receptor gr gene promoter region. multiple regression analyses indicated that the hippocampal volumegr methylation interaction was a predictor of ptsd symptoms. our findings suggest that neuroimaging and epigenetic measures contribute interactively to ptsd symptoms. incorporation of these metrics may aid in the identification and treatment of ptsd patients",
        ),
        (
            "Recent evidence has suggested that activation of AMP-activated protein kinase (AMPK) induced by shortterm caloric restriction (CR) protects against myocardial ischemia-reperfusion (I/R) injury. Because AMPK plays a central role in regulating energy metabolism we investigated whether alterations in cardiac energy metabolism contribute to the cardioprotective effects induced by CR. Hearts from control or short-term CR mice were subjected to ex vivo I/R and metabolism as well as post-ischemic functional recovery was measured. Even in the presence of elevated levels of fatty acids CR significantly improved recovery of cardiac function following ischemia. While rates of fatty acid oxidation or glycolysis from exogenous glucose were similar between groups improved functional recovery post-ischemia in CR hearts was associated with high rates of glucose oxidation during reperfusion compared to controls. Consistent with CR improving energy supply hearts from CR mice had increased ATP levels as well as lower AMPK activity at the end of reperfusion compared to controls. Furthermore in agreement with the emerging concept that CR is a non-conventional form of pre-conditioning we observed a significant increase in phosphorylation of Akt and Erk1/2 at the end of reperfusion. These data also suggest that activation of the reperfusion salvage kinase (RISK) pathway also contributes to the beneficial effects of CR in reducing post-ischemia contractile dysfunction. These findings also suggest that short-term CR improves post-ischemic recovery by promoting glucose oxidation and activating the RISK pathway. As such pre-operative CR may be a clinically relevant strategy for increasing ischemic tolerance of the heart. Springer-Verlag 2010.",
            "recent evidence has suggested that activation of ampactivated protein kinase ampk induced by shortterm caloric restriction cr protects against myocardial ischemiareperfusion ir injury. because ampk plays a central role in regulating energy metabolism we investigated whether alterations in cardiac energy metabolism contribute to the cardioprotective effects induced by cr. hearts from control or shortterm cr mice were subjected to ex vivo ir and metabolism as well as postischemic functional recovery was measured. even in the presence of elevated levels of fatty acids cr significantly improved recovery of cardiac function following ischemia. while rates of fatty acid oxidation or glycolysis from exogenous glucose were similar between groups improved functional recovery postischemia in cr hearts was associated with high rates of glucose oxidation during reperfusion compared to controls. consistent with cr improving energy supply hearts from cr mice had increased atp levels as well as lower ampk activity at the end of reperfusion compared to controls. furthermore in agreement with the emerging concept that cr is a nonconventional form of preconditioning we observed a significant increase in phosphorylation of akt and erk12 at the end of reperfusion. these data also suggest that activation of the reperfusion salvage kinase risk pathway also contributes to the beneficial effects of cr in reducing postischemia contractile dysfunction. these findings also suggest that shortterm cr improves postischemic recovery by promoting glucose oxidation and activating the risk pathway. as such preoperative cr may be a clinically relevant strategy for increasing ischemic tolerance of the heart",
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
            "1469-493x",
        ),
        (
            """0145-6008 (Print)
0145-6008""",
            "0145-6008",
        ),
        ("2041-1723 (Electronic)\n2041-1723 (Linking)", "2041-1723"),
        ("978-3-16-148410-1", "978-3-16-148410-1"),
    ],
)
def test_prep_isbn(input_isbn: str, expected_output: str) -> None:
    result = prep_isbn(np.array([input_isbn]))
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_doi, expected_output",
    [
        ("ARTN 32\n10.1186/s13229-017-0138-8", "10.1186/s13229-017-0138-8"),
    ],
)
def test_prep_doi(input_doi: str, expected_output: str) -> None:
    result = prep_doi(np.array([input_doi]))
    assert result[0] == expected_output
