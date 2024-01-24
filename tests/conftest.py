#!/usr/bin/env python
"""Conftest file containing fixtures to set up tests efficiently"""
from __future__ import annotations

from pathlib import Path

import pytest


# pylint: disable=too-few-public-methods
class Helpers:
    """Helpers class providing utility functions (e.g., for test-file retrieval)"""

    test_data_path = Path(__file__).parent / Path("data")


@pytest.fixture(scope="session", name="helpers")
def get_helpers():  # type: ignore
    """Fixture returning Helpers"""
    return Helpers
