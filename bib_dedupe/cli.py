"""Command-line interface for :mod:`bib_dedupe`."""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Optional
from typing import Sequence

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
    verbosity_level: Optional[int]


DataFrame = pd.DataFrame


def read_df(path: Path) -> DataFrame:
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


def write_df(df: DataFrame, path: Path) -> None:
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


def _resolve_verbosity(args: argparse.Namespace) -> Optional[int]:
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


def run_merge(args: argparse.Namespace) -> int:
    options = _collect_runtime_options(args)
    records_df = read_df(Path(args.input))
    n_input = len(records_df)

    matched_df: Optional[DataFrame] = None
    duplicate_id_sets: Optional[list] = None
    pairs_df: Optional[DataFrame] = None

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
        )
    else:
        merged_df = merge(
            records_df,
            verbosity_level=options.verbosity_level,
        )

    write_df(merged_df, Path(args.output))

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
        records_df = read_df(Path(args.records))
        export_maybe(
            records_df,
            matched_df=matched_df,
            verbosity_level=options.verbosity_level,
        )
        print(_describe_maybe_cases())

    return 0


def run_export_maybe(args: argparse.Namespace) -> int:
    options = _collect_runtime_options(args)
    records_df = read_df(Path(args.records))
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


def main(argv: Optional[Sequence[str]] = None) -> int:
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
