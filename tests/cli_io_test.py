"""Tests for bibliography-io based CLI record file handling."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import bibliography_io
import pandas as pd
import pytest

from bib_dedupe.cli import build_parser
from bib_dedupe.cli import CLIError
from bib_dedupe.cli import parse_colrev_origin
from bib_dedupe.cli import read_records
from bib_dedupe.cli import write_records


def _sample_records() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID": "record-1",
                "ENTRYTYPE": "article",
                "title": "A preserved title",
                "author": "Example, Ada",
                "colrev_origin": "source-a.bib/001; source-b.bib/002",
                "colrev_masterdata_provenance": (
                    "{'title': {'source': 'source-a.bib/001', 'note': 'checked'}}"
                ),
                "custom_metadata": "Keep this field",
            }
        ]
    ).set_index("ID", drop=False)


def test_csv_bibtex_round_trip_preserves_ids_metadata_and_origins(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "records.csv"
    bibtex_path = tmp_path / "merged.bib"
    output_csv_path = tmp_path / "merged.csv"
    _sample_records().to_csv(input_path, index=False)

    records_df = read_records(input_path)
    assert records_df.loc["record-1", "ID"] == "record-1"
    assert records_df.loc["record-1", "custom_metadata"] == "Keep this field"

    write_records(records_df, bibtex_path)
    raw_records = bibliography_io.load_raw(
        bibtex_path,
        list_fields={"colrev_origin"},
        mapping_fields={"colrev_masterdata_provenance"},
    )
    assert len(raw_records) == 1
    assert raw_records[0]["ID"] == "record-1"
    assert raw_records[0]["custom_metadata"] == "Keep this field"
    assert raw_records[0]["colrev_origin"] == [
        "source-a.bib/001",
        "source-b.bib/002",
    ]
    assert raw_records[0]["colrev_masterdata_provenance"] == {
        "title": {"source": "source-a.bib/001", "note": "checked"}
    }

    bibtex_df = read_records(bibtex_path)
    assert parse_colrev_origin(bibtex_df.loc["record-1", "colrev_origin"]) == [
        "source-a.bib/001",
        "source-b.bib/002",
    ]
    write_records(bibtex_df, output_csv_path)

    csv_df = read_records(output_csv_path)
    assert csv_df.loc["record-1", "ID"] == "record-1"
    assert csv_df.loc["record-1", "custom_metadata"] == "Keep this field"
    assert parse_colrev_origin(csv_df.loc["record-1", "colrev_origin"]) == [
        "source-a.bib/001",
        "source-b.bib/002",
    ]


def test_read_records_rejects_duplicate_ids(tmp_path: Path) -> None:
    input_path = tmp_path / "duplicate_ids.csv"
    input_path.write_text(
        "ID,title\nrecord-1,First\nrecord-1,Second\n", encoding="utf-8"
    )

    with pytest.raises(CLIError, match="Duplicate record ID"):
        read_records(input_path)


def test_read_records_keeps_library_generated_ids(tmp_path: Path) -> None:
    input_path = tmp_path / "missing_id.csv"
    input_path.write_text("title\nNo identifier\n", encoding="utf-8")

    records_df = read_records(input_path)

    assert records_df["ID"].tolist() == ["000001"]
    assert read_records(input_path, generate_ids=True)["ID"].tolist() == ["000001"]


def test_read_records_can_select_an_alternate_id_field(tmp_path: Path) -> None:
    input_path = tmp_path / "alternate_id.csv"
    input_path.write_text(
        "ID,external_key,title\nrecord-1,source-001,First\nrecord-2,source-002,Second\n",
        encoding="utf-8",
    )

    records_df = read_records(input_path, id_field="external_key")

    assert records_df["ID"].tolist() == ["source-001", "source-002"]
    assert records_df.index.tolist() == ["source-001", "source-002"]


def test_read_records_rejects_duplicate_alternate_ids(tmp_path: Path) -> None:
    input_path = tmp_path / "duplicate_alternate_id.csv"
    input_path.write_text(
        "ID,external_key,title\nrecord-1,same,First\nrecord-2,same,Second\n",
        encoding="utf-8",
    )

    with pytest.raises(CLIError, match="duplicate value 'same'"):
        read_records(input_path, id_field="external_key")


def test_read_records_rejects_blank_alternate_ids(tmp_path: Path) -> None:
    input_path = tmp_path / "blank_alternate_id.csv"
    input_path.write_text(
        "ID,external_key,title\nrecord-1,,First\nrecord-2,source-002,Second\n",
        encoding="utf-8",
    )

    with pytest.raises(CLIError, match="contains empty values"):
        read_records(input_path, id_field="external_key")


def test_generate_ids_can_handle_missing_normalized_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bib_dedupe import cli

    monkeypatch.setattr(
        cli,
        "_bibliography_io",
        lambda: SimpleNamespace(load=lambda _: {"temporary": {"title": "Example"}}),
    )

    records_df = read_records(tmp_path / "records.csv", generate_ids=True)

    assert records_df["ID"].tolist() == ["000001"]
    assert records_df.index.tolist() == ["000001"]


def test_missing_normalized_id_fails_without_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bib_dedupe import cli

    monkeypatch.setattr(
        cli,
        "_bibliography_io",
        lambda: SimpleNamespace(load=lambda _: {"temporary": {"title": "Example"}}),
    )

    with pytest.raises(CLIError, match="No usable ID field"):
        read_records(tmp_path / "records.csv")


def test_record_id_cli_options_are_mutually_exclusive() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "merge",
                "-i",
                "records.csv",
                "-o",
                "merged.csv",
                "--id-field",
                "external_key",
                "--generate-ids",
            ]
        )


def test_read_records_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CLIError, match="Failed to load bibliographic records"):
        read_records(tmp_path / "missing.csv")


def test_write_records_rejects_non_writable_library_formats(
    tmp_path: Path,
) -> None:
    with pytest.raises(CLIError, match="Writing json is unsupported"):
        write_records(_sample_records(), tmp_path / "records.json")
