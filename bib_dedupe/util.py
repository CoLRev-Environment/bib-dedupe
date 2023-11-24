#! /usr/bin/env python
"""BibDedupe utility"""
from __future__ import annotations

import datetime
import pprint
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Dict
from typing import List

import pandas as pd

from bib_dedupe.constants import Fields
from bib_dedupe.constants import FieldSet

# pylint: disable=too-few-public-methods


class BibDedupeUtil:
    """BibDedupeUtil class"""

    def __init__(self, *, debug: bool = False):
        self.debug = debug
        self.p_printer = pprint.PrettyPrinter(indent=4, width=140, compact=False)

    def get_dataset_labels(self) -> list:
        """
        Get the directory names in data
        """
        data_path = Path(__file__).parent.parent / "data"
        return [dir.name for dir in data_path.iterdir() if dir.is_dir()]

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
                    "runtime",  # Add runtime to the DataFrame columns
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
                "runtime",
            ]
        ]
        results_df = pd.concat([results_df, result_item_df])
        results_df.to_csv(output_path, index=False)

        output_md_path = Path("../output/current_results.md")
        if not output_md_path.is_file():
            output_md_path.touch()
        with open(output_md_path, "w") as f:
            f.write("# Current statistics\n\n")
            for dataset in results_df["dataset"].unique():
                if dataset == "problem_cases":
                    continue
                dataset_df = results_df[results_df["dataset"] == dataset]
                n_total = (
                    dataset_df.iloc[0]["FP"]
                    + dataset_df.iloc[0]["TP"]
                    + dataset_df.iloc[0]["FN"]
                    + dataset_df.iloc[0]["TN"]
                )
                f.write(f"## {dataset} (n={n_total})\n\n")
                dataset_df = dataset_df.sort_values(by="time", ascending=False)
                dataset_df = dataset_df.drop_duplicates(subset="package", keep="first")
                dataset_df = dataset_df.drop(columns=["dataset"])
                dataset_df = dataset_df[
                    [
                        "package",
                        "FP",
                        "TP",
                        "FN",
                        "TN",
                        "false_positive_rate",
                        "specificity",
                        "sensitivity",
                        "precision",
                        "f1",
                    ]
                ]
                dataset_df["false_positive_rate"] = dataset_df[
                    "false_positive_rate"
                ].round(4)
                dataset_df["specificity"] = dataset_df["specificity"].round(4)
                dataset_df["sensitivity"] = dataset_df["sensitivity"].round(4)
                dataset_df["precision"] = dataset_df["precision"].round(4)
                dataset_df["f1"] = dataset_df["f1"].round(4)
                dataset_df = dataset_df.sort_values(by=["f1"], ascending=[False])
                f.write(dataset_df.to_markdown(index=False))
                f.write("\n\n")


def connected_components(origin_sets: list) -> list:
    """
    Find the connected components in a graph.

    Args:
        origin_sets (list): A list of origin sets.

    Returns:
        list: A list of connected components.
    """
    graph = defaultdict(list)

    def dfs(node: str, graph: dict, visited: dict, component: list) -> None:
        visited[node] = True
        component.append(node)
        for neighbor in graph[node]:
            if not visited[neighbor]:
                dfs(neighbor, graph, visited, component)

    # Create an adjacency list
    for origin_set in origin_sets:
        for combination in combinations(origin_set, 2):
            graph[combination[0]].append(combination[1])
            graph[combination[1]].append(combination[0])

    visited = {node: False for node in graph}
    components = []

    for node in graph:
        if not visited[node]:
            component: List[str] = []
            dfs(node, graph, visited, component)
            components.append(sorted(component))

    return components
