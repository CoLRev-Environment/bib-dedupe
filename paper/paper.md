---
title: 'BibDedupe: An Open-Source Python Library for Bibliographic Record Deduplication'
tags:
- Python
- Bibliographic Records
- Deduplication
- Data Preprocessing
- Blocking
authors:
- name: Gerit Wagner
orcid: "0000-0003-3926-7717"
affiliation: Otto-Friedrich Universität Bamberg
date: "2023-11-20"
bibliography: paper.bib

---

**TODO: update tables etc. with latest results from the evaluations**

# Summary

BibDedupe is a Python library developed for bibliographic record deduplication in meta-analysis and research synthesis. It is constructed with a focus on four requirements:
(1) **Zero false positives**: The primary objective is to prevent incorrectly merging distinct entries. This focus on zero false positives is crucial to ensure trustworthiness and prevent biased conclusions in the analysis.
(2) **Reproducibility**: BibDedupe implements fixed rules to produce consistent results, in line with the scientific standard of reproducibility.
(3) **Efficiency**: The library is also tuned for low false-negative rates and rapid processing, to ensure scalability of the duplicate identification process.
(4) **Continuous evaluation and improvement**: It is continuously evaluated on over 160,000 records from 10 datasets to ensure its effectiveness, especially in follow-up refinements.
Unlike general-purpose deduplication tools, BibDedupe is specifically designed for the unique requirements of bibliographic data in meta-analysis and research synthesis.
In this context, BibDedupe aims to provide a Python library that significantly improves the effectiveness and efficiency of duplicate identification, potentially benefitting standalone review papers across scientific disciplines.

<!-- 
JOSS welcomes submissions from broadly diverse research areas. For this reason, we require that authors include in the paper some sentences that explain the software functionality and domain of use to a non-specialist reader. We also require that authors explain the research applications of the software. The paper should be between 250-1000 words. Authors submitting papers significantly longer than 1000 words may be asked to reduce the length of their paper.
-->

# Statement of Need

Handling duplicates is a critical step in meta-analysis and research synthesis [@HarrerEtAl2021], given that errors in this step can directly affect conclusions [@Wood2008].
Prior research has invested considerable efforts to evaluate duplicate identification software for bibliographic data [@BramerEtAl2016;@KoumarelasEtAl2020;@RathboneEtAl2015;@BinetteSteorts2022].
While methodologists have repeatedly cautioned against the risk of treating identical studies independently when they are published in different papers [@Senn2009;@FairfieldEtAl2017], the risk of erroneously classifying papers as duplicates has arguably received less attention.
However, once removed from the process, it is rarely possible to recover false positives, or to quantify and correct their effect on meta-analytic results.
As such, preventing false positives is of critical importance, while false negatives can be detected and merged in the subsequent screening and analysis steps [@McLoughlin2022].
<!-- The requirements for duplicate identification software therefore include (1) zero false positives, (2) reproducibility, (3) efficiency, and (4) continuous evaluation and improvement. -->

<!-- 
- Reiterate the requirements stated in the summary (zero false positives, reproducibility [@CramEtAl2020], efficiency, continuous evaluation and improvement)

Methodology for Dealing With Duplicate Study Effects in a Meta-Analysis @Wood2008 -->

<!-- TODO : implicitly evaluate according to the requiremens -->

Proprietary research software for duplicate identification often suffers from shortcomings related to the four requirements.
Relying on tools like Endnote, Covidence, or Hubmeta requires compromises related to false positives, limited transparency of black-box algorithms, or the lack of peer-review and external validation.
Moreover, the use of proprietary tools often incurs costs, and restricts the combination of research tools, because data is hard to access and programmatic interfaces are not offered.

<!-- - research software supporting meta-analysis, research synthesis, and literature reviews, arguably suffers from the lack of peer-reviewed software published under open-source licenses.
- Proprietary tools: presumably used often: Reference managers like Endnote, Platforms like Covidence, Free web-based tools like Hubmeta / Many available solutions are costly, ineffective or inefficient, do not offer programmatic access (lock-in), cannot be adapted (extensibility), and raw data is hard to access, limited transparency and validation
 -->

General purpose deduplication libraries often lack the specificity needed for bibliographic data, requiring skills and excessive amounts of effort to develop and evaluate algorithms.
For example, libraries such as the *Python Record Linkage Toolkit* [@DeBruin2019] and *dedupe (io)* [@GreggEder2022] provide an arsenal of similarity measures, blocking rules, and utility functions.
As such, they provide a valuable basis to support the design of domain-specific duplicate identification tools, but they are rarely used directly by researchers conducting a meta-analysis.
When developing a custom deduplication algorithm, its effectiveness can only be evaluated by creating an independently deduplicated dataset.
More severely, develping an accurate algorithm require in-depth knowledge of publication practices and errors (meta data variation) typically introduced by academic databases, or other systems handling bibliographic metadata.
Experience shows that minor changes potentially have significant effects on overall performance.
Finally, machine-learning libraries, such as *dedupe (io)*, involve the learning of blocking rules and similarity functions from each dataset, and based on user input.
This limits reproducibiltiy, and the required manual efforts reduce efficiency.

<!-- 

- General purpose deduplication tools lack the specificity needed for bibliographic data.

- examples: , : require users to select blocking rules, similarity measures with limited guidance on what is effective for bibliographic data, black-box with unknown generalizability
- dedupe-io: non-reproducible (since blocking rules are learned) - mention small samples: impossible to train (active) learning
- error-function agnostic. data preparation: recommended in data management literature. Rationale: mirror the error function (undo systematic changes introduced by the database) / We focus on the unique requirements of bibliographic duplicate detection (contasts with general-purpose duplicate detection, which is context-agnostic)

research objective: identifying duplicates for a meta-analysis (instead of developing a domain-specific dedupcliation algorithm)

Comparisons between platforms are not so relevant once users have decided for a platform
-->

Open-source research software for duplicate identification is scarce, and to-date, peer-reviewed software is non-existent in this area.
In the Python ecosystem, the only library we found is *ASReview Datatools*, provided by the team behind the *ASReview* screening tool [@VanDeSchootetAl2021].
Our evaluations show that this library introduces a considerable number of false positives, and cannot be used for meta-analyses.
R users or Python users willing to switch the ecosystem, may use ASySD [@Hair2023], a recently published R package with a Shiny web interface.
The code of this package resembles BibDedupe, but it does not achieve zero-false-positives, uses a relatively small test dataset from medicine (n=1845) in the unit tests, and was not evaluated in the peer review process.

In conclusion, researchers are not well-served by currently available proprietary tools, or general purpose deduplication libraries.
Effetive and peer-reviewed libraries are urgently needed for meta-analyses and research synthesis to facilitate researchers' trust and adoption of open-source libraries in the area of literature reviews. 

<!-- - Emphasize that users may decide for a platform (python or R or covidence) first and then use the best deduplication library available -->

<!-- 
aserview: one of the most downloaded python packages for deduplicating bibliographic references

https://support.covidence.org/help/how-does-covidence-detect-duplicates
https://www.covidence.org/blog/improving-our-deduplication-process/

general deduplication resources:
https://github.com/j535d165/data-matching-software
https://github.com/ropeladder/record-linkage-resources
-->

# Example usage

```python
import pandas as pd
from bib_dedupe import merge

# Load your bibliographic dataset into a pandas DataFrame
records_df = pd.read_csv("records.csv")

# Get the merged_df
merged_df = merge(records_df)

```

For advanced use cases, it is also possible to complete and customize each step individually

```python
from bib_dedupe import prep, block, match, merge, export_maybe, import_maybe

# Preprocess records
records_df = prep(records_df)
# Block records
blocked_df = block(records_df)
# Identify matches
matched_df = match(blocked_df)
# Export maybe cases
export_maybe(matched_df)
# Import maybe cases
import_maybe(matched_df)
# Merge
merged_df = merge(records_df, matched_df=matched_df)
```

# Implementation

<!-- distinguish from other approaches like: https://github.com/kermitt2/grobid -->

<!-- ## Duplicate definition -->

We define duplicates as potentially differing bibliographic representations of the same real-world record [cf. @RathboneEtAl2015].
This conceptual definition is operationalized as follows.
The following are considered **duplicates**:

- Papers referring to the same record (per definition)
- Paper versions, including the author's original, submitted, accepted, proof, and corrected versions [@NISO2008]
- Papers that are continuously updated (e.g., versions of Cochrane reviews)
- Papers with different DOIs if they refer to the same record (e.g., redundantly registered DOIs for online and print versions)

<!-- - Papers with fully identical and relatively complete metadata (including DOIs and abstracts if available) are assumed to refer to the same record -->

The following are considered **non-duplicates**:

- A conference paper and its extended journal publication
- A journal paper and a reprint in another journal
- Papers reporting on the same study if they are published separately (e.g., involving different stages of the study such as pilots and protocols, or differences in outcomes, interventions, or populations)

These clarifications are necessary for the evaluation dataset, and for users to understand what will (not) be considered a duplicate.
The rationale is that cases of duplicates are rarely or never cited as separate items in a reference section, while non-duplicates can in principle be cited separately.
It is a different issue whether the corresponding research and administrative practices are considered questionable or ethical (e.g., salami publications, or registering multiple DOIs for the same paper).

To accurately identify and merge duplicates, BibDedupe implements the steps of preprocessing, blocking, rule-based matching, and merging.
As seen in the usage example, each step can be adapted.

<!--
- point out that the dois and the crossref system have redundant global identifiers (different identifiers refer to the same paper - they cannot be used directly for the purpose of deduplication in literature reviews)
- provide a conceptual definition of duplicates (high level, not possible to evaluate automatically) -> provide an operational definition (e.g., references for which all meta-data is identical and complete, they can be assumed to refer to the same paper)
- add the issue of levels to the operational definition (e.g., books/book-chapters, conferences/conference-papers)
- the completeness condition emphasizes the importance of preparation as a preceding step
-->

<!-- each paper can have multiple identifiers (they are not sufficient to identify duplicates). -> need to go back to the metadata (cf. Manubot - trend to cite-by-ID only) -->

## Preprocessing

Preprocessing involves an array of standardizations across fields, including replacement of special characters.
For titles and journals, stopwords are removed to give more weight to distinctive words in the similarity measures.
For the author field, name particles are removed because they are often handled incorrectly in the data creation process.
Additional notes and translations are removed from the title field.
For translated journal names, the English version is used as a replacement.

<!--
BibDedupe includes a function preprocess_authors that standardizes author names to ensure consistency.
This function handles various cases such as non-latin characters, empty strings, organizations, and different author formats.
Other fields such as title, journal, volume, pages, abstract, year, and DOI are also preprocessed to remove unnecessary characters and standardize formats.
-->

## Blocking

To avoid checking all possible combinations of papers, blocking selects the pairs that are likely to be duplicates.
This is a common technique in deduplication where only records within the same block are compared for potential duplication.
<!-- This significantly reduces the number of comparisons needed and improves the efficiency of the deduplication process. -->

BibDedupe relies on a comprehensive set of blocking rules to avoid false negatives in this step.
After the set of blocking rules is applied, we remove pairs not sharing a minimum number of words in the titles, effectively reducing the number of pairs by 50-95% without losing true pairs.
This leads to a more efficient matching step.

## Matching

The matching function selects duplicates or potential duplicates from the list of blocked record pairs.
Potential duplicates, also known as "maybe cases", are marked separately for manual verification.
To achieve accurate and interpretable matching, we specified an array of human-readable conditions, which are based on pre-calculated and context-specific similarities between fields.

<!--
Similarities (details):
Deduplication: continuous, additive, and context-agnostic similarity functions are problematic - e.g., highly similar records but no duplicate (highly similar references with conference vs extended journal papers)
In the specific context of bibliographic duplicates, it is essential to rationalize whether variation in meta-data can be explained by systems processing the same original record (including manuscript production systems, academic databases, or reference managers), or whether it can be explained by different publications.
-->
The conditions and similarity functions account for bibliographic errors commonly introduced between duplicates.
We summarize the key design decisions of BibDedupe, which differ from other approaches (notably ASySD):

- **Robust author similarities**: The most substantial format variation is observed in the author field, requiring robust similarity measures. This is particularly challenging for non-Western names, which are are not supported well by current [citation style conventions](https://tp.libguides.com/c.php?g=920621&p=6640859), or name-parsing software (see [nameparser](https://github.com/derek73/python-nameparser/issues/83)). Given that Chinese authors are leading in many research output and impact rankings [@BrainardNormile2022], this is a limitation. After testing multiple similarity measures, we found that the agreement between capital or beginning-of-word letters provided the most robust measure of author similarity, suggesting that common similarity measures like Jaro-Winkler are less appropriate in this case. We briefly illustrate this with an example of non-Western names that were erroneously abbreviated:

<!--
Yet, it is evident that this is the same author team, with systematic errors in the abbreviation of non-Western names.
For example, the similarity scores (including the commonly used Jaro-Winkler) for the following strings vary between 0.4 and 0.7, suggesting a low similarity or non-matching fields:
-->
```
Author string 1: "Chen J. M.Gong X. Q.Zhong J. G.Chen S. C.Zhang G. Y."
Author string 2: "Jin-Ming C.Xiao-Qi G.Ji-Gen Z.Si-Cong C.Guo-Yuan Z."

Jaccard similarity          : 0.18
Cosine similarity           : 0.31
Jaro-Winkler similarity     : 0.64
First-letters similarity    : 1.0
```

- **Sensitive title similarities**: For titles, similarity measures must be sensitive to minor differences between non-duplicates, as exemplified in so-called *salami-publications* or publications consisting of multiple parts. In these cases, titles are almost identical, and general similarity measures yield values close to 1, i.e., they are not sensitive enough to differences that are significant in the context of bibliographic data. BibDedupe implements a similarity function that is sensitive to differences in numbers (e.g., part 1 vs. part 2), populations (e.g., men vs. women, in vivo vs. in vitro, cats vs. rats), interventions (e.g., effect of X vs. effect of Y), and outcomes (e.g., effect on X vs. effect on Y).

<!-- 
Similarly, some distinct paper titles have a similarity close to 1.0, for instance when presenting "part 1" and "part 2" of a study, or splitting a sample for 
pico: ...
"in vitro" and "in vivo", "men" and "women", "adults" and "adolescents", or "cats" and "rats". This variation clearly results from different publications.
-->

- **Translations of container titles**: Given the nested data structure, in which papers are contained in journals, proceedings, or other containers, accurate matching is required for the field of container titles. To accomplish this, BibDedupe uses a list of approx. 1,300 translated journal names as replacements in the preprocessing step, effectively increasing the average Jaro-Winkler similarity between journals and their translated titles from 0.45 to 1.0. This leads to a sbustantial improvement in false negatives.

- **Handling missing values**: While values author, title, and container_title fields are rarely missing, there can be missing values in the other fields, such as the volume, doi, or abstract. Similarity measures typically return insufficient results when only one value is missing. For instance, when one paper contains a doi and the other does not, the similarity would be zero, as it would be the case for different dois. We distinguish these cases based on a `non_contradictory()` function, which is robust against missing values, and indicates whether non-missing values differ between records.

<!--
Note: there were no improvements in accuracy when handling misplaced values (volume/number/pages) explicitly.
In addition, we check for misplaced values between selected fields, including the volume, number, and pages. Such misplacements were observed in the datasets, and it is plausible to assume that humans and machines perform worse in distinguishing whether a digit represents the volume or number of a paper, given that the other fields often have discernible patterns. -->

We note that global IDs (like DOIs) contribute to duplicate identification, but neither are identical DOIs considered a sufficient condition for a duplicate, nor are distinct DOIs considered a sufficient condition for non-duplicates.
This is confirmed by the data.
For the iterative tuning, we designed diagnostic utilities to assess which conditions match for selected (FP/FN) cases.

## Merging

<!-- 
Advancing the foundations of record-level research integration: A ban/moratorium for "duplicate removal" and a path forward
-->

Upon merging a set of records, BibDedupe keeps track of the original IDs in the *origin* field.
Compared to the common approach of deleting n-1 records from the set of duplicates, this approach has three distinct advantages: (1) **validation**: together with the original dataset, it allows users to validate whether duplicate decisions are accurate, (2) **undo**: it is possible to restore selected cases where erroneous duplicates were merged, and (3) **evaluation**: it enables subsequent use of datasets to evaluate and tune duplicate detection algorithms.

The merging function uses heuristics to select the most appropriate fields from duplicate records instead of selecting all fields from one record regardless of field-level quality.
For instance, proper capitalization is preferred when one record has author or title fields in all-caps, and DOIs are selected when other DOI fields are empty.

## Evaluation

To evaluate BibDedupe, we collected 10 datasets comprising over 160,000 records and 34,900 duplicates [@Hair2023;@RathboneEtAl2015;@WagnerPresterPare2021].
This is, to the best of our knowledge, the most comprehensive evaluation of bibliographic duplicate detection algorithms to date.
We completed over 3,000 iterations to evaluate and improve BibDedupe based on these dataset.

The efforts involved tuning the preprocessing, blocking, and matching steps, vetting different similarity measures, and validating the false positives and negatives based on the definition of (non)-duplicates.
We carefully reviewed the conditions to combine and generalize narrowly defined cases.
In addition, we implemented unit tests to ensure consistency, and understand how changes in the code affect each step.
Runtime was optimized by implementing and evaluating different approaches to parallel processing, such as processing numpy-arrays vs. splitting dataframes horizontally.
As a result, the depression dataset with approx. 80,000 records is processed in under 10 minutes with 8 CPUs.

<!--
performance/runtime: hard to compare, but dedupliating 80,000 records in 5 minutes is ok (scales with cpus given that prep, block and similarities are implemented for parallel processing).

transparent/analyzable/reproducible: fixed blocking rules, rules to identify duplicates

The datasets were checked according to the above-stated definition.
comprehensively analyzed error cases
-->

**Package** | **FP** | **TP** | **FN** | **TN** | **FP rate** | **Specificity** | **Sensitivity** | **F1**
:-----------|-------:|-------:|-------:|-------:|------------:|----------------:|----------------:|-------:
BibDedupe   | 0      | 34906  | 312    | 125568 | 0           | 1.0             | 0.99            | 1.00
asreview    | 5596   | 29749  | 5469   | 119972 | 0.04        | 0.96            | 0.84            | 0.84

Given that ASySD and other tools were evaluated on a subset of the datasets contained in our evaluation [@Hair2023], it is instructive to re-print the results for comparison.

**Package** | **FP** | **TP** | **FN** | **TN** | **FP rate** | **Specificity** | **Sensitivity** | **F1**
:-----------|-------:|-------:|-------:|-------:|------------:|----------------:|----------------:|-------:
Endnote  | 11 | 12466 | 3657 | 77977 | 0.0 | 1.0 | 0.77 | 0.87
Human    | 54 | 14693 | 1430 | 77934 | 0.0 | 1.0 | 0.91 | 0.95
ASySD    | 80 | 15664 | 459  | 77908 | 0.0 | 1.0 | 0.97 | 0.98
SRA-DM   | 1735 | 12794 | 3329 | 76253 | 0.02 | 0.98 | 0.79 | 0.83

<!--

**Package** | **FP** | **TP** | **FN** | **TN** | **FP rate** | **Specificity** | **Sensitivity** | **Precision** | **F1**
:-----------|-------:|-------:|-------:|-------:|------------:|----------------:|----------------:|--------------:|-------:
BibDedupe   | 0      | 34906  | 312    | 125568 | 0           | 1.0             | 0.99            | 1.0           | 1.00
asreview    | 5596   | 29749  | 5469   | 119972 | 0.04        | 0.96            | 0.84            | 0.84          | 0.84

Given that ASySD and other tools were evaluated on a subset of the datasets contained in our evaluation, it is instructive to re-print the results for comparison.

**Package** | **FP** | **TP** | **FN** | **TN** | **FP rate** | **Specificity** | **Sensitivity** | **Precision** | **F1**
:-----------|-------:|-------:|-------:|-------:|------------:|----------------:|----------------:|--------------:|-------:
Endnote (Hair et al. 2021) | 11 | 12466 | 3657 | 77977 | 0.0 | 1.0 | 0.77 | 1.0 | 0.87
Human (Hair et al. 2021)   | 54 | 14693 | 1430 | 77934 | 0.0 | 1.0 | 0.91 | 1.0 | 0.95
ASySD (Hair et al. 2021)   | 80 | 15664 | 459  | 77908 | 0.0 | 1.0 | 0.97 | 0.99 | 0.98
SRA-DM (Hair et al. 2021)  | 1735 | 12794 | 3329 | 76253 | 0.02 | 0.98 | 0.79 | 0.88 | 0.83
-->

# Ongoing improvements

BibDedupe provides duplicate identification functionality, which performs with zero false positives on a dataset comprising over 160,000 records.
It builds on carefully crafted rules and high-quality training data to ensure effectiveness, transparency, and reproducibility.
The evaluation runs automatically and provides a solid foundation for continuous improvements and additions of datasets.
We intend to incorporate additional datasets and continue refining the rules and procedures.

<!--
going forward, BibDedupe will adopt an approach similar to GROBID, and focus on high-quality training and evaluation data (https://grobid.readthedocs.io/en/latest/Principles/#training-data-qualitat-statt-quantitat)

similar to:
10.21105.joss.05755

addresses these issues by providing an effective (zero-false-positives), automated/efficient
-->

# References

