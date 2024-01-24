#! /usr/bin/env python
"""BibDedupe utility"""
from __future__ import annotations

import pprint


class VerbosePrint:
    """A class to handle verbose printing with different verbosity levels."""

    def __init__(self, verbosity_level: int):
        """Initialize the VerbosePrint class with a specific verbosity level."""
        self.verbosity_level = verbosity_level
        self.p_printer = pprint.PrettyPrinter(indent=4, width=140, compact=False)

    def print(self, message: str = "", *, level: int = 1) -> None:
        """Print a message if the specified level is less than or equal to the current verbosity level."""
        if level <= self.verbosity_level:
            print(message)

    def pretty_print(self, input_dict: dict) -> None:
        """Pretty print a dictionary."""
        self.p_printer.pprint(input_dict)
