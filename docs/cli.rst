Command-line interface
======================

BibDedupe exposes its deduplication pipeline through the :command:`bib-dedupe`
entry point. The CLI layers structured subcommands on top of the library
functions in :mod:`bib_dedupe.bib_dedupe` and aims to provide an ergonomic
wrapper for common workflows.

To use the cli, install bib-dedupe with the cli option:

.. code-block:: bash

   pip install bib-dedupe[cli]

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

Bibliographic records used by ``merge``, ``export-maybe``, and
``match --records`` are loaded and written with `bibliography-io`_. Supported
record inputs include BibTeX (``.bib``), RIS (``.ris``), CSV (``.csv``), ENL,
NBIB, and JSON. Excel input requires the ``bibliography-io[excel]`` extra;
Markdown reference-list input requires the ``bibliography-io[markdown]`` extra
and a running GROBID service. Record output is supported in BibTeX, RIS, CSV,
ENL (``.enl``), Markdown tables, and Excel (``.xlsx`` with the Excel extra).
JSON and NBIB are input-only formats, and Parquet is not supported for
bibliographic records. BibTeX output preserves ``colrev_origin`` as a list.
RIS and ENL can omit fields their formats cannot represent; use BibTeX or CSV
when preserving arbitrary metadata and provenance is required.

Record IDs come from the normalized records returned by bibliography-io,
including sequential IDs it generates for some inputs. IDs must be non-empty
and unique. On ``merge``, ``export-maybe``, and ``match --export-maybe``, use
``--id-field FIELD`` to select a different normalized field as the ID. The
mutually exclusive ``--generate-ids`` option generates sequential IDs only if
the loader returns no usable IDs; it does not replace IDs supplied or generated
by bibliography-io. These options apply after bibliography-io loading and cannot
override a load error such as duplicate IDs rejected during normalization.

The stepwise ``prep``, ``block``, ``match``, and ``import-maybe`` commands use
DataFrame files instead: CSV is supported, Parquet (``.parquet`` or ``.pq``)
requires a pandas backend such as ``pyarrow``, and JSON is read/written in
records orientation. Unknown extensions produce a helpful error and non-zero
exit code.

.. _bibliography-io: https://github.com/CoLRev-Environment/bibliography-io

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
