#! /usr/bin/env python
"""BibDedupe utility"""
from __future__ import annotations

import datetime
import pprint
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import List

import pandas as pd

from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import BOOKTITLE
from bib_dedupe.constants.fields import CHAPTER
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import EDITOR
from bib_dedupe.constants.fields import ENTRYTYPE
from bib_dedupe.constants.fields import ID
from bib_dedupe.constants.fields import INSTITUTION
from bib_dedupe.constants.fields import ISBN
from bib_dedupe.constants.fields import JOURNAL
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import PUBLISHER
from bib_dedupe.constants.fields import STATUS
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR

# pylint: disable=too-few-public-methods


class VerbosePrint:
    def __init__(self, verbosity_level: int):
        self.verbosity_level = verbosity_level

    def print(self, message: str, *, level: int = 1) -> None:
        if level <= self.verbosity_level:
            print(message)


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
        true_merged_ids: list,
        benchmark_path: Path,
    ) -> None:
        """
        Export the benchmark data for pytest.

        Args:
            target_path (Path): The path to export the benchmark data to.
        """
        benchmark_path.mkdir(parents=True, exist_ok=True)

        records_df = records_df.copy()

        records_df = records_df[
            records_df.columns.intersection(
                [
                    ID,
                    ENTRYTYPE,
                    STATUS,
                    TITLE,
                    AUTHOR,
                    YEAR,
                    JOURNAL,
                    BOOKTITLE,
                    CHAPTER,
                    PUBLISHER,
                    VOLUME,
                    NUMBER,
                    PAGES,
                    EDITOR,
                    INSTITUTION,
                    DOI,
                    ISBN,
                    ABSTRACT,
                ]
            )
        ]

        records_df.to_csv(
            str(benchmark_path / Path("records_pre_merged.csv")), index=False
        )

        merged_record_ids_df = pd.DataFrame({"case": true_merged_ids})
        merged_record_ids_df.to_csv(
            str(benchmark_path / Path("merged_record_ids.csv")), index=False
        )

    def add_external_evaluations(self, dataset_df: pd.DataFrame) -> pd.DataFrame:
        performance_data_depression = pd.DataFrame(
            [
                {
                    "package": "Human (Hair et al. 2021)",
                    "TP": 9390,
                    "TN": 69793,
                    "FN": 669,
                    "FP": 28,
                    "sensitivity": 0.933,
                    "specificity": 0.999,
                    "precision": 0.997,
                    "f1": 0.964,
                    "runtime": "Unknown",
                },
                {
                    "package": "Endnote (Hair et al. 2021)",
                    "TP": 7531,
                    "TN": 69816,
                    "FN": 2528,
                    "FP": 5,
                    "sensitivity": 0.749,
                    "specificity": 0.999,
                    "precision": 0.999,
                    "f1": 0.856,
                    "runtime": "<30 minutes",
                },
                {
                    "package": "SRA-DM (Hair et al. 2021)",
                    "TP": 9448,
                    "TN": 68473,
                    "FN": 611,
                    "FP": 1348,
                    "sensitivity": 0.939,
                    "specificity": 0.980,
                    "precision": 0.875,
                    "f1": 0.906,
                    "runtime": "~48 hours",
                },
                {
                    "package": "ASySD (Hair et al. 2021)",
                    "TP": 9624,
                    "TN": 69749,
                    "FN": 435,
                    "FP": 72,
                    "sensitivity": 0.957,
                    "specificity": 0.999,
                    "precision": 0.993,
                    "f1": 0.974,
                    "runtime": "<1 hour",
                },
            ]
        )

        performance_data_neuroimaging = pd.DataFrame(
            [
                {
                    "package": "Human (Hair et al. 2021)",
                    "TP": 1274,
                    "TN": 2139,
                    "FN": 19,
                    "FP": 6,
                    "sensitivity": 0.985,
                    "specificity": 0.997,
                    "precision": 0.996,
                    "f1": 0.990,
                    "runtime": "Unknown",
                },
                {
                    "package": "Endnote (Hair et al. 2021)",
                    "TP": 983,
                    "TN": 2142,
                    "FN": 310,
                    "FP": 3,
                    "sensitivity": 0.760,
                    "specificity": 0.999,
                    "precision": 0.997,
                    "f1": 0.863,
                    "runtime": "<5 minutes",
                },
                {
                    "package": "SRA-DM (Hair et al. 2021)",
                    "TP": 1050,
                    "TN": 2103,
                    "FN": 243,
                    "FP": 42,
                    "sensitivity": 0.812,
                    "specificity": 0.980,
                    "precision": 0.962,
                    "f1": 0.880,
                    "runtime": "<5 minutes",
                },
                {
                    "package": "ASySD (Hair et al. 2021)",
                    "TP": 1278,
                    "TN": 2141,
                    "FN": 15,
                    "FP": 4,
                    "sensitivity": 0.988,
                    "specificity": 0.998,
                    "precision": 0.997,
                    "f1": 0.993,
                    "runtime": "<5 minutes",
                },
            ]
        )

        performance_data_diabetes = pd.DataFrame(
            [
                {
                    "package": "Human (Hair et al. 2021)",
                    "TP": 893,
                    "TN": 581,
                    "FN": 368,
                    "FP": 3,
                    "sensitivity": 0.708,
                    "specificity": 0.995,
                    "precision": 0.997,
                    "f1": 0.828,
                    "runtime": "Unknown",
                },
                {
                    "package": "Endnote (Hair et al. 2021)",
                    "TP": 1218,
                    "TN": 584,
                    "FN": 43,
                    "FP": 0,
                    "sensitivity": 0.966,
                    "specificity": 1.0,
                    "precision": 1.0,
                    "f1": 0.983,
                    "runtime": "<5 minutes",
                },
                {
                    "package": "SRA-DM (Hair et al. 2021)",
                    "TP": 1147,
                    "TN": 514,
                    "FN": 114,
                    "FP": 70,
                    "sensitivity": 0.910,
                    "specificity": 0.880,
                    "precision": 0.942,
                    "f1": 0.926,
                    "runtime": "<5 minutes",
                },
                {
                    "package": "ASySD (Hair et al. 2021)",
                    "TP": 1259,
                    "TN": 584,
                    "FN": 2,
                    "FP": 0,
                    "sensitivity": 0.998,
                    "specificity": 1.0,
                    "precision": 1.0,
                    "f1": 0.999,
                    "runtime": "<5 minutes",
                },
            ]
        )

        performance_data_cardiac = pd.DataFrame(
            [
                {
                    "package": "Human (Hair et al. 2021)",
                    "TP": 3136,
                    "TN": 5421,
                    "FN": 374,
                    "FP": 17,
                    "sensitivity": 0.893,
                    "specificity": 0.997,
                    "precision": 0.995,
                    "f1": 0.941,
                    "runtime": "Unknown",
                },
                {
                    "package": "Endnote (Hair et al. 2021)",
                    "TP": 2734,
                    "TN": 5435,
                    "FN": 776,
                    "FP": 3,
                    "sensitivity": 0.779,
                    "specificity": 0.999,
                    "precision": 0.999,
                    "f1": 0.875,
                    "runtime": "<5 minutes",
                },
                {
                    "package": "SRA-DM (Hair et al. 2021)",
                    "TP": 1149,
                    "TN": 5163,
                    "FN": 2361,
                    "FP": 275,
                    "sensitivity": 0.327,
                    "specificity": 0.949,
                    "precision": 0.807,
                    "f1": 0.466,
                    "runtime": "<30 minutes",
                },
                {
                    "package": "ASySD (Hair et al. 2021)",
                    "TP": 3503,
                    "TN": 5434,
                    "FN": 7,
                    "FP": 4,
                    "sensitivity": 0.998,
                    "specificity": 0.999,
                    "precision": 0.999,
                    "f1": 0.998,
                    "runtime": "<5 minutes",
                },
            ]
        )

        current_time = datetime.datetime.now()
        performance_data_depression["time"] = current_time.strftime("%Y-%m-%d %H:%M")
        performance_data_depression["dataset"] = "depression"
        performance_data_depression[
            "false_positive_rate"
        ] = performance_data_depression["FP"] / (
            performance_data_depression["FP"] + performance_data_depression["TN"]
        )
        performance_data_neuroimaging["time"] = current_time.strftime("%Y-%m-%d %H:%M")
        performance_data_neuroimaging["dataset"] = "neuroimaging"
        performance_data_neuroimaging[
            "false_positive_rate"
        ] = performance_data_neuroimaging["FP"] / (
            performance_data_neuroimaging["FP"] + performance_data_neuroimaging["TN"]
        )
        performance_data_diabetes["time"] = current_time.strftime("%Y-%m-%d %H:%M")
        performance_data_diabetes["dataset"] = "diabetes"
        performance_data_diabetes["false_positive_rate"] = performance_data_diabetes[
            "FP"
        ] / (performance_data_diabetes["FP"] + performance_data_diabetes["TN"])
        performance_data_cardiac["time"] = current_time.strftime("%Y-%m-%d %H:%M")
        performance_data_cardiac["dataset"] = "cardiac"
        performance_data_cardiac["false_positive_rate"] = performance_data_cardiac[
            "FP"
        ] / (performance_data_cardiac["FP"] + performance_data_cardiac["TN"])

        dataset_df = pd.concat(
            [
                dataset_df,
                performance_data_depression,
                performance_data_neuroimaging,
                performance_data_diabetes,
                performance_data_cardiac,
            ],
            ignore_index=True,
        )
        return dataset_df

    def create_plot(self, dataset_df: pd.DataFrame) -> None:
        try:
            import matplotlib.pyplot as plt
        except ModuleNotFoundError:
            return

        grouped_df = (
            dataset_df.groupby(["package"], group_keys=True)
            .apply(lambda x: x.sort_values("time").tail(1))
            .sort_values("FP", ascending=False)
            .reset_index(drop=True)
        )

        plt.figure(figsize=(14, 3))
        plt.suptitle(
            "Evaluation overall (10 datasets, 160,000 papers)",
            fontsize=14,
            fontweight="bold",
        )  # Added dataset as subheading title
        ax1 = plt.subplot(121)
        grouped_df.plot(ax=ax1, x="package", y="false_positive_rate", kind="barh")
        plt.title("False positive rate by package")
        plt.legend().remove()
        plt.ylabel("")
        for p in ax1.patches:
            ax1.annotate(
                f"{p.get_width():.2f}",
                (p.get_width(), p.get_y() + p.get_height() / 2),
                ha="left",
                va="center",
            )

        ax2 = plt.subplot(122)
        grouped_df.plot(ax=ax2, x="package", y="sensitivity", kind="barh")
        plt.title("Sensitivity by package")
        plt.legend().remove()
        plt.ylabel("")
        for p in ax2.patches:
            ax2.annotate(
                f"{p.get_width():.2f}",
                (p.get_width(), p.get_y() + p.get_height() / 2),
                ha="left",
                va="center",
            )

        latest_time = dataset_df["time"].max()
        plt.figtext(
            0.5,
            0.001,
            f"Time of last evaluation run: {latest_time}",
            ha="center",
            fontsize=10,
        )

        plt.tight_layout()
        # plt.show()
        plt.savefig(str(Path("../output/evaluation_total.png")))
        plt.close()

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
            # Overall summary
            f.write("# Summary for datasets combined\n\n")

            dataset_df = results_df.sort_values(by="time", ascending=False)
            dataset_df = self.add_external_evaluations(dataset_df)
            total_df = (
                dataset_df[dataset_df["dataset"] != "problem_cases"]
                .drop_duplicates(subset=["package", "dataset"], keep="first")
                .groupby(["package"])
                .sum(numeric_only=True)
                .reset_index()
            )

            total_df["false_positive_rate"] = total_df["FP"] / (
                total_df["FP"] + total_df["TN"]
            )
            total_df["specificity"] = total_df["TN"] / (total_df["TN"] + total_df["FP"])
            total_df["sensitivity"] = total_df["TP"] / (total_df["TP"] + total_df["FN"])
            total_df["precision"] = total_df["TP"] / (total_df["TP"] + total_df["FP"])
            total_df["f1"] = 2 * (
                (total_df["precision"] * total_df["sensitivity"])
                / (total_df["precision"] + total_df["sensitivity"])
            )

            total_df = total_df[
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
            total_df = total_df.sort_values(
                by=["false_positive_rate"], ascending=[True]
            )
            f.write(total_df.to_markdown(index=False))

            self.create_plot(dataset_df=dataset_df)

            f.write("\n\n")
            f.write("# Individual datasets\n\n")
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
                        "runtime",
                    ]
                ]
                # dataset_df = self.add_external_evaluations(dataset_df, dataset)
                dataset_df["false_positive_rate"] = dataset_df["FP"] / (
                    dataset_df["FP"] + dataset_df["TN"]
                )
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


def connected_components(id_sets: list) -> list:
    """
    Find the connected components in a graph.

    Args:
        id_sets (list): A list of id sets.

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
    for id_set in id_sets:
        for combination in combinations(id_set, 2):
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
