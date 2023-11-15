#! /usr/bin/env python
"""BibDedupe utility"""
from __future__ import annotations

import datetime
import pprint
from pathlib import Path
from typing import Dict

import pandas as pd
from colrev.constants import Fields
from colrev.constants import FieldSet

# pylint: disable=too-few-public-methods


class BibDedupeUtil:
    """BibDedupeUtil class"""

    def __init__(self, *, debug: bool = False):
        self.debug = debug
        self.p_printer = pprint.PrettyPrinter(indent=4, width=140, compact=False)

    def export_for_pytest(
        self,
        *,
        records_df: pd.DataFrame,
        true_merged_origins: list,
        benchmark_path: Path,
    ) -> None:
        """
        Export the benchmark data for pytest.

        Args:
            target_path (Path): The path to export the benchmark data to.
        """
        benchmark_path.mkdir(parents=True, exist_ok=True)

        records_df = records_df.copy()
        merged_origins = true_merged_origins

        all_origins = records_df[Fields.ORIGIN].tolist()
        all_origins_dict = {x: "" for n in all_origins for x in n}

        # anonymize origins
        source_dict: Dict[str, str] = {}
        for i, key in enumerate(all_origins_dict.keys()):
            source = key.split("/")[0]
            if source not in source_dict:
                source_dict[source] = f"source_{len(source_dict)}.bib"
            new_key = f"{source_dict[source]}/{str(i).zfill(10)}"
            all_origins_dict[key] = new_key
        records_df[Fields.ORIGIN] = records_df[Fields.ORIGIN].apply(
            lambda x: [all_origins_dict.get(i, i) for i in x]
        )
        merged_origins = [
            [all_origins_dict.get(sub_origin, sub_origin) for sub_origin in origin]
            for origin in merged_origins
        ]

        records_df = records_df[
            records_df.columns.intersection(
                set(
                    FieldSet.IDENTIFYING_FIELD_KEYS
                    + [
                        Fields.ID,
                        Fields.ENTRYTYPE,
                        Fields.ORIGIN,
                        Fields.STATUS,
                        Fields.DOI,
                        Fields.ISBN,
                        Fields.ABSTRACT,
                    ]
                )
            )
        ]

        records_df.to_csv(
            str(benchmark_path / Path("records_pre_merged.csv")), index=False
        )

        merged_record_origins_df = pd.DataFrame({"merged_origins": merged_origins})
        merged_record_origins_df.to_csv(
            str(benchmark_path / Path("merged_record_origins.csv")), index=False
        )

    def append_to_output(self, result: dict, *, package_name: str) -> None:
        """
        Append the result to the output file.

        Args:
            result (dict): The result dictionary.
            package_name (str): The name of the package.

        Returns:
            None
        """

        output_path = Path("../output/evaluation.csv")

        result["package"] = package_name
        current_time = datetime.datetime.now()
        result["time"] = current_time.strftime("%Y-%m-%d %H:%M")

        if not Path(output_path).is_file():
            results_df = pd.DataFrame(
                columns=[
                    "package",
                    "time",
                    "dataset",
                    "TP",
                    "FP",
                    "FN",
                    "TN",
                    "false_positive_rate",
                    "specificity",
                    "sensitivity",
                    "precision",
                    "f1",
                ]
            )
        else:
            results_df = pd.read_csv(output_path)

        result_item_df = pd.DataFrame.from_records([result])
        result_item_df = result_item_df[
            [
                "package",
                "time",
                "dataset",
                "TP",
                "FP",
                "FN",
                "TN",
                "false_positive_rate",
                "specificity",
                "sensitivity",
                "precision",
                "f1",
            ]
        ]
        results_df = pd.concat([results_df, result_item_df])
        results_df.to_csv(output_path, index=False)
