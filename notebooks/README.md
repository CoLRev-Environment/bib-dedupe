# Evaluation

## Duplicate definition

Rathbone et al. (2015): "A duplicate record was defined as being the same bibliographic record (irrespective of how the citation details were reported, e.g. variations in page numbers, author details, accents used or abridged titles). Where further reports from a single study were published, these were not classed as duplicates as they are multiple reports which can appear across or within journals. Similarly, where the same study was reported in both journal and conference proceedings, these were treated as separate bibliographic records."

Borissov et al. (2022): "Following a standardized definition [6, 7, 9], we defined one or more duplicates as an existing unique record having the same title, authors, journal, DOI, year, issue, volume, and page number range metadata."

Note: The datasets may have applied a different understanding of duplicates.

The similarity-functions should be sensitive to important differences (e.g., "in vivo" vs "in vitro" should not be 92% similar, "men" vs "women" should not be 94% similar)

Bib-Dedupe could support different labels:

- Distinct
- Duplicate
- Maybe
- Updated
- Reprinted
- Extended (conference-journal)
- Included (inbook-book)

A flag could be used to indicate whether they should be merged (retain_reprinted = False, ...)

TODO : start with the maybe category (and indicate that Bib-dedupe will be extended) - the other categories would require separate "true-origin-pars" lists.

Updates
- In some cases, papers are continuously updated, such as Cochrane review papers. These updates can be treated as separate entities or as part of the original paper, depending on the requirements of the analysis.
- For example, the following two papers are updates of the same study:
    https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.CD009128.pub2
    https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.CD009128.pub3
- These updates often have similar DOIs
- Aka current/previous versions:
https://currentprotocols.onlinelibrary.wiley.com/doi/10.1002/0471142301.ns0810as14
https://currentprotocols.onlinelibrary.wiley.com/doi/10.1002/0471142301.ns0810as55

Reprints
- (e.g., abstract_similarity= 1.0)
- physiological effects of medium chain triglycerides potential agents in the prevention of obesity reprinted from vol 132 pg 329 2002
- srsr  source_1.bib/0000023119;source_1.bib/0000056666
- "reprint of " - "reprinted from" (source_1.bib/0000054209;source_1.bib/0000017201)
- check: "reprinted in ..." in title.
- The book series "Advances in Alzheimer's Disease" brings together the latest insights in Alzheimer’s disease research in specific areas in which major advances have been made. It assembles and builds on work recently published in the Journal of Alzheimer's Disease (JAD) and also includes further contributions to ensure comprehensive coverage of the topic. The emphasis is on the development of novel approaches to understanding and treating Alzheimer’s and related diseases.
adva alzh s dise
j alzh s dise

Corrected and republished
- Comparative analysis of anxiety-like behaviors and sensorimotor functions in two rat mutants, ci2 and ci3, with lateralized rotational behavior. Lindema S, Gernet M, Bennay M, Koch M, Löscher W. Physiol Behav. 2008 Jan 28;93(1-2):417-26. doi: 10.1016/j.physbeh.2007.11.034. PMID: 18320635

Multiple letters and replies:
- haematology - source_1.bib/0000000008;source_1.bib/0000000039

Included
- Part 1-2, ...
- TBD: match books/inbooks separately and exclude proceedigns items?!



## Evaluation datasets

| Dataset            | Reference                | Status                                           |
| ------------------ | -------------------------| ------------------------------------------------ |
| digital_work       | Wagner et al. 2021       | Included                                         |
| cytology_screening | Rathbone et al. 2015     | Included (based on [OSF](https://osf.io/dyvnj/)) |
| haematology        | Rathbone et al. 2015     | Included (based on [OSF](https://osf.io/dyvnj/)) |
| respiratory        | Rathbone et al. 2015     | Included (based on [OSF](https://osf.io/dyvnj/)) |
| stroke             | Rathbone et al. 2015     | Included (based on [OSF](https://osf.io/dyvnj/)) |
| cardiac            | Hair et al. 2021         | Included (based on [OSF](https://osf.io/c9evs/)) |
| depression         | Hair et al. 2021         | Included (based on [OSF](https://osf.io/c9evs/)) |
| diabetes           | Hair et al. 2021         | Included (based on [OSF](https://osf.io/c9evs/)) |
| neuroimaging       | Hair et al. 2021         | Included (based on [OSF](https://osf.io/c9evs/)) |
| srsr               | Hair et al. 2021         | Included (based on [OSF](https://osf.io/c9evs/)) |
|                    | Kwon et al. 2015         | Requested: 2023-11-14                            |
|                    | Borissov et al. 2022     | Requested: 2023-11-14                            |

The [SYNERGY](https://github.com/asreview/synergy-dataset) datasets are not useful to evaluate duplicate identification algorithms because they only contain IDs, and the associated metadata would have no variance.

## Dataset model and confusion matrix

Record list before de-duplication

| ID  | Author           | Title                                    |
| --- | ---------------- | ---------------------------------------- |
| 1   | John Doe         | Introduction to Data Science             |
| 2   | J. Smith         | the art of problem solving               |
| 3   | Jane A. Smith    | The Art of Problem Solving               |
| 4   | Jane M. Smith    | the art of problem solving               |
| 5   | Alex Johnson     | beyond the basics: advanced programming  |

Duplicate matrix:

|     | 1   | 2   | 3   | 4   | 5   |
| --- | --- | --- | --- | --- | --- |
| 1   |  -  |  -  |  -  |  -  |  -  |
| 2   |     |  -  |  -  |  -  |  -  |
| 3   |     |  X  |  -  |  -  |  -  |
| 4   |     |  X  |  X  |  -  |  -  |
| 5   |     |     |     |     |  -  |

Components:

| Paper | Components |
| ---   | ----------- |
| 1     | c_1         |
| 2     | c_2         |
| 3     | c_2         |
| 4     | c_2         |
| 5     | c_3         |

Record list without duplicates:

| ID  | Author           | Title                                    |
| --- | ---------------- | ---------------------------------------- |
| 1   | John Doe         | Introduction to Data Science             |
| 2   | J. Smith         | the art of problem solving               |
| 5   | Alex Johnson     | beyond the basics: advanced programming  |

Note: instead of paper 2, papers 3 or 4 could have been removed. It is not pre-determined which duplicates are retained or removed.

That makes the evaluation challenging because the following list would also be correct:

| ID  | Author           | Title                                    |
| --- | ---------------- | ---------------------------------------- |
| 1   | John Doe         | Introduction to Data Science             |
| 4   | Jane M. Smith    | the art of problem solving               |
| 5   | Alex Johnson     | beyond the basics: advanced programming  |


We use the `compare_dedupe_id()` method of `colrev.ops.dedupe_benchmark.DedupeBenchmarker`, which compares sets.

Given the set of duplicate IDs `did = [Ang2011, Ang2011a, Ang2012, AngHu2011]` as the ground truth, it is evident that only one of the IDs should be retained in the merged list `ml` (although any selection among the IDs in `did` would be valid).

- If none of the duplicate IDs is retained, there is one false positive (FP), i.e., a record that was erroneously removed as a duplicate. The remaining (`len(did)-1`) records are counted as true positives (TP).
- The first duplicate ID that is retained is counted as the true negative (TN), i.e., the record correctly marked as a non-duplicate. Additional records in `ml` are marked as false negatives (FN) because they should have been removed. Remaining records from `did` that are not in `ml` are marked as true positives (TP) because they were correctly removed from `ml`.

<!--
Rathbone et al. (2015): "The **accuracy of the results were coded against the benchmark** according to whether it was a true positive (true duplicate, i.e. correctly identified duplicate), false positive (false duplicate, i.e. incorrectly identified as duplicate), true negative (unique record) or false negative (true duplicate, i.e. incorrectly identified as unique record).

Kwon et al. (2015): "All sets of results from the de-duplication strategies outlined above were compared against the gold standard sets to identify false negatives (duplicate citations that should have been deleted but were not) and false positives (duplicate citations that were deleted but should not have been). We also recorded the time it took to de-duplicate results in each option (Table 1, online only)"
-->

## References

Borissov, N., Haas, Q., Minder, B., Kopp-Heim, D., von Gernler, M., Janka, H., ... & Amini, P. (2022). Reducing systematic review burden using Deduklick: a novel, automated, reliable, and explainable deduplication algorithm to foster medical research. Systematic Reviews, 11(1), 172. doi:10.1186/s13643-022-02045-9

Hair, K., Bahor, Z., Macleod, M., Liao, J., & Sena, E. S. (2023). The Automated Systematic Search Deduplicator (ASySD): a rapid, open-source, interoperable tool to remove duplicate citations in biomedical systematic reviews. BMC Biology, 21(1), 189.

Kwon, Y., Lemieux, M., McTavish, J., & Wathen, N. (2015). Identifying and removing duplicate records from systematic review searches. Journal of the Medical Library Association, 103(4), 184. doi:10.3163/1536-5050.103.4.004

Rathbone, J., Carter, M., Hoffmann, T., & Glasziou, P. (2015). Better duplicate detection for systematic reviewers: evaluation of Systematic Review Assistant-Deduplication Module. Systematic Reviews, 4, 1-6. doi:10.1186/2046-4053-4-6

Wagner, G., Prester, J., & Paré, G. (2021). Exploring the boundaries and processes of digital platforms for knowledge work: A review of information systems research. The Journal of Strategic Information Systems, 30(4), 101694.
