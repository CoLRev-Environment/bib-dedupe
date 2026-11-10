Usage
====================================

It is possible to complete and customize each step individually:

.. code-block:: python

  import pandas as pd
  from bib_dedupe.bib_dedupe import prep, block, match, merge, export_maybe, import_maybe

  # Load your bibliographic dataset into a pandas DataFrame
  records_df = pd.read_csv("records.csv")

  # Preproces records
  records_df = prep(records_df)

  # Block records
  blocked_df = block(records_df)

  # Identify matches
  matched_df = match(blocked_df)

  # Check maybe cases
  export_maybe(records_df, matched_df=matched_df)
  matched_df = import_maybe(matched_df)

  # Merge
  merged_df = merge(records_df, matched_df=matched_df)

Fields used by BibDeduper

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - **Name**
     - **Definition**
   * - **ID**
     - A unique ID
   * - **ENTRYTYPE**
     - The type of publication (e.g., article, book, inproceedings)
   * - **author**
     - The author(s) of the publication
   * - **title**
     - The title of the publication
   * - **year**
     - The year of publication
   * - **journal**
     - The name of the journal in which the publication appeared
   * - **volume**
     - The volume number of the publication
   * - **number**
     - The issue number of the publication
   * - **pages**
     - The page numbers of the publication
   * - **doi**
     - The Digital Object Identifier (DOI)
   * - **abstract**
     - The abstract
   * - **search_set**
     - Distinct sets of papers (e.g., old_search), can be empty. \*

\* The `merge()` function ensures that records from the same `search_set` are not merged. The `match()` function ensures that individual pairs (e.g., A-B, B-C) do not come from the same `search_set`. `match()` does not consider transitive relations (i.e., A-C could be from the same `search_set`). The `cluster()` and `get_connected_components()` functions (part of `merge()`) ensure that records are not merged if the component already contains a record from the same `search_set`.

Search updates
-----------------------

When updating a literature search, the `old_search` can be assumed to have no duplicates. To exclude a set of papers from deduplication, it is possible to pass a corresponding label to the `search_set` column.


Example data
-----------------------

Data from the `example datasets`_ can be loaded as follows:

.. code-block:: python

  from bib_dedupe.bib_dedupe import merge
  from bib_dedupe.bib_dedupe import load_example_data

  # Load example dataset
  records_df = load_example_data("stroke")

  # Get the merged_df
  merged_df = merge(records_df)

  # Save as csv
  merged_df.to_csv("merged.csv", index=False)


Import file formats
-----------------------

BibDedupe can process any bibliographic data set once it is in a pandas DataFrame, and contains the columns listed above.
For importing common bibliographic formats, use the standalone `bibliography-io <https://github.com/CoLRev-Environment/bibliography-io>`_ package.
It can read BibTeX, RIS, CSV, Excel, EndNote, NBIB, and JSON files; Markdown reference-list parsing is also available with its optional Markdown backend.
BibDedupe does not require `bibliography-io` to be installed.

Install bibliography-io with the Excel extra to enable its pandas DataFrame helper (and Excel file support):

.. code-block:: console

   python -m pip install "bibliography-io[excel]"

Use `load_df()` to load and normalize a supported file directly into a DataFrame.
The format is inferred from the filename extension, so change the path to load a different format:

.. code-block:: python

   from bibliography_io import load_df
   from bib_dedupe.bib_dedupe import merge

   records_df = load_df("references.ris")  # also accepts .bib, .csv, .xlsx, .enl, .nbib, and .json

   merged_df = merge(records_df)

If the filename extension is ambiguous or does not match the file format, pass `format` explicitly:

.. code-block:: python

   records_df = load_df("references.txt", format="ris")

`load_df()` applies generic normalization unless a source is specified.
Database exports can differ in their field conventions, so check that the loaded DataFrame contains BibDedupe's required fields (including `ID`, `ENTRYTYPE`, `author`, `title`, and `year`); source-specific normalization may be needed for some exports.
Markdown reference-list parsing is also available with the optional Markdown backend and requires a GROBID service managed by the caller.
See the `bibliography-io usage documentation <https://colrev-environment.github.io/bibliography-io/usage.html>`_ for source options, the complete format support table, format limitations, and optional dependencies.

.. _example datasets: https://github.com/CoLRev-Environment/bib-dedupe/tree/main/data
