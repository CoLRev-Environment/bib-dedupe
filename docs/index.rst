Bib-Dedupe Documentation
======================================

Bib-Dedupe is an open-source **Python library for deduplication of bibliographic records**, tailored for literature reviews.
Unlike traditional deduplication methods, **Bib-Dedupe** focuses on entity resolution, linking duplicate records instead of simply deleting them.

Features
--------

* **Automated Duplicate Linking with Zero False Positives**: Bib-Dedupe automates the duplicate linking process with a focus on eliminating false positives.
* **Preprocessing Approach**: Bib-Dedupe uses a preprocessing approach that reflects the unique error generation process in academic databases, such as author re-formatting, journal abbreviation or translations.
* **Entity Resolution**: Bib-Dedupe does not simply delete duplicates, but it links duplicates to resolve the entitity and integrates the data. This allows for validation, and undo operations.
* **Programmatic Access**: Bib-Dedupe is designed for seamless integration into existing research workflows, providing programmatic access for easy incorporation into scripts and applications.
* **Transparent and Reproducible Rules**: Bib-Dedupe's blocking and matching rules are transparent and easily reproducible to promote reproducibility in deduplication processes.
* **Continuous Benchmarking**: Continuous integration tests running on GitHub Actions ensure ongoing benchmarking, maintaining the library's reliability and performance across datasets.
* **Efficient and Parallel Computation**: Bib-Dedupe implements computations efficiently and in parallel, using appropriate data structures and functions for optimal performance.


Installation
------------

Bib-Dedupe is available on `PyPI <https://pypi.org/project/bib-dedupe/>`_, and can be installed via pip:

.. code-block:: bash

   pip install bib-dedupe

Getting Started
---------------

.. code-block:: python

   import pandas as pd
   from bib_dedupe.bib_dedupe import merge

   # Load your bibliographic dataset into a pandas DataFrame
   records_df = pd.read_csv("records.csv")

   # Get the merged_df
   merged_df = merge(records_df)

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



.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

   usage
   evaluation
   api
