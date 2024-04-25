#! /usr/bin/env python
"""Utils for evaluation"""
from __future__ import annotations

import datetime
from pathlib import Path

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
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR


def get_dataset_labels() -> list:
    """
    Get the directory names in data
    """
    data_path = Path(__file__).parent.parent / "data"
    return [
        dir.name
        for dir in data_path.iterdir()
        if dir.is_dir() and dir.name != "__pycache__"
    ]


def export_for_pytest(
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

    records_df.to_csv(str(benchmark_path / Path("records_pre_merged.csv")), index=False)

    merged_record_ids_df = pd.DataFrame({"case": true_merged_ids})
    merged_record_ids_df.to_csv(
        str(benchmark_path / Path("merged_record_ids.csv")), index=False
    )


def create_plot(dataset_df: pd.DataFrame) -> None:
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
    plt.savefig(str(Path("../docs/_static/evaluation_total.png")))
    plt.close()


def append_to_output(result: dict, *, package_name: str) -> None:
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
        total_df = (
            dataset_df.drop_duplicates(subset=["package", "dataset"], keep="first")
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
        total_df = total_df.sort_values(by=["false_positive_rate"], ascending=[True])
        f.write(total_df.to_markdown(index=False))

        create_plot(dataset_df=dataset_df)

        f.write("\n\n")
        f.write("# Individual datasets\n\n")
        for dataset in results_df["dataset"].unique():
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
            dataset_df["false_positive_rate"] = dataset_df["FP"] / (
                dataset_df["FP"] + dataset_df["TN"]
            )
            dataset_df["false_positive_rate"] = dataset_df["false_positive_rate"].round(
                4
            )
            dataset_df["specificity"] = dataset_df["specificity"].round(4)
            dataset_df["sensitivity"] = dataset_df["sensitivity"].round(4)
            dataset_df["precision"] = dataset_df["precision"].round(4)
            dataset_df["f1"] = dataset_df["f1"].round(4)
            dataset_df = dataset_df.sort_values(by=["f1"], ascending=[False])
            f.write(dataset_df.to_markdown(index=False))
            f.write("\n\n")
