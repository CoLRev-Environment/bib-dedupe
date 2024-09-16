#! /usr/bin/env python
"""Utility to export and evaluate dedupe benchmarks."""
from __future__ import annotations

import time
import typing
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Optional

import pandas as pd
from tqdm import tqdm

import bib_dedupe.cluster
import bib_dedupe.util
from bib_dedupe.constants.fields import AUTHOR_FIRST
from bib_dedupe.constants.fields import CONTAINER_TITLE_SHORT
from bib_dedupe.constants.fields import DUPLICATE_LABEL
from bib_dedupe.constants.fields import ID
from bib_dedupe.constants.fields import MAYBE
from bib_dedupe.constants.fields import ORIGIN
from bib_dedupe.constants.fields import TITLE_SHORT

TP = "TP"
FP = "FP"
TN = "TN"
FN = "FN"
PRECISION = "precision"
SENSITIVITY = "sensitivity"
SPECIFICITY = "specificity"
FP_RATE = "false_positive_rate"
F1 = "f1"
RUNTIME = "runtime"

CASE = "case"


class DedupeBenchmarker:
    """Dedupe benchmarker"""

    # pylint: disable=too-many-instance-attributes

    true_merged_ids: list
    records_df: pd.DataFrame

    def __init__(
        self,
        *,
        benchmark_path: Optional[Path] = None,
        regenerate_benchmark_from_history: bool = False,
        colrev_project_path: Optional[Path] = None,
    ) -> None:
        if benchmark_path is None:
            benchmark_path = Path.cwd()
        self.benchmark_path = Path(benchmark_path).resolve()
        if colrev_project_path is None:
            self.colrev_project_path = benchmark_path
        else:
            self.colrev_project_path = colrev_project_path

        self.records_pre_merged_path = Path(
            self.benchmark_path, "records_pre_merged.csv"
        )
        self.merged_record_ids_path = Path(self.benchmark_path, "merged_record_ids.csv")
        if regenerate_benchmark_from_history:
            self.__get_dedupe_benchmark()
        else:
            self.__load_data()

    def __load_data(self) -> None:
        # print("after", self.true_merged_ids)

        if self.records_pre_merged_path.is_file():
            records_df = pd.read_csv(str(self.records_pre_merged_path))
            self.records_df = records_df
        else:
            part1_path = self.records_pre_merged_path.with_name(
                self.records_pre_merged_path.stem + "_part1.csv"
            )
            part2_path = self.records_pre_merged_path.with_name(
                self.records_pre_merged_path.stem + "_part2.csv"
            )

            if part1_path.is_file() and part2_path.is_file():
                part1_df = pd.read_csv(str(part1_path))
                self.records_df = part1_df
                part2_df = pd.read_csv(str(part2_path))
                self.records_df = pd.concat(
                    [self.records_df, part2_df], ignore_index=True
                )

        true_merged_ids_df = pd.read_csv(str(self.merged_record_ids_path))
        self.true_merged_ids = true_merged_ids_df["merged_ids"].str.split(";").tolist()

        # Validate
        non_unique_lists = []
        for merged_id_list in self.true_merged_ids:
            if len(merged_id_list) != len(set(merged_id_list)):
                non_unique_lists.append(merged_id_list)

        for non_unique_list in non_unique_lists:
            print(f"Duplicate strings found in: {non_unique_list}")

        if non_unique_lists:
            raise ValueError(
                "Each list in self.true_merged_ids should only contain unique strings"
            )

        all_ids_in_true_merged_ids = [
            id for sublist in self.true_merged_ids for id in sublist
        ]
        ids_not_in_records_df = set(all_ids_in_true_merged_ids) - set(
            self.records_df[ID].tolist()
        )
        if ids_not_in_records_df:
            print(f"IDs not found in records_df: {ids_not_in_records_df}")
            raise ValueError(
                "Not all ids in self.true_merged_ids are in self.records_df column ID"
            )

        # Validate: Ensure that there is no overlap between sets of self.true_merged_ids
        flattened_ids = [id for sublist in self.true_merged_ids for id in sublist]
        if len(flattened_ids) != len(set(flattened_ids)):
            from collections import Counter

            counter = Counter(flattened_ids)
            problem_ids = [id for id, count in counter.items() if count > 1]
            print(f"Problem IDs: {problem_ids}")
            raise ValueError("Overlap found between sets in self.true_merged_ids")

    def get_records_for_dedupe(self) -> pd.DataFrame:
        """
        Get (pre-processed) records for dedupe

        Returns:
            pd.DataFrame: Pre-processed records for dedupe
        """

        return self.records_df

    # pylint: disable=too-many-locals
    def __get_dedupe_benchmark(self) -> None:
        """Get benchmark for dedupe"""
        import colrev.review_manager
        import colrev.record

        STATUS = "colrev_status"

        def merged(record: dict) -> bool:
            return len([o for o in record[ORIGIN] if not o.startswith("md_")]) != 1

        self.review_manager = colrev.review_manager.ReviewManager(
            path_str=str(self.colrev_project_path), force_mode=True
        )
        self.dedupe_operation = self.review_manager.get_dedupe_operation()

        records = self.review_manager.dataset.load_records_dict()
        for record in records.values():
            if STATUS not in record:
                record[STATUS] = colrev.record.RecordState.md_processed
                print("setting missing status")

        # Select md-processed records (discard recently added/non-deduped ones)
        records = {
            r[ID]: r
            for r in records.values()
            if r[STATUS]
            in colrev.record.RecordState.get_post_x_states(
                state=colrev.record.RecordState.md_processed
            )
        }
        # Drop origins starting with md_... (not relevant for dedupe)
        for record_dict in records.values():
            record_dict[ORIGIN] = [
                o for o in record_dict[ORIGIN] if not o.startswith("md_")
            ]

        records_pre_merged_list = [r for r in records.values() if not merged(r)]
        records_merged_origins = [
            o
            for r in records.values()
            if merged(r)
            for o in r[ORIGIN]
            if not o.startswith("md_")
        ]

        nr_commits = self.review_manager.dataset.get_repo().git.rev_list(
            "--count", "HEAD"
        )
        for hist_recs in tqdm(
            self.review_manager.dataset.load_records_from_history(),
            total=int(nr_commits),
        ):
            if len(records_merged_origins) == 0:
                break

            try:
                for hist_record_dict in hist_recs.values():
                    if any(
                        o in hist_record_dict[ORIGIN] for o in records_merged_origins
                    ) and not merged(hist_record_dict):
                        # only consider post-md_prepared (non-merged) records
                        if hist_record_dict[
                            STATUS
                        ] in colrev.record.RecordState.get_post_x_states(
                            state=colrev.record.RecordState.md_prepared
                        ):
                            hist_record_dict[ORIGIN] = [
                                o
                                for o in hist_record_dict[ORIGIN]
                                if not o.startswith("md_")
                            ]
                            records_pre_merged_list.append(hist_record_dict)
                            records_merged_origins.remove(
                                [
                                    o
                                    for o in hist_record_dict[ORIGIN]
                                    if not o.startswith("md_")
                                ][0]
                            )

            except KeyError:
                break

        records_pre_merged = {r[ID]: r for r in records_pre_merged_list}

        # drop missing from records
        # (can only evaluate record/origins that are available in records_pre_merged)
        pre_merged_orgs = {o for r in records_pre_merged.values() for o in r[ORIGIN]}
        for record_dict in records.values():
            record_dict[ORIGIN] = [
                o
                for o in record_dict[ORIGIN]
                if o in pre_merged_orgs and o not in records_merged_origins
            ]
        records = {r[ID]: r for r in records.values() if len(r[ORIGIN]) > 0}

        assert {o for x in records_pre_merged.values() for o in x[ORIGIN]} == {
            o for x in records.values() for o in x[ORIGIN]
        }
        # [x for x in o_rec if x not in o_pre]

        records_pre_merged_df = pd.DataFrame.from_dict(
            records_pre_merged, orient="index"
        )
        self.records_pre_merged_df = records_pre_merged_df

        records_df = pd.DataFrame.from_dict(records, orient="index")
        self.records_df = records_df

        merged_record_ids = []
        for row in list(records_df.to_dict(orient="records")):
            if len(row[ID]) > 1:
                merged_record_ids.append(row[ID])

        self.true_merged_ids = merged_record_ids
        merged_record_ids_df = pd.DataFrame({"merged_ids": self.true_merged_ids})
        records_pre_merged_df.to_csv(str(self.records_pre_merged_path), index=False)
        merged_record_ids_df.to_csv(str(self.merged_record_ids_path), index=False)

    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    def compare(
        self,
        *,
        blocked_df: pd.DataFrame,
        predicted: list,
    ) -> dict:
        """Compare the predicted matches and blocked pairs to the ground truth."""

        ground_truth_pairs = set()
        for item in self.true_merged_ids:
            for combination in combinations(item, 2):
                ground_truth_pairs.add(";".join(sorted(combination)))

        blocked = blocked_df.apply(lambda row: [row[f"{ID}_1"], row[f"{ID}_2"]], axis=1)

        blocked_pairs = set()
        for item in blocked:
            for combination in combinations(item, 2):
                blocked_pairs.add(";".join(sorted(combination)))

        predicted_pairs = set()
        for item in predicted:
            for combination in combinations(item, 2):
                predicted_pairs.add(";".join(sorted(combination)))

        blocks = {TP: 0, FP: 0, TN: 0, FN: 0}
        blocks_fn_list = []
        matches = {TP: 0, FP: 0, TN: 0, FN: 0}
        matches_fp_list = []
        matches_fn_list = []

        all_ids = self.records_df[ID].tolist()

        # Note: the following takes long:
        for combination in combinations(all_ids, 2):
            pair = ";".join(sorted(combination))

            if pair in blocked_pairs:
                if pair in ground_truth_pairs:
                    blocks[TP] += 1
                else:
                    blocks[FP] += 1
                    # Don't need a list here.
            else:
                if pair in ground_truth_pairs:
                    blocks[FN] += 1
                    blocks_fn_list.append(combination)
                else:
                    blocks[TN] += 1

            if pair in predicted_pairs:
                if pair in ground_truth_pairs:
                    matches[TP] += 1
                else:
                    matches[FP] += 1
                    matches_fp_list.append(combination)
            else:
                if pair in ground_truth_pairs:
                    matches[FN] += 1
                    matches_fn_list.append(combination)
                else:
                    matches[TN] += 1

        return {
            "matches": matches,
            "blocks_FN_list": blocks_fn_list,
            "matches_FP_list": matches_fp_list,
            "matches_FN_list": matches_fn_list,
            "blocks": blocks,
        }

    def get_runtime(self, timestamp: datetime) -> str:
        """
        Calculate the runtime.

        Args:
            timestamp (datetime.datetime): The timestamp when the deduplication was started.

        Returns:
            str: The runtime in the format "hours:minutes:seconds".
        """
        start_time = datetime.now()
        time_diff = start_time - timestamp
        runtime_in_minutes = time_diff.total_seconds() / 60

        runtime_in_hours = runtime_in_minutes / 60
        hours = int(runtime_in_hours)
        minutes = (runtime_in_hours * 60) % 60
        seconds = (runtime_in_hours * 3600) % 60
        runtime_string = f"{hours}:{int(minutes):02d}:{int(seconds):02d}"
        print(f"Runtime: {runtime_string}")
        return runtime_string

    def compare_dedupe_id(
        self,
        *,
        records_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        timestamp: datetime,
    ) -> pd.DataFrame:
        """
        Compare dedupe IDs and calculate evaluation metrics.

        Args:
            records_df (pd.DataFrame): DataFrame containing the original records.
            merged_df (pd.DataFrame): DataFrame containing the merged records.
            timestamp (datetime.datetime): The timestamp when the deduplication was started.

        Returns:
            pd.DataFrame: DataFrame containing the evaluation metrics.
        """

        results: typing.Dict[str, typing.Any] = {
            TP: 0,
            FP: 0,
            FN: 0,
            TN: 0,
            RUNTIME: self.get_runtime(timestamp),
        }

        all_ids = records_df[ID].tolist()

        true_non_duplicate_ids = [
            x for x in all_ids if not any(x in y for y in self.true_merged_ids)
        ]

        # Assume that IDs are not changed (merged IDs are not available)
        # For each ID-set, **exactly one** must be in the merged_df

        for true_non_duplicate_id in true_non_duplicate_ids:
            if true_non_duplicate_id in merged_df[ID].tolist():
                results[TN] += 1
            else:
                results[FP] += 1

        for true_merged_id_set in self.true_merged_ids:
            nr_in_merged_df = merged_df[merged_df[ID].isin(true_merged_id_set)].shape[0]
            # One would always be required to be a non-duplicate (true value:negative)
            # All that are removed are true positive, all that are not removed are false negatives
            if nr_in_merged_df == 0:
                results[FP] += 1
                results[TP] += len(true_merged_id_set) - 1
            elif nr_in_merged_df >= 1:
                results[TN] += 1
                results[FN] += nr_in_merged_df - 1
                results[TP] += len(true_merged_id_set) - nr_in_merged_df

        results[FP_RATE] = results[FP] / (results[FP] + results[TN])

        results[SPECIFICITY] = results[TN] / (results[TN] + results[FP])
        results[SENSITIVITY] = results[TP] / (results[TP] + results[FN])
        if (results[TP] + results[FP]) > 0:
            results[PRECISION] = results[TP] / (results[TP] + results[FP])
        else:
            results[PRECISION] = 0.0
        if (results[PRECISION] + results[SENSITIVITY]) > 0:
            results[F1] = (
                2
                * (results[PRECISION] * results[SENSITIVITY])
                / (results[PRECISION] + results[SENSITIVITY])
            )
        else:
            results[F1] = 0.0

        results["dataset"] = Path(self.benchmark_path).name

        return results

    def export_cases(
        self,
        *,
        prepared_records_df: pd.DataFrame,
        blocked_df: pd.DataFrame,
        matched_df: pd.DataFrame,
    ) -> None:
        """Get the cases for results

        records_df = [ID, title, author, ...]
        blocked_df = ...
        results = {"blocks_FN_list", "matches_FP_list", "matches_FN_list"}
        """

        maybe_cases_df = matched_df[matched_df[DUPLICATE_LABEL] == MAYBE].copy()

        columns_to_drop = [
            TITLE_SHORT,
            AUTHOR_FIRST,
            CONTAINER_TITLE_SHORT,
            ORIGIN,
        ]
        prepared_records_df = prepared_records_df.drop(
            columns=[
                col for col in columns_to_drop if col in prepared_records_df.columns
            ]
        )

        maybe_cases_df.loc[:, CASE] = (
            maybe_cases_df[f"{ID}_1"] + ";" + maybe_cases_df[f"{ID}_2"]
        )
        maybe_df_copy = maybe_cases_df.copy()
        maybe_df_1 = pd.merge(
            maybe_df_copy,
            prepared_records_df,
            left_on=f"{ID}_2",
            right_on=ID,
            how="inner",
        )
        maybe_df_2 = pd.merge(
            maybe_cases_df,
            prepared_records_df,
            left_on=f"{ID}_1",
            right_on=ID,
            how="inner",
        )

        maybe_df = pd.concat([maybe_df_1, maybe_df_2])
        maybe_df = maybe_df.sort_values(by=CASE)
        maybe_df = maybe_df.drop(columns=[f"{ID}_1", f"{ID}_2", DUPLICATE_LABEL])

        maybe_df.to_csv(self.benchmark_path / "maybe_pairs.csv", index=False)

        print("Export started at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        start_time = time.time()

        duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)

        results = self.compare(
            blocked_df=blocked_df,
            predicted=duplicate_id_sets,
        )

        for list_name in [
            "blocks_FN_list",
            "matches_FP_list",
            "matches_FN_list",
        ]:
            id_pairs = results[list_name]

            id_pairs_cases_df = pd.DataFrame(id_pairs, columns=[f"{ID}_1", f"{ID}_2"])
            id_pairs_cases_df.loc[:, CASE] = (
                id_pairs_cases_df[f"{ID}_1"] + ";" + id_pairs_cases_df[f"{ID}_2"]
            )

            id_pairs_cases_df_copy = id_pairs_cases_df.copy()
            id_pairs_df_1 = pd.merge(
                id_pairs_cases_df_copy,
                prepared_records_df,
                left_on=f"{ID}_2",
                right_on=ID,
                how="inner",
            )
            id_pairs_df_2 = pd.merge(
                id_pairs_cases_df,
                prepared_records_df,
                left_on=f"{ID}_1",
                right_on=ID,
                how="inner",
            )

            cases_df = pd.concat([id_pairs_df_1, id_pairs_df_2])
            cases_df = cases_df.sort_values(by=CASE)
            cases_df = cases_df.drop(columns=[f"{ID}_1", f"{ID}_2"])

            if not cases_df.empty:
                cases_df = cases_df[
                    [CASE, ID]
                    + [col for col in cases_df.columns if col not in [CASE, ID]]
                ]
                cases_df = cases_df.sort_values(by=[CASE, ID])

                if cases_df.empty:
                    continue

            cases_df.to_csv(self.benchmark_path / f"{list_name}.csv", index=False)

            ignored_file = self.benchmark_path / f"{list_name}_ignored.csv"
            if not ignored_file.is_file():
                continue
            try:
                ignored_df = pd.read_csv(ignored_file)
                cases_df = cases_df[~cases_df[CASE].isin(ignored_df[CASE])]
                cases_df.to_csv(
                    self.benchmark_path / f"{list_name}_remaining.csv", index=False
                )
            except KeyError as exc:
                print(exc)

        end_time = time.time()
        print(f"Export completed after: {end_time - start_time:.2f} seconds")
