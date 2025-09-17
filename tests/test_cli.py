"""Integration tests for the bib-dedupe command line interface."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import pytest

from bib_dedupe.bib_dedupe import load_example_data


@contextmanager
def working_directory(path: Path) -> None:
    """Temporarily change the working directory for the duration of a context."""

    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    """Execute the CLI using ``python -m bib_dedupe.cli`` within *tmp_path*."""

    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[1]
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, "-m", "bib_dedupe.cli", *args]
    return subprocess.run(cmd, cwd=tmp_path, env=env, check=True, capture_output=True)


@pytest.fixture()
def example_records(tmp_path: Path) -> Path:
    """Prepare example stroke records for use in CLI tests."""

    repo_root = Path(__file__).resolve().parents[1]
    local_copy = tmp_path / "stroke.csv"
    shutil.copy(repo_root / "data" / "stroke" / "records_pre_merged.csv", local_copy)

    with working_directory(tmp_path):
        df = load_example_data("stroke")

    if "container_title" not in df.columns:
        df["container_title"] = df.get("journal", "")
    if "doi" not in df.columns:
        df["doi"] = ""
    if "abstract" not in df.columns:
        df["abstract"] = ""

    records_path = tmp_path / "records.csv"
    df.to_csv(records_path, index=False)
    return records_path


def test_merge_end_to_end(tmp_path: Path, example_records: Path) -> None:
    merged_path = tmp_path / "merged.csv"
    run_cli(tmp_path, "merge", "-i", str(example_records), "-o", str(merged_path))

    assert merged_path.exists()
    merged_df = pd.read_csv(merged_path)
    input_df = pd.read_csv(example_records)
    assert 0 < len(merged_df) <= len(input_df)


def test_stepwise_pipeline(tmp_path: Path, example_records: Path) -> None:
    prep_path = tmp_path / "prep.csv"
    block_path = tmp_path / "pairs.csv"
    match_path = tmp_path / "matches.csv"
    match_maybe_path = tmp_path / "matches_with_maybe.csv"
    imported_path = tmp_path / "matches_imported.csv"
    merged_path = tmp_path / "merged_after_import.csv"

    run_cli(tmp_path, "prep", "-i", str(example_records), "-o", str(prep_path))
    run_cli(tmp_path, "block", "-i", str(prep_path), "-o", str(block_path))
    run_cli(tmp_path, "match", "-i", str(block_path), "-o", str(match_path))

    prep_df = pd.read_csv(prep_path)
    assert {"ID", "title"}.issubset(set(prep_df.columns))

    pairs_df = pd.read_csv(block_path)
    assert {"ID_1", "ID_2"}.issubset(set(pairs_df.columns))

    matches_df = pd.read_csv(match_path)
    assert "duplicate_label" in {col.lower() for col in matches_df.columns}

    run_cli(
        tmp_path,
        "match",
        "-i",
        str(block_path),
        "-o",
        str(match_maybe_path),
        "--export-maybe",
        "--records",
        str(example_records),
    )

    maybe_file = tmp_path / "maybe_cases.csv"
    assert maybe_file.exists()

    run_cli(
        tmp_path,
        "import-maybe",
        "-i",
        str(match_maybe_path),
        "-o",
        str(imported_path),
    )
    assert imported_path.exists()

    run_cli(
        tmp_path,
        "merge",
        "-i",
        str(example_records),
        "-o",
        str(merged_path),
        "--import-maybe",
    )
    assert merged_path.exists()
