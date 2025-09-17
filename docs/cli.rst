Command-line interface
======================

BibDedupe exposes its deduplication pipeline through the :command:`bib-dedupe`
entry point. The CLI layers structured subcommands on top of the library
functions in :mod:`bib_dedupe.bib_dedupe` and aims to provide an ergonomic
wrapper for common workflows.

Quick reference
---------------

.. code-block:: bash

   # merge records in one go
   bib-dedupe merge -i records.csv -o merged.csv

   # run the pipeline step by step
   bib-dedupe prep -i records.csv -o records.prep.csv
   bib-dedupe block -i records.prep.csv -o pairs.csv
   bib-dedupe match -i pairs.csv -o matches.csv

   # export maybe cases for manual review
   bib-dedupe match -i pairs.csv -o matches.csv --export-maybe --records records.csv
   # review the generated maybe_cases.csv file, then
   bib-dedupe import-maybe -i matches.csv -o matches.reviewed.csv
   bib-dedupe merge -i records.csv -o merged.csv --import-maybe

Input and output formats
------------------------

The CLI inspects file extensions to determine how to load or persist
:class:`pandas.DataFrame` objects. CSV is supported out of the box. Parquet files
(``.parquet`` or ``.pq``) are supported when an appropriate pandas backend (for
example ``pyarrow``) is installed. JSON files are read and written in ``records``
orientation. Unknown extensions trigger a helpful error and non-zero exit code.

Subcommands
-----------

``merge``
   Execute the full pipeline and write merged records. Optional flags include
   ``--stats`` (print pipeline statistics), ``--export-maybe`` (export uncertain
   pairs for manual review), ``--import-maybe`` (apply decisions captured in
   :mod:`bib_dedupe.maybe_cases`).

``prep``
   Run :func:`bib_dedupe.bib_dedupe.prep` on an input dataset and write the
   prepared records.

``block``
   Produce candidate record pairs via :func:`bib_dedupe.bib_dedupe.block`.

``match``
   Score blocked pairs with :func:`bib_dedupe.bib_dedupe.match`. Accepts
   ``--export-maybe`` to immediately write maybe cases (requires ``--records`` to
   supply the original dataset).

``export-maybe``
   Call :func:`bib_dedupe.bib_dedupe.export_maybe` on explicit records and match
   files. Useful for re-running the export without recomputing matches.

``import-maybe``
   Apply manually reviewed maybe cases using
   :func:`bib_dedupe.bib_dedupe.import_maybe`. When ``-o/--output`` is omitted
   the updated matches are emitted to ``stdout``.

``version``
   Print the installed BibDedupe package version.

Common options
--------------

* ``--cpu`` controls how many CPUs the underlying functions may use. ``-1`` is
  the default and lets the library pick an appropriate value.
* ``--verbosity-level`` passes through the exact verbosity value expected by the
  library. ``-q/--quiet`` maps to level ``0`` and ``-v/--verbose`` maps to level
  ``2`` for convenience. These flags are mutually exclusive.

Error handling and exit codes
-----------------------------

Usage issues (for example missing files or incompatible flag combinations)
raise friendly error messages and exit with status code ``2``. Unexpected
runtime failures exit with status ``1`` after printing the exception message.
