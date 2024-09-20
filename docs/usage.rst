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
Given that each database follows its own schema with slightly different column names, import functionality must be customized to the specific database.
We are working on corresponding import functions as part of the `CoLRev project <https://github.com/CoLRev-Environment/colrev>`_.
Once the import functions are available, they will be described here (see this `issue <https://github.com/CoLRev-Environment/bib-dedupe/issues/16>`_ for more information).

.. _example datasets: https://github.com/CoLRev-Environment/bib-dedupe/tree/main/data
