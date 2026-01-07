#! /usr/bin/env python
"""
Debug for dedupe — pick a CSV in the current directory (interactive),
then load records via CoLRev and continue with prep/block/match.
"""
from __future__ import annotations

from pathlib import Path

import colrev.loader.load_utils
import inquirer
import pandas as pd

import bib_dedupe.cluster
from bib_dedupe.bib_dedupe import block
from bib_dedupe.bib_dedupe import match
from bib_dedupe.bib_dedupe import prep


def _select_from_list(
    prompt: str, choices: list[str], multi: bool = False
) -> list[str] | str:
    """inquirer-first selection helper; falls back to terminal input."""
    try:
        if multi:
            q = [inquirer.Checkbox("sel", message=prompt, choices=choices)]
            ans = inquirer.prompt(q)
            if not ans or "sel" not in ans or not ans["sel"]:
                raise RuntimeError("Nothing selected.")
            return ans["sel"]
        else:
            q = [inquirer.List("sel", message=prompt, choices=choices)]
            ans = inquirer.prompt(q)
            if not ans or "sel" not in ans:
                raise RuntimeError("Nothing selected.")
            return ans["sel"]
    except ModuleNotFoundError:
        print("Optional dependency missing: `inquirer` (pip install inquirer).")
        for i, c in enumerate(choices, start=1):
            print(f"{i}: {c}")
        if multi:
            raw = input(f"{prompt} (comma-separated numbers): ").strip()
            idxs = [int(x) for x in raw.split(",") if x.strip()]
            return [choices[i - 1] for i in idxs]
        idx = int(input(f"{prompt} (number): ").strip())
        return choices[idx - 1]


def _select_csv_in_cwd() -> Path:
    csv_files = sorted(Path(".").glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No *.csv files found in the current directory.")
    selected = _select_from_list(
        "Select a CSV file", [p.name for p in csv_files], multi=False
    )
    return Path(str(selected))


def _load_records_df_via_colrev(filename: Path) -> pd.DataFrame:
    records = colrev.loader.load_utils.load(filename=str(filename))
    df = pd.DataFrame.from_dict(records, orient="index")

    # Only add index as ID if there isn't already an ID column
    if "ID" not in df.columns:
        df = df.reset_index().rename(columns={"index": "ID"})
    else:
        df = df.reset_index(drop=True)

    return df


def _select_components(records_df: pd.DataFrame) -> list[str]:
    if "component" not in records_df.columns:
        raise KeyError(
            "No 'component' column found. "
            "If this CSV is a matches/component list, it must contain a 'component' column."
        )

    comps = sorted(records_df["component"].dropna().astype(str).unique().tolist())
    selected = _select_from_list("Select component(s) to debug", comps, multi=True)
    return list(selected)


def debug() -> None:
    selected_csv = _select_csv_in_cwd()
    records_df = _load_records_df_via_colrev(selected_csv)

    selected_components = _select_components(records_df)
    subset_df = records_df[records_df["component"].isin(selected_components)].copy()

    prep_df = prep(subset_df)
    pairs_df = block(records_df=prep_df)
    matched_df = match(pairs_df, verbosity_level=2)
    print(matched_df)

    duplicate_id_sets = bib_dedupe.cluster.get_connected_components(matched_df)
    print(duplicate_id_sets)
