Usage
====================================


.. code-block:: python

   import pandas as pd
   from bib_dedupe.bib_dedupe import merge

   # Load your bibliographic dataset into a pandas DataFrame
   records_df = pd.read_csv("records.csv")

   # Get the merged_df
   merged_df = merge(records_df)

For more detailed usage instructions and customization options, refer to the documentation.

For advanced use cases, it is also possible to complete and customize each step individually

.. code-block:: python

   from bib_dedupe.bib_dedupe import prep, block, match, merge, export_maybe, import_maybe

   records_df = prep(records_df)

   # Block records
   blocked_df = block(records_df)

   # Identify matches
   matched_df = match(blocked_df)

   # Check maybe cases
   export_maybe(matched_df, records_df, matches)
   matches = import_maybe(matches)

   # Merge
   merged_df = merge(records_df, matches=matches)

Fields used by BibDeduper

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - **Name**
     - **Definition**
   * - **ID**
     - A unique ID
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
     - Distinct sets of papers (e.g., old_search), can be empty.
