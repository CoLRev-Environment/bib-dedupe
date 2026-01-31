Architecture
====================================

.. mermaid::

  flowchart LR

    A0["Input: records_df"]
      --> A1["prep(records_df)<br>• prep_schema<br>• prep_author<br>• prep_title<br>• prep_abstract<br>• prep_container_title<br>• prep_doi<br>• prep_volume<br>• prep_number<br>• prep_pages<br>• prep_year"]

    O2["(manual review outside code)"]

    subgraph API["Public API (call sequence)"]
      A1 --> A2["block(prep_df)<br>Uses block.py to create candidate record pairs"]

      A2 --> A3["match(pairs_df)<br>Uses match.py to compute similarities and classify pairs"]

      A3 --> A4["cluster(matched_df)<br>Uses cluster.py to build connected components (duplicate groups)"]

      A4 --> A5["merge(records_df, duplicate_id_sets)<br>Uses merge.py to combine records within each group"]

      subgraph Manual["Optional manual review (human-in-the-loop)"]
          O1["export_maybe(records_df, matched_df)<br>Write uncertain pairs via maybe_cases.export"]
          O3["import_maybe(matched_df)<br>Read decisions via maybe_cases.import"]
      end
    end

    O1 --> O2 --> O3

    A5 --> A6["Output: merged records_df"]

    %% optional linkage back into the main flow
    A3 -. "optional manual review" .-> O1
    O3 -. "returns updated matched_df" .-> A4


Runtime of individual steps

cd docs
python benchmark_runtime_detailed.py