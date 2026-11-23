#! /usr/bin/env python
"""Command-line interface for :mod:`bib_dedupe`."""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import typing
from collections.abc import Sequence
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

import pandas as pd

from bib_dedupe import cluster as _cluster
from bib_dedupe import maybe_cases
from bib_dedupe.bib_dedupe import block
from bib_dedupe.bib_dedupe import export_maybe
from bib_dedupe.bib_dedupe import import_maybe
from bib_dedupe.bib_dedupe import match
from bib_dedupe.bib_dedupe import merge
from bib_dedupe.bib_dedupe import prep


class CLIError(Exception):
    """Raised for command-line usage errors."""


@dataclass
class RuntimeOptions:
    """Common runtime options passed to library functions."""

    cpu: int
    verbosity_level: int | None


# ----------------------------- I/O helpers --------------------------------- #
def _bibliography_io() -> typing.Any:
    """Import the optional bibliography I/O dependency when it is needed."""
    try:
        import bibliography_io
    except ImportError as exc:
        raise CLIError(
            "Bibliographic file I/O requires 'bibliography-io'. "
            "Install it with `pip install 'bib-dedupe[cli]'`."
        ) from exc
    return bibliography_io


def _validated_record_ids(values: pd.Series, *, field: str, path: Path) -> pd.Series:
    """Return normalized IDs after checking for blanks and duplicates."""
    ids = values.astype("string").str.strip()
    missing = ids.isna() | ids.eq("") | ids.str.casefold().eq("nan")
    if missing.any():
        raise CLIError(f"Record ID field {field!r} contains empty values in {path}.")

    duplicates = ids[ids.duplicated(keep=False)]
    if not duplicates.empty:
        duplicate_id = duplicates.iloc[0]
        raise CLIError(
            f"Record ID field {field!r} contains duplicate value {duplicate_id!r} in {path}."
        )
    return ids


def read_records(
    path: Path,
    *,
    id_field: str | None = None,
    generate_ids: bool = False,
) -> pd.DataFrame:
    """Load records and validate or explicitly select their record IDs."""
    if id_field is not None and generate_ids:
        raise CLIError("--id-field and --generate-ids cannot be used together.")

    bibliography_io = _bibliography_io()
    try:
        records = bibliography_io.load(path)
        if path.suffix.lower() == ".bib":
            structured_fields = {
                "colrev_origin",
                "colrev_masterdata_provenance",
                "colrev_data_provenance",
            }
            raw_records = bibliography_io.load_raw(
                path,
                list_fields={"colrev_origin"},
                mapping_fields=structured_fields - {"colrev_origin"},
            )
            for raw_record in raw_records:
                record_id = raw_record.get("ID")
                if record_id in records:
                    for field in structured_fields:
                        if field in raw_record:
                            records[record_id][field] = raw_record[field]
        records_df = pd.DataFrame.from_dict(records, orient="index")
    except Exception as exc:
        raise CLIError(
            f"Failed to load bibliographic records from {path}: {exc}"
        ) from exc

    if id_field is not None:
        if id_field not in records_df.columns:
            raise CLIError(
                f"ID field {id_field!r} was not found in records loaded from {path}."
            )
        ids = _validated_record_ids(records_df[id_field], field=id_field, path=path)
    else:
        ids = None
        if "ID" in records_df.columns:
            try:
                ids = _validated_record_ids(records_df["ID"], field="ID", path=path)
            except CLIError:
                if not generate_ids:
                    raise

        if ids is None:
            if not generate_ids:
                raise CLIError(
                    f"No usable ID field was returned for records loaded from {path}. "
                    "Specify --id-field or opt in with --generate-ids."
                )
            ids = pd.Series(
                [f"{number:06d}" for number in range(1, len(records_df) + 1)],
                index=records_df.index,
                dtype="string",
            )
        else:
            expected_ids = pd.Series(
                records_df.index, index=records_df.index, dtype="string"
            )
            if not ids.equals(expected_ids):
                if not generate_ids:
                    raise CLIError(
                        f"Record IDs loaded from {path} do not match their index."
                    )
                ids = None

        if ids is None:
            ids = pd.Series(
                [f"{number:06d}" for number in range(1, len(records_df) + 1)],
                index=records_df.index,
                dtype="string",
            )

    records_df["ID"] = ids.astype(str)
    records_df.index = pd.Index(records_df["ID"].to_numpy())

    # Generic normalization omits fields whose values are empty in every row.
    # Manual-review export expects these bibliographic columns to be present.
    for column in maybe_cases.FIELDS_TO_EXPORT[3:]:
        if column not in records_df.columns:
            records_df[column] = ""

    return records_df


def _read_command_records(path: Path, args: argparse.Namespace) -> pd.DataFrame:
    """Load records using ID options from the parsed command arguments."""
    return read_records(
        path,
        id_field=getattr(args, "id_field", None),
        generate_ids=getattr(args, "generate_ids", False),
    )


def read_df(path: Path) -> pd.DataFrame:
    """Load a dataframe from *path* based on its file extension."""

    if not path.exists():
        raise CLIError(f"Input file not found: {path}")

    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            return pd.read_csv(path, keep_default_na=False, low_memory=False)
        if suffix in {".parquet", ".pq"}:
            try:
                return pd.read_parquet(path)
            except ImportError as exc:  # pragma: no cover - depends on optional backend
                raise CLIError(
                    "Parquet support requires an optional dependency such as 'pyarrow'."
                ) from exc
        if suffix == ".json":
            return pd.read_json(path)
    except ValueError as exc:
        raise CLIError(f"Failed to read {path}: {exc}") from exc

    raise CLIError(
        "Unsupported file extension for input. Supported extensions: .csv, .parquet, .json"
    )


def _ensure_output_path(path: Path) -> Path:
    if path.suffix:
        return path
    return path.with_suffix(".csv")


def parse_colrev_origin(value: typing.Any) -> list[str]:
    """Return a clean list like ['dblp.bib/000591', 'files.bib/000037'] from messy inputs."""
    # Already a list → normalize & dedupe
    if isinstance(value, list):
        seen, out = set(), []
        for x in value:
            t = str(x).strip()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return out

    # Not a string → nothing usable
    if not isinstance(value, str):
        return []

    s = value.strip()
    if not s:
        return []

    # Fix common broken joiners/separators from bib exports
    s = (
        s.replace("'];['", ",")
        .replace("';['", ",")
        .replace("']['", ",")
        .replace("];[", ",")
        .replace("] ; [", ",")
        .replace(";", ",")
    )

    # Strip trailing commas
    while s.endswith(","):
        s = s[:-1].strip()

    # Repeatedly strip outer quotes/braces/brackets
    # (handles "'[...]'", "{[...]}", "{{[...]}}", etc.)
    while len(s) >= 2 and (
        (s[0] in "'\"" and s[-1] == s[0])
        or (s[0] == "{" and s[-1] == "}")
        or (s[0] == "[" and s[-1] == "]")
    ):
        s = s[1:-1].strip()

    # Try proper parsers first
    parsers: tuple[typing.Callable[[str], typing.Any], ...] = (
        json.loads,
        ast.literal_eval,
    )
    for parser in parsers:
        try:
            parsed = parser(s)
            if isinstance(parsed, list):
                return parse_colrev_origin(parsed)  # normalize/dedupe
        except Exception:
            pass

    # Last-resort: extract tokens that look like "source.bib/000123"
    candidates = re.findall(r"[A-Za-z0-9._-]+(?:\.bib)?/[A-Za-z0-9._-]+", s)
    # Dedupe while preserving order
    seen, out = set(), []
    for tok in candidates:
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


def maybe_cast_literal(value: typing.Any) -> typing.Any:
    """Parse list/dict-ish strings (incl. BibTeX double-braced) into Python objects."""
    if not isinstance(value, str):
        return value

    s = value.strip()

    # Trim a trailing comma (common in .bib exports)
    if s.endswith(","):
        s = s[:-1].strip()

    # Unwrap quotes if the whole thing is quoted: "'[... ]'" or '"{ ... }"'
    if len(s) >= 2 and s[0] in ("'", '"') and s[-1] == s[0]:
        inner = s[1:-1].strip()
        # Only unwrap if the inner looks like a literal container
        if (inner.startswith("[") and inner.endswith("]")) or (
            inner.startswith("{") and inner.endswith("}")
        ):
            s = inner

    # Handle BibTeX-style double braces: {{ ... }}
    if s.startswith("{{") and s.endswith("}}"):
        s = s[1:-1].strip()

    # If it doesn't look like a literal, skip work
    if not (
        (s.startswith("{") and s.endswith("}"))
        or (s.startswith("[") and s.endswith("]"))
    ):
        return value

    # Safely parse Python literal (handles single quotes etc.). Avoid eval().
    try:
        return ast.literal_eval(s)
    except Exception:
        return value


def write_records(df: pd.DataFrame, path: Path) -> None:
    """Persist bibliographic records via bibliography-io based on the suffix."""
    bibliography_io = _bibliography_io()
    output_path = _ensure_output_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    is_bibtex = output_path.suffix.lower() == ".bib"
    try:
        records: dict[str, dict[str, typing.Any]] = {}
        mapping_fields = {"colrev_masterdata_provenance", "colrev_data_provenance"}
        for record in df.to_dict(orient="records"):
            raw_id = record.get("ID")
            if raw_id is None or (not isinstance(raw_id, str) and pd.isnull(raw_id)):
                raise CLIError("Every output record must have a non-empty ID.")
            rec_id = str(raw_id).strip()
            if not rec_id:
                raise CLIError("Every output record must have a non-empty ID.")
            if rec_id in records:
                raise CLIError(f"Duplicate output record ID: {rec_id}")

            clean_record: dict[str, typing.Any] = {}
            for key, value in record.items():
                if key == "ID":
                    clean_record[key] = rec_id
                    continue
                if key == "colrev_origin":
                    origins = parse_colrev_origin(value)
                    clean_record[key] = origins if is_bibtex else ";".join(origins)
                    continue
                if is_bibtex and key in mapping_fields:
                    value = maybe_cast_literal(value)
                elif not is_bibtex and isinstance(value, (list, dict)):
                    value = str(value)
                if value is None or (isinstance(value, str) and value in {"", "nan"}):
                    continue
                if not isinstance(value, (list, dict)) and pd.isnull(value):
                    continue
                clean_record[key] = value
            records[rec_id] = clean_record

        bibliography_io.write(
            records,
            path=output_path,
            list_fields={"colrev_origin"} if is_bibtex else (),
            mapping_fields=mapping_fields if is_bibtex else (),
        )
    except CLIError:
        raise
    except Exception as exc:
        raise CLIError(
            f"Failed to write bibliographic records to {output_path}: {exc}"
        ) from exc


def write_df(df: pd.DataFrame, path: Path) -> None:
    """Persist *df* to *path*, inferring the format from the file suffix."""

    output_path = _ensure_output_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = output_path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(output_path, index=False)
        return
    if suffix in {".parquet", ".pq"}:
        try:
            df.to_parquet(output_path, index=False)
        except Exception as exc:  # pragma: no cover - backend availability specific
            raise CLIError(
                f"Failed to write parquet file {output_path}: {exc}"
            ) from exc
        return
    if suffix == ".json":
        df.to_json(output_path, orient="records", indent=2)
        return

    raise CLIError(
        "Unsupported file extension for output. Supported extensions: .csv, .parquet, .json"
    )


# ----------------------------- options helpers ------------------------------ #
def _resolve_verbosity(args: argparse.Namespace) -> int | None:
    verbosity_level = getattr(args, "verbosity_level", None)
    quiet = getattr(args, "quiet", False)
    verbose = getattr(args, "verbose", False)

    if quiet and verbose:
        raise CLIError("--quiet and --verbose cannot be used together.")

    if quiet:
        if verbosity_level is not None:
            raise CLIError("--quiet cannot be combined with --verbosity-level.")
        return 0
    if verbose:
        if verbosity_level is not None:
            raise CLIError("--verbose cannot be combined with --verbosity-level.")
        return 2
    return verbosity_level


def _collect_runtime_options(args: argparse.Namespace) -> RuntimeOptions:
    cpu = getattr(args, "cpu", -1)
    verbosity_level = _resolve_verbosity(args)
    return RuntimeOptions(cpu=cpu, verbosity_level=verbosity_level)


def _describe_maybe_cases() -> str:
    path = Path(maybe_cases.MAYBE_CASES_FILEPATH)
    if path.exists():
        return f"Maybe cases exported to: {path.resolve()}"
    return "No maybe cases were exported."


# ----------------------------- commands ------------------------------------- #
def run_merge(args: argparse.Namespace) -> int:
    options = _collect_runtime_options(args)
    records_df = _read_command_records(Path(args.input), args)
    n_input = len(records_df)

    matched_df: pd.DataFrame | None = None
    duplicate_id_sets: list | None = None
    pairs_df: pd.DataFrame | None = None

    if args.export_maybe:
        prep_df = prep(
            records_df, verbosity_level=options.verbosity_level, cpu=options.cpu
        )
        pairs_df = block(
            prep_df, verbosity_level=options.verbosity_level, cpu=options.cpu
        )
        matched_df = match(
            pairs_df, verbosity_level=options.verbosity_level, cpu=options.cpu
        )
        export_maybe(
            records_df,
            matched_df=matched_df,
            verbosity_level=options.verbosity_level,
        )
        print(_describe_maybe_cases())
        print(
            "Review the exported maybe cases and rerun with --import-maybe to apply decisions."
        )
        return 0

    if args.import_maybe:
        prep_df = prep(
            records_df, verbosity_level=options.verbosity_level, cpu=options.cpu
        )
        pairs_df = block(
            prep_df, verbosity_level=options.verbosity_level, cpu=options.cpu
        )
        matched_df = match(
            pairs_df, verbosity_level=options.verbosity_level, cpu=options.cpu
        )
        matched_df = import_maybe(matched_df, verbosity_level=options.verbosity_level)
        duplicate_id_sets = _cluster.get_connected_components(matched_df)
        merged_df = merge(
            records_df,
            duplicate_id_sets=duplicate_id_sets,
            verbosity_level=options.verbosity_level,
            origin_column="colrev_origin",
        )
    else:
        merged_df = merge(
            records_df,
            verbosity_level=options.verbosity_level,
            origin_column="colrev_origin",
        )

    write_records(merged_df, Path(args.output))

    if args.stats:
        stats_lines = [
            f"Input records: {n_input}",
            f"Merged records: {len(merged_df)}",
        ]
        if pairs_df is not None:
            stats_lines.append(f"Blocked pairs: {len(pairs_df)}")
        if matched_df is not None and "duplicate_label" in matched_df.columns:
            label_counts = matched_df["duplicate_label"].value_counts()
            n_true = int(label_counts.get("duplicate", 0))
            n_maybe = int(label_counts.get("maybe", 0))
            stats_lines.append(f"Confirmed matches: {n_true}")
            stats_lines.append(f"Maybe matches: {n_maybe}")
        print(" | ".join(stats_lines))

    return 0


def run_prep(args: argparse.Namespace) -> int:
    options = _collect_runtime_options(args)
    # prep produces an internal artifact used by block; keep non-colrev IO here
    records_df = read_df(Path(args.input))
    prepared_df = prep(
        records_df, verbosity_level=options.verbosity_level, cpu=options.cpu
    )
    write_df(prepared_df, Path(args.output))
    return 0


def run_block(args: argparse.Namespace) -> int:
    options = _collect_runtime_options(args)
    records_df = read_df(Path(args.input))
    pairs_df = block(
        records_df, verbosity_level=options.verbosity_level, cpu=options.cpu
    )
    write_df(pairs_df, Path(args.output))
    return 0


def run_match(args: argparse.Namespace) -> int:
    if (args.id_field or args.generate_ids) and not args.export_maybe:
        raise CLIError(
            "--id-field and --generate-ids require --export-maybe and --records."
        )

    options = _collect_runtime_options(args)
    pairs_df = read_df(Path(args.input))
    matched_df = match(
        pairs_df, verbosity_level=options.verbosity_level, cpu=options.cpu
    )
    write_df(matched_df, Path(args.output))

    if args.export_maybe:
        if not args.records:
            raise CLIError(
                "--export-maybe requires --records to provide the original records."
            )
        records_df = _read_command_records(Path(args.records), args)
        export_maybe(
            records_df,
            matched_df=matched_df,
            verbosity_level=options.verbosity_level,
        )
        print(_describe_maybe_cases())

    return 0


def run_export_maybe(args: argparse.Namespace) -> int:
    options = _collect_runtime_options(args)
    records_df = _read_command_records(Path(args.records), args)
    matches_df = read_df(Path(args.matches))
    export_maybe(
        records_df,
        matched_df=matches_df,
        verbosity_level=options.verbosity_level,
    )
    print(_describe_maybe_cases())
    return 0


def run_import_maybe(args: argparse.Namespace) -> int:
    options = _collect_runtime_options(args)
    matches_df = read_df(Path(args.input))
    updated_matches = import_maybe(matches_df, verbosity_level=options.verbosity_level)

    if args.output:
        write_df(updated_matches, Path(args.output))
    else:
        updated_matches.to_csv(sys.stdout, index=False)
    return 0


def run_version(_: argparse.Namespace) -> int:
    try:
        dist_version = metadata.version("bib-dedupe")
    except metadata.PackageNotFoundError:
        dist_version = "unknown"
    print(dist_version)
    return 0


# ----------------------------- CLI wiring ----------------------------------- #
def _add_record_id_arguments(parser: argparse.ArgumentParser) -> None:
    """Add mutually exclusive options for choosing or generating record IDs."""
    id_group = parser.add_mutually_exclusive_group()
    id_group.add_argument(
        "--id-field",
        help="Use this normalized input field as the record ID.",
    )
    id_group.add_argument(
        "--generate-ids",
        action="store_true",
        help="Generate sequential IDs only if loaded records have no usable IDs.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bib-dedupe",
        description="Deduplicate bibliographic records from the command line.",
    )

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--verbosity-level", type=int, help="Override verbosity level."
    )
    common_parser.add_argument(
        "-q", "--quiet", action="store_true", help="Silence verbose output."
    )
    common_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity level."
    )

    cpu_parser = argparse.ArgumentParser(add_help=False)
    cpu_parser.add_argument(
        "--cpu",
        type=int,
        default=-1,
        help="Number of CPUs to use (default: -1 for auto).",
    )

    subparsers = parser.add_subparsers(dest="command")

    merge_parser = subparsers.add_parser(
        "merge",
        parents=[common_parser, cpu_parser],
        help="Run the full deduplication workflow and write merged records.",
    )
    _add_record_id_arguments(merge_parser)
    merge_parser.add_argument(
        "-i", "--input", required=True, help="Input records file path."
    )
    merge_parser.add_argument(
        "-o", "--output", required=True, help="Output file path for merged records."
    )
    merge_parser.add_argument(
        "--stats", action="store_true", help="Print a short statistics summary."
    )
    merge_parser.add_argument(
        "--export-maybe",
        action="store_true",
        help="Export potential duplicates for manual review and exit.",
    )
    merge_parser.add_argument(
        "--import-maybe",
        action="store_true",
        help="Re-import maybe decisions before merging.",
    )
    merge_parser.set_defaults(func=run_merge)

    prep_parser = subparsers.add_parser(
        "prep",
        parents=[common_parser, cpu_parser],
        help="Preprocess records before blocking.",
    )
    prep_parser.add_argument(
        "-i", "--input", required=True, help="Input records file path."
    )
    prep_parser.add_argument(
        "-o", "--output", required=True, help="Output file path for prepared records."
    )
    prep_parser.set_defaults(func=run_prep)

    block_parser = subparsers.add_parser(
        "block",
        parents=[common_parser, cpu_parser],
        help="Generate candidate record pairs for matching.",
    )
    block_parser.add_argument(
        "-i", "--input", required=True, help="Input preprocessed records file path."
    )
    block_parser.add_argument(
        "-o", "--output", required=True, help="Output file path for blocked pairs."
    )
    block_parser.set_defaults(func=run_block)

    match_parser = subparsers.add_parser(
        "match",
        parents=[common_parser, cpu_parser],
        help="Score candidate pairs and classify matches.",
    )
    _add_record_id_arguments(match_parser)
    match_parser.add_argument(
        "-i", "--input", required=True, help="Input candidate pairs file path."
    )
    match_parser.add_argument(
        "-o", "--output", required=True, help="Output file path for match decisions."
    )
    match_parser.add_argument(
        "--export-maybe",
        action="store_true",
        help="Export maybe cases immediately after matching.",
    )
    match_parser.add_argument(
        "--records",
        help="Records file path required when using --export-maybe.",
    )
    match_parser.set_defaults(func=run_match)

    export_maybe_parser = subparsers.add_parser(
        "export-maybe",
        parents=[common_parser],
        help="Export maybe cases for manual review.",
    )
    _add_record_id_arguments(export_maybe_parser)
    export_maybe_parser.add_argument(
        "--records", required=True, help="Path to the records file."
    )
    export_maybe_parser.add_argument(
        "--matches", required=True, help="Path to the matches file."
    )
    export_maybe_parser.set_defaults(func=run_export_maybe)

    import_maybe_parser = subparsers.add_parser(
        "import-maybe",
        parents=[common_parser],
        help="Apply manual maybe decisions to match results.",
    )
    import_maybe_parser.add_argument(
        "-i", "--input", required=True, help="Matches file containing maybe decisions."
    )
    import_maybe_parser.add_argument(
        "-o", "--output", help="Optional output path for updated matches."
    )
    import_maybe_parser.set_defaults(func=run_import_maybe)

    version_parser = subparsers.add_parser(
        "version", help="Print the installed bib-dedupe version."
    )
    version_parser.set_defaults(func=run_version)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except CLIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - safeguard for unexpected failures
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover - manual execution
    sys.exit(main())
