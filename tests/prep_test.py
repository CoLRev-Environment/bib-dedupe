import numpy as np
import pytest

from bib_dedupe.prep import prep_abstract
from bib_dedupe.prep import prep_authors
from bib_dedupe.prep import prep_container_title
from bib_dedupe.prep import prep_doi
from bib_dedupe.prep import prep_number
from bib_dedupe.prep import prep_pages
from bib_dedupe.prep import prep_title
from bib_dedupe.prep import prep_volume
from bib_dedupe.prep_schema import fix_schema_misalignments

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
            "viana, a f and maciel, i s and dornelles, f n and figuiredo, c p and siquira, j m and campos, m m and calixto, j b",
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
            "koop, a c and bossers, g p l and plogstra, m j and hagdorn, q a j and berger, r m f and sillje, h h w and bartelds, b",
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
            "bouwense, s a and devries, m and schreuder, l t and olesen, s s and frokjar, j b and drewes, a m and vangoor, h and wildersmith, o h",
        ),
        (
            "Buchaim Daniela VieiraCassaro Claudia VilalvaTadashi Cosin Shindo Joao VitorDella Coletta Bruna BotteonPomini Karina Torresde Oliveira Rosso Marcelie PriscilaGuissoni Campos Leila MariaFerreira Rui Seabra Jr.Barraviera BeneditoBuchaim Rogerio Leone",
            "buchaim, daniela vieira and cassaro, claudia vilalva and tadashi cosin, shindo joao vitor and della coletta, bruna botteon and pomini karina torresde, oliveira rosso marcelie priscila and guissoni campos, leila maria and ferreira rui, seabra jr and barraviera, benedito and buchaim, rogerio leone",
        ),
        (
            "Siqueira-Lima Pollyana S.Silva Juliane C.Quintans Jullyana S. S.Antoniolli Angelo R.Shanmugam SaravananBarreto Rosana S. S.Santos Marcio R. V.Almeida Jackson R. G. S.Bonjardim Leonardo R.Menezes Irwin R. A.Quintans-Junior Lucindo J.",
            "siquiralima pollyana, s and silva juliane, c and quintans jullyana, s s and antoniolli angelo, r and shanmugam saravanan barreto rosana, s s and santos marcio, r v and almeida jackson, r g s and bonjardim leonardo, r and menezes irwin, r a and quintansjunior lucindo, j",
        ),
        ("Agarwal, Ritu", "agarwal, ritu"),
        ("Avgerou, Chrisanthi", "avgerou, chrisanthi"),
        ("Van Bokhoven H.", "vanbokhoven, h"),
        ("Tejedor Jorge A.", "tejedor, jorge a"),
        (
            "PayenJ.-L.IzopetJ.Galindo-MigeotV.Lauwers-CancesV.ZarskiJ.-P.SeigneurinJ.-M.DussaixE.VoigtJ.-J.SelvesJ.BarangeK.PuelJ.PascalJ.-P.",
            "payen, jl and izopet, j and galindomigeot, v and lauwerscances, v and zarski, jp and seigneurin, jm and dussaix, e and voigt, jj and selves, j and barange, k and pul, j and pascal, jp",
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
        ("Anonymous", ""),
        ("", ""),
        (
            "B. Abrahao; P. Parigi; A. Gupta; K. S. Cook",
            "abrahao, b and parigi, p and gupta, a and cook, k s",
        ),
    ],
)
def test_prep_authors(input_author: str, expected_output: str) -> None:
    result = prep_authors(np.array([input_author]), debug=True)
    print(result[0])
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_container_title, expected_output",
    [
        # Journal fields with additional contents
        (
            "Frontiers in Cellular Neuroscience.9 (DEC) (no pagination) 2015.Article Number: 490.Date of Publication: 22 Dec 2015.",
            "fron cell neur",
        ),
        (
            "Molecular Psychiatry.9 (3) ()(pp 224) 2004.Date of Publication: March 2004.",
            "mol psyc",
        ),
        # (
        #     "TheScientificWorldJournal.2014 ()(pp 310821) 2014.Date of Publication: 2014.",
        #     "sci worl j",
        # ),
        (
            "Advances in Alzheimer's Disease.4 ()(pp 163-173) 2015.Date of Publication: 2015.",
            "adv alzh dise",
        ),
        (
            "Progress in Neuro-Psychopharmacology and Biological Psychiatry.65 ()(pp 96-103) 2016.Date of Publication: February 04 2016.",
            "prog neur biol psyc",
        ),
        (
            "Neurologie und Rehabilitation. Conference: Jahreskongress der Deutschen Gesellschaft fur Neurotraumatologie und Klinische Neurorehabilitation e",
            "neur reha conf",
        ),
        # ("Eculizumab for atypical hemolytic-uremic syndrome (New England Journal of Medicine (2009) 360 (542-544))",
        #  "ecul atyp hemo urem synd"),
        (
            "Journal of clinical oncology : official journal of the American Society of Clinical Oncology",
            "j clin onco",
        ),
        (
            "American Journal of Physiology - Heart and Circulatory Physiology",
            "am j phys",
        ),
        ("Proc.Soc.Exp.Biol.Med.", "soc exp biol med"),
        (
            "Proceedings of the Society for Experimental Biology and Medicine.Society for Experimental Biology and Medicine (New York N.Y.).87 (1) ()(pp 54-57) 1954.Date of Publication: 01 Oct 1954.",
            "soc exp biol med",
        ),
        (
            "L'Encephale.20 Spec No 4 ()(pp 619-712) 1994.Date of Publication: Dec 1994.",
            "ence",
        ),
        # Journal translations:
        ("National Medical Journal of China", "nati med j chin"),
        ("Zhonghua Yi Xue Za Zhi", "nati med j chin"),
        # TODO:
        # ("Genetika", "russ j gene"),
        ("Zhong.Nan.Da.Xue.Xue.Bao.Yi.Xue.Ban.", "j cent sout univ"),
        ("Zhongguo Yao Li Xue.Bao.", "acta phar sini"),
        (
            "International journal of cancer. Journal international du cancer",
            "int j canc",
        ),
        ("Chung-Hua Chung Liu Tsa Chih [Chinese Journal of Oncology]", "chin j onco"),
        (
            "Zhonghua jie he he hu xi za zhi = Zhonghua jiehe he huxi zazhi = Chinese journal of tuberculosis and respiratory diseases",
            "chin j tube resp dise",
        ),
        (
            "Chung-Hua Chieh Ho Ho Hu Hsi Tsa Chih Chinese Journal of Tuberculosis & Respiratory Diseases",
            "chin j tube resp dise",
        ),
        (
            "Zhongguo Zhong xi yi jie he za zhi Zhongguo Zhongxiyi jiehe zazhi = Chinese journal of integrated traditional and Western medicine / Zhongguo Zhong xi yi jie he xue hui, Zhongguo Zhong yi yan jiu yuan zhu ban",
            "chin j int trad west med",
        ),
        (
            "Zhong nan da xue xue bao.Yi xue ban = Journal of Central South University.Medical sciences.37 (8) ()(pp 790-795) 2012.Date of Publication: Aug 2012.",
            "j cent sout univ med sci",
        ),
        (
            "Yaoxue Xuebao.49 (2) ()(pp 209-216) 2014.Date of Publication: 12 Feb 2014.",
            "acta phar sini",
        ),
        ("Sichuan.Da.Xue.Xue.Bao.Yi.Xue.Ban.", "j sich univ"),
        ("Zhongguo Yi.Xue.Ke.Xue.Yuan Xue.Bao.", "acta acad med sini"),
        ("Zhen.Ci.Yan.Jiu.", "acup res"),
        (
            "50Th Annual Hawaii International Conference On System Sciences",
            "hawa int conf syst sci",
        ),
        (
            "Proceedings of the 51st Hawaii International Conference on System Sciences",
            "hawa int conf syst sci",
        ),
        ("BMJ-BRITISH MEDICAL JOURNAL", "bmj"),
        ("British Medical Journal", "bmj"),
        ("Ann.N.Y.Acad.Sci.", "ann n y acad sci"),
        ("J Mol Med (Berl)", "j mol med"),
        ("PLoS ONE [Electronic Resource]", "plos one"),
        ("PLoS One", "plos one"),
        (
            "Cochrane Database of Systematic Reviews",
            "coch data syst rev",
        ),  # NOTE: important for matching rules
        ("", ""),
    ],
)
def test_prep_container_title(input_container_title: str, expected_output: str) -> None:
    result = prep_container_title(np.array([input_container_title]))
    assert np.all(result[0] == expected_output)


@pytest.mark.parametrize(
    "input_title, expected_output",
    [
        (
            "Comparison of several drugs in treating acute barbiturate depression in the dog. II. Pairs of drugs",
            "comparison several drugs treating acute barbiturate depression dog 2 pairs drugs",
        ),
        (
            "Mental and somatic diseases are interlaced in elderly with multiple diseases. [Swedish]",
            "mental somatic diseases interlaced elderly multiple diseases",
        ),
        (
            "Effect of new polyprenol drug ropren on anxiety-depressive-like behavior: Neurochemical mechanisms of antidepressant effect on Alzheimer type dementia model in rats. [Russian]",
            "effect new polyprenol drug ropren anxiety depressivelike behavior neurochemical mechanisms antidepressant effect alzheimer type dementia model rats",
        ),
        (
            "Antidepressant Effects of Ketamine Are Not Related to (1)(8)F-FDG Metabolism or Tyrosine Hydroxylase Immunoreactivity in the Ventral Tegmental Area of Wistar Rats",
            "antidepressant effects ketamine not related 18 f fdg metabolism tyrosine hydroxylase immunoreactivity ventral tegmental area wistar rats",
        ),
        (
            "Antidepressant Effects of Ketamine Are Not Related to 18F-FDG Metabolism or Tyrosine Hydroxylase Immunoreactivity in the Ventral Tegmental Area of Wistar Rats",
            "antidepressant effects ketamine not related 18f fdg metabolism tyrosine hydroxylase immunoreactivity ventral tegmental area wistar rats",
        ),
        (
            "Effects of low- and high-dose tranylcypromine on [3H]tryptamine binding sites in the rat hippocampus and striatum",
            "effects low high dose tranylcypromine [3h]tryptamine binding sites rat hippocampus striatum",
        ),
        (
            "Update on the diagnosis and treatment of human papillomavirus infection. [Review] [33 refs]",
            "update diagnosis treatment human papillomavirus infection",
        ),
        (
            "Control of malignant pleural effusing in breast cancer: a randomized trial of bleomycoin versus interferon alfa [abstract no: 134]",
            "control malignant pleural effusing breast cancer randomized trial bleomycoin versus interferon alfa",
        ),
        (
            "Delayed cardioprotective effects of wy-14643 are associated with inhibition of mmp-2 and modulation of bcl-2 family proteins through PPAR-alpha activation in rat hearts subjected to global ischaemia-reperfusion1",
            "delayed cardioprotective effects wy 14643 associated inhibition mmp 2 modulation bcl 2 family proteins through ppar alpha activation rat hearts subjected global ischaemia reperfusion",
        ),
        (
            "Consequences of brief ischemia: stunning preconditioning and their clinical implications: part 1",
            "consequences brief ischemia stunning preconditioning clinical implications part 1",
        ),
        (
            "PHOTOBIOMODULATION IN PERIODONTOLOGY AND IMPLANT DENTISTRY: PART II",
            "photobiomodulation periodontology implant dentistry part 2",
        ),
        (
            "Protein kinase C and G(i/o) proteins are involved in adenosine- and ischemic preconditioning-mediated renal protection",
            "protein kinase c g 1 o proteins involved adenosine ischemic preconditioning mediated renal protection",
        ),
        (
            "Crowdwork Platforms - Juxtaposing Centralized and Decentralized Governance",
            "crowdwork platforms juxtaposing centralized decentralized governance",
        ),
        (
            """Reperfusion and postconditioning in acute ST segment elevation myocardial infarction. A new paradigm for the treatment of acute myocardial infarction. From bench to bedside?. Spanish
De la reperfusion al post-acondicionamiento del miocardio con isquemia prolongada. Nuevo paradigma terapeutico de los sindromes coronarios agudos con elevacion del segmento ST? De lo basico a lo clinico""",
            "reperfusion postconditioning acute st segment elevation myocardial infarction new paradigm treatment acute myocardial infarction bench bedside",
        ),
        ("Donor heart preservation. Japanese", "donor heart preservation"),
        (
            "Protective effects of renal ischemic preconditioning and adenosine pretreatment: role of A(1) and A(3) receptors",
            "protective effects renal ischemic preconditioning adenosine pretreatment role a1 a3 receptors",
        ),
        (
            "Protective effects of renal ischemic preconditioning and adenosine pretreatment: Role of A1 and A3 receptors",
            "protective effects renal ischemic preconditioning adenosine pretreatment role a1 a3 receptors",
        ),
        (
            "A(1) or A(3) adenosine receptors induce late preconditioning against infarction in conscious rabbits by different mechanisms",
            "a1 a3 adenosine receptors induce late preconditioning against infarction conscious rabbits different mechanisms",
        ),
        (
            "Study of two new GABA-ergics (GABA-linoleamide and GABA-steatamide). On two experimental models of depression",
            "study 2 new gaba ergics gaba linoleamide gaba steatamide 2 experimental models depression",
        ),
        (
            "Adenosine administration produces an antidepressant-like effect in mice: evidence for the involvement of A1 and A2A receptors",
            "adenosine administration produces antidepressantlike effect mice evidence involvement a1 a2a receptors",
        ),
        (
            "WITHDRAWN. ANTIVIRAL TREATMENT FOR BELL'S PALSY (IDIOPATHIC FACIAL PARALYSIS)",
            "antiviral treatment bell s palsy",
        ),
        (
            "WITHDRAWN: IMMUNOGLOBULIN FOR PREVENTING RESPIRATORY SYNCYTIAL VIRUS INFECTION",
            "immunoglobulin preventing respiratory syncytial virus infection",
        ),
        (
            "EFFECT OF IMMOBILISATION ON NEUROMUSCULAR FUNCTION IN VIVO IN HUMANS: A SYSTEMATIC REVIEW (VOL 49 PG 931 2019)",
            "effect immobilisation neuromuscular function vivo humans systematic review",
        ),
        (
            "Tamoxifen antagonizes the effects of ovarian hormones to induce anxiety and depression-like behavior in rats",
            "tamoxifen antagonizes effects ovarian hormones induce anxiety depressionlike behavior rats",
        ),
        (
            "TAN-67 a 1-opioid receptor agonist reduces infarct size via activation of G(i/o) proteins and K(ATP) channels",
            # TODO : ideally, 67 and 1 should not be joined...
            "tan 671 opioid receptor agonist reduces infarct size via activation g 1 o proteins k atp channels",
        ),
        (
            "BRAIN BENZODIAZEPINE RECEPTORS IN HUMANS AND RATS WITH ALCOHOL ADDICTION. RUSSIAN",
            "brain benzodiazepine receptors humans rats alcohol addiction",
        ),
        (
            "Proceedings: Methylamphetamine withdrawal as a model for the depressive state: antagonism of post-amphetamine depression by imipramine",
            "methylamphetamine withdrawal model depressive state antagonism postamphetamine depression imipramine",
        ),
        (
            "HPV testing and monitoring of women after treatment of CIN 3: review of the literature and meta-analysis (Provisional abstract)",
            "hpv testing monitoring women after treatment cin 3 review literature meta analysis",
        ),
        (
            "REPRINT OF: FMRI STUDIES OF SUCCESSFUL EMOTIONAL MEMORY ENCODING: A QUANTITATIVE META-ANALYSIS",
            "fmri studies successful emotional memory encoding quantitative meta analysis",
        ),
        (
            "Mode of action of alkylating agents using a ciliate protozoan as a model system: Part III--Effects of metepa on cell division & DNA synthesis in the ciliate Belpharisma intermedium",
            "mode action alkylating agents using ciliate protozoan model system part 3 effects metepa cell division dna synthesis ciliate belpharisma intermedium",
        ),
        # (
        #     "Behavioral effects of acute sublethal exposure to dimethoate on wood mice Apodemus sylvaticus: II--Field studies on radio-tagged mice in a cereal ecosystem",
        #     "behavioral effects acute sublethal exposure dimethoate wood mice apodemus sylvaticus 2 field studies radio tagged mice cereal ecosystem",
        # ),
        # ("Eculizumab for atypical hemolytic-uremic syndrome (New England Journal of Medicine (2009) 360 (542-544))",
        #  "TODO")
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
        (
            "Supplement. Kongressband. Deutsche Gesellschaft fur Chirurgie. Kongress. 115",
            "115",
        ),
        ("SUPPL", ""),
        ("(Jul)", ""),
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
        ("6 51-6", "6"),
        ("La Semaine des hopitaux", ""),
        ("Shariqah (United Arab Emirates", ""),
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
        ("v-vii", "5-7"),
        ("(1) (no pagination)", "1"),
        ("08-Nov", "8-11"),
        ("822-822", "822")
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
        (
            "Background: Deep hypothermic circulatory arrest (DHCA) causes myocyte injury as a consequence of ischemia and reperfusion. Previous studies have shown that hypoxia or hypoxia-mimetic agents (cobalt chloride CoCl<sub>2</sub> or deferoxamine DFX) limit myocyte necrosis by upregulating the transcription factor hypoxia-inducible factor. However it remains unknown whether these agents attenuate myocardial apoptosis after DHCA. This study tested the hypotheses (1) that hypoxia DFX or CoCl<sub>2</sub> preconditioning attenuates myocardial apoptosis during DHCA; and (2) that the protective mechanism involves the altered expression of apoptosis regulatory proteins pAkt (antiapoptotic) Bcl-2 (antiapoptotic) and Bax (proapoptotic). Methods: Anesthetized neonatal piglets were randomly assigned to four groups (n = 6 in a group): control (NaCl injection); hypoxia (pO<sub>2</sub> of 30 to 40 mm Hg for 3 hours); DFX injection; or CoCl<sub>2</sub> injection. Twenty-four hours later the animals underwent cardiopulmonary bypass (CPB) and 110 minutes of DHCA. One week after CPB percentage of apoptotic myocytes (terminal deoxynucleotidyl transferase-mediated dUTP nick end labeling TUNEL assay) and expression of the pAKT Bcl-2 and Bax were assessed by Western blot. Results: Although preconditioning with hypoxia and DFX failed to show a protective benefit CoCl<sub>2</sub> pretreatment significantly attenuated myocardial apoptosis (9.3% +/- 4.1%) versus controls (33.8% +/- 9.7% p = 0.042). That was associated with increased myocardial pAkt expression (0.19 +/- 0.006 in CoCl<sub>2</sub> versus 0.12 +/- 0.008 in control p < 0.001). The expression of Bcl-2 was also significantly higher in the CoCl<sub>2</sub> group (0.15 +/- 0.02) versus control (0.11 +/- 0.01 p = 0.007) whereas Bax expression was lower (0.34 +/- 0.04 versus 0.54 +/- 0.03 for control p < 0.001). Conclusions: Preconditioning with CoCl<sub>2</sub> before prolonged DHCA in neonatal piglets attenuates myocardial apoptosis by mechanisms involving phosphorylation of Akt upregulation of the antiapoptotic protein Bcl-2 and decreased expression of the proapoptotic protein Bax. 2006 The Society of Thoracic Surgeons.",
            "deep hypothermic circulatory arrest dhca causes myocyte injury as a consequence of ischemia and reperfusion. previous studies have shown that hypoxia or hypoxiamimetic agents cobalt chloride cocl 2 or deferoxamine dfx limit myocyte necrosis by upregulating the transcription factor hypoxiainducible factor. however it remains unknown whether these agents attenuate myocardial apoptosis after dhca. this study tested the hypotheses 1 that hypoxia dfx or cocl 2 preconditioning attenuates myocardial apoptosis during dhca and 2 that the protective mechanism involves the altered expression of apoptosis regulatory proteins pakt antiapoptotic bcl2 antiapoptotic and bax proapoptotic. methods anesthetized neonatal piglets were randomly assigned to four groups n 6 in a group control nacl injection hypoxia po 2 of 30 to 40 mm hg for 3 hours dfx injection or cocl 2 injection. twentyfour hours later the animals underwent cardiopulmonary bypass cpb and 110 minutes of dhca. one week after cpb percentage of apoptotic myocytes terminal deoxynucleotidyl transferasemediated dutp nick end labeling tunel assay and expression of the pakt bcl2 and bax were assessed by western blot. results although preconditioning with hypoxia and dfx failed to show a protective benefit cocl 2 pretreatment significantly attenuated myocardial apoptosis 9.3 4.1 versus controls 33.8 9.7 p 0.042. that was associated with increased myocardial pakt expression 0.19 0.006 in cocl 2 versus 0.12 0.008 in control p 2 group 0.15 0.02 versus control 0.11 0.01 p 0.007 whereas bax expression was lower 0.34 0.04 versus 0.54 0.03 for control p 2 before prolonged dhca in neonatal piglets attenuates myocardial apoptosis by mechanisms involving phosphorylation of akt upregulation of the antiapoptotic protein bcl2 and decreased expression of the proapoptotic protein bax",
        ),
        (
            "Background. Ischemic preconditioning (IPC) reduces infarct size in experimental preparations. IPC however is not without detrimental effects We studied amrinone as a possible alternative to IPC. Methods. Isolated perfused rabbit hearts were given a 5-minute infusion of 10 mumol/L amrinone followed by a 5-minute washout (n = 6). The anterior descending artery was then occluded for 1 hour and reperfused for 1 hour. Six hearts underwent IPC with two episodes of 5-minute global ischemia followed by 5-minute reperfusion before LAD occlusion; eight control hearts received no preconditioning. Left ventricular pressure and ischemic zone epicardial monophasic action potentials were continuously monitored. Results. IPC but not amrinone reduced peak pressure before anterior descending artery occlusion. Peak pressure fell significantly during ischemia and reperfusion in all hearts. End diastolic pressure rose significantly during reperfusion in control and IPC hearts but not in amrinone hearts. Action potentials shortened during ischemia in all hearts. They returned to preocclusion values in control hearts but lasted beyond preocclusion values in IPC and amrinone hearts. Both the incidences of ventricular fibrillation and infarct size were significantly reduced in amrinone hearts but not in IPC hearts. Conclusions. Amrinone is not only a useful inotropic agent but is also a superior preconditioning agent when compared to IPC. (C) 2000 by The Society of Thoracic Surgeons.",
            "ischemic preconditioning ipc reduces infarct size in experimental preparations. ipc however is not without detrimental effects we studied amrinone as a possible alternative to ipc. methods. isolated perfused rabbit hearts were given a 5minute infusion of 10 mumoll amrinone followed by a 5minute washout n 6. the anterior descending artery was then occluded for 1 hour and reperfused for 1 hour. six hearts underwent ipc with two episodes of 5minute global ischemia followed by 5minute reperfusion before lad occlusion eight control hearts received no preconditioning. left ventricular pressure and ischemic zone epicardial monophasic action potentials were continuously monitored. results. ipc but not amrinone reduced peak pressure before anterior descending artery occlusion. peak pressure fell significantly during ischemia and reperfusion in all hearts. end diastolic pressure rose significantly during reperfusion in control and ipc hearts but not in amrinone hearts. action potentials shortened during ischemia in all hearts. they returned to preocclusion values in control hearts but lasted beyond preocclusion values in ipc and amrinone hearts. both the incidences of ventricular fibrillation and infarct size were significantly reduced in amrinone hearts but not in ipc hearts. conclusions. amrinone is not only a useful inotropic agent but is also a superior preconditioning agent when compared to ipc",
        ),
        (
            "We have studied vertical synaptic pathways in two cytoarchitectonically distinct areas of rat neocortex--the granular primary somatosensory (SI) area and the agranular primary motor (MI) area--and tested their propensity to generate long-term potentiation (LTP) long-term depression (LTD) and related forms of synaptic plasticity. Extracellular and intracellular responses were recorded in layer II/III of slices in vitro while stimulating in middle cortical layers (in or around layer IV). Under control conditions 5 Hz theta-burst stimulation produced LTP in the granular area but not in the agranular area. Agranular cortex did generate short-term potentiation that decayed within 20 min. Varying the inter-burst frequency from 2 Hz to 10 Hz reliably yielded LTP of 21-34% above control levels in granular cortex but no lasting changes were induced in agranular cortex. However the agranular cortex was capable of generating LTP if a GABAA receptor antagonist was applied locally at the recording site during the induction phase. In contrast to LTP an identical form of homosynaptic LTD could be induced in both granular and agranular areas by applying low frequency stimulation (1 Hz for 15 min) to the middle layers. Under control conditions both LTP and LTD were synapse-specific; theta-burst or low-frequency stimulation in the vertical pathway did not induce changes in responses to stimulation of a layer II/III horizontal pathway. Application of the NMDA receptor antagonist D-2-amino-5-phosphonovaleric acid (AP5) blocked the induction of both LTP and LTD in granular and agranular cortex. In the presence of AP5 low-frequency conditioning stimuli yielded a short-term depression in both areas that decayed within 10-15 min. Nifedipine which blocks L-type voltage-sensitive calcium channels slightly depressed the magnitudes of LTP and LTD but did not abolish them. Synaptic responses evoked during theta-burst stimulation were strikingly different in granular and agranular areas. Responses in granular cortex were progressively facilitated during each sequence of 10 theta-bursts and from sequence-to-sequence; in contrast responses in agranular cortex were stable during an entire theta-burst tetanus. The results suggest that vertical pathways in primary somatosensory cortex and primary motor cortex express several forms of synaptic plasticity. They were equally capable of generating LTD but the pathways in somatosensory cortex much more reliably generated LTP unless inhibition was reduced. LTP may be more easily produced in sensory cortex because of the pronounced synaptic facilitation that occurs there during repetitive stimulation of the induction phase.(ABSTRACT TRUNCATED AT 400 WORDS)",
            "we have studied vertical synaptic pathways in two cytoarchitectonically distinct areas of rat neocortexthe granular primary somatosensory si area and the agranular primary motor mi areaand tested their propensity to generate longterm potentiation ltp longterm depression ltd and related forms of synaptic plasticity. extracellular and intracellular responses were recorded in layer iiiii of slices in vitro while stimulating in middle cortical layers in or around layer iv. under control conditions 5 hz thetaburst stimulation produced ltp in the granular area but not in the agranular area. agranular cortex did generate shortterm potentiation that decayed within 20 min. varying the interburst frequency from 2 hz to 10 hz reliably yielded ltp of 2134 above control levels in granular cortex but no lasting changes were induced in agranular cortex. however the agranular cortex was capable of generating ltp if a gabaa receptor antagonist was applied locally at the recording site during the induction phase. in contrast to ltp an identical form of homosynaptic ltd could be induced in both granular and agranular areas by applying low frequency stimulation 1 hz for 15 min to the middle layers. under control conditions both ltp and ltd were synapsespecific thetaburst or lowfrequency stimulation in the vertical pathway did not induce changes in responses to stimulation of a layer iiiii horizontal pathway. application of the nmda receptor antagonist d2amino5phosphonovaleric acid ap5 blocked the induction of both ltp and ltd in granular and agranular cortex. in the presence of ap5 lowfrequency conditioning stimuli yielded a shortterm depression in both areas that decayed within 1015 min. nifedipine which blocks ltype voltagesensitive calcium channels slightly depressed the magnitudes of ltp and ltd but did not abolish them. synaptic responses evoked during thetaburst stimulation were strikingly different in granular and agranular areas. responses in granular cortex were progressively facilitated during each sequence of 10 thetabursts and from sequencetosequence in contrast responses in agranular cortex were stable during an entire thetaburst tetanus. the results suggest that vertical pathways in primary somatosensory cortex and primary motor cortex express several forms of synaptic plasticity. they were equally capable of generating ltd but the pathways in somatosensory cortex much more reliably generated ltp unless inhibition was reduced. ltp may be more easily produced in sensory cortex because of the pronounced synaptic facilitation that occurs there during repetitive stimulation of the induction phase",
        ),
    ],
)
def test_prep_abstract(input_abstract: str, expected_output: str) -> None:
    result = prep_abstract(np.array([input_abstract]))
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "input_doi, expected_output",
    [
        ("ARTN 32\n10.1186/s13229-017-0138-8", "101186/s13229_017_0138_8"),
        (
            "10.1097/FJC.0b013e3182776c28. [doi];00005344-201301000-00008 [pii]",
            "101097/fjc0b013e3182776c28",
        ),
        # the replacement seems to be a common error (which is hard to explain given that dois are not case sensitive, but -/_ are considered different)
        ("10.1007/82-2012-287", "101007/82_2012_287"),
    ],
)
def test_prep_doi(input_doi: str, expected_output: str) -> None:
    result = prep_doi(np.array([input_doi]))
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "case",
    [
        {
            "id": "vol_issue_no_pagination",
            "row": {
                "volume": "7 (1) (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {"volume": "7", "number": "1", "pages": "", "year": ""},
        },
        {
            "id": "vol_no_pagination_only",
            "row": {
                "volume": "5 (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {"volume": "5", "number": "", "pages": "", "year": ""},
        },
        {
            "id": "year_in_volume_no_pagination",
            "row": {
                "volume": "2011 (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {"volume": "", "number": "", "pages": "", "year": "2011"},
        },
        {
            "id": "year_in_volume_with_issue_no_pagination",
            "row": {
                "volume": "2017 (10) (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {"volume": "", "number": "10", "pages": "", "year": "2017"},
        },
        {
            "id": "issue_only_no_pagination_in_volume",
            "row": {
                "volume": "(4) (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {"volume": "", "number": "4", "pages": "", "year": ""},
        },
        {
            "id": "issue_only_no_pagination_in_pages",
            "row": {
                "volume": "",
                "number": "",
                "pages": "(1) (no pagination)",
                "year": "",
            },
            "expected": {"volume": "", "number": "1", "pages": "", "year": ""},
        },
        {
            "id": "supplement_in_volume_parentheses",
            "row": {
                "volume": "8 (SUPPL. 1) (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {"volume": "8", "number": "SUPPL.1", "pages": "", "year": ""},
        },
        {
            "id": "supplement_word_form",
            "row": {
                "volume": "12 (Supplement 1)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {
                "volume": "12",
                "number": "Supplement 1",
                "pages": "",
                "year": "",
            },
        },
        {
            "id": "special_issue_code_s1",
            "row": {"volume": "52 (S1)", "number": "", "pages": "", "year": ""},
            "expected": {"volume": "52", "number": "S1", "pages": "", "year": ""},
        },
        {
            "id": "issue_range",
            "row": {"volume": "7 (2-3)", "number": "", "pages": "", "year": ""},
            "expected": {"volume": "7", "number": "2-3", "pages": "", "year": ""},
        },
        {
            "id": "alphanumeric_volume",
            "row": {"volume": "82B (6)", "number": "", "pages": "", "year": ""},
            "expected": {"volume": "82B", "number": "6", "pages": "", "year": ""},
        },
        {
            "id": "part_marker",
            "row": {"volume": "42 (4 PART 2)", "number": "", "pages": "", "year": ""},
            "expected": {"volume": "42", "number": "4 PART 2", "pages": "", "year": ""},
        },
        {
            "id": "pt_marker",
            "row": {"volume": "187 ( Pt 1)", "number": "", "pages": "", "year": ""},
            "expected": {"volume": "187", "number": "Pt 1", "pages": "", "year": ""},
        },
        {
            "id": "month_in_parentheses_is_ignored",
            "row": {
                "volume": "8 (JAN) (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {"volume": "8", "number": "", "pages": "", "year": ""},
        },
        {
            "id": "month_with_year_in_parentheses_is_ignored",
            "row": {
                "volume": "6 (FEBRUARY 2012) (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {"volume": "6", "number": "", "pages": "", "year": ""},
        },
        {
            "id": "issue_only_monthish_is_dropped",
            "row": {
                "volume": "(7 JUL) (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            "expected": {"volume": "", "number": "", "pages": "", "year": ""},
        },
        {
            "id": "no_pagination_alone_is_cleared",
            "row": {"volume": "(no pagination)", "number": "", "pages": "", "year": ""},
            "expected": {"volume": "", "number": "", "pages": "", "year": ""},
        },
        {
            "id": "nested_parens_weirdness",
            "row": {
                "volume": "18 (2(2)) (no pagination)",
                "number": "",
                "pages": "",
                "year": "",
            },
            # We do NOT try to fully interpret "2(2)" – but we should at least keep volume and move token if number empty
            "expected": {"volume": "18", "number": "2(2)", "pages": "", "year": ""},
        },
    ],
)
def test_fix_schema_misalignments(case: dict) -> None:
    import pandas as pd

    split_df = pd.DataFrame([case["row"]])

    # function mutates split_df in-place
    fix_schema_misalignments(split_df)

    for field, expected_value in case["expected"].items():
        assert split_df.loc[0, field] == expected_value, (
            f"{case['id']} failed for field '{field}': "
            f"expected '{expected_value}', got '{split_df.loc[0, field]}'"
        )
