"""CLI behavior when the optional bibliography I/O extra is unavailable."""
from __future__ import annotations

import importlib.util
import os
import sys

import pytest

from bib_dedupe.cli import main


def test_no_cli_extra_environment_has_no_bibliography_io() -> None:
    if os.environ.get("BIB_DEDUPE_EXPECT_NO_BIBLIOGRAPHY_IO") == "1":
        assert importlib.util.find_spec("bibliography_io") is None


def test_version_does_not_require_bibliography_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "bibliography_io", None)
    assert main(["version"]) == 0


def test_bibliographic_commands_explain_missing_optional_dependency(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setitem(sys.modules, "bibliography_io", None)
    result = main(["merge", "-i", "records.csv", "-o", "merged.csv"])

    assert result == 2
    assert "bibliography-io" in capsys.readouterr().err
