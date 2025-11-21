#! /usr/bin/env python
"""Exceptions"""
from __future__ import annotations


class BibDedupeException(Exception):
    """
    Base class for all exceptions raised by this package
    """


class MissingRequiredFieldsError(BibDedupeException):
    """
    Raised when a bibliographic record is missing required fields
    (e.g., 'author', 'title', 'year').
    """

    def __init__(self, missing_fields: list[str]) -> None:
        fields = ", ".join(missing_fields)
        self.message = (
            f"Missing required fields: [{fields}].\n"
            "Please ensure all mandatory metadata fields are present."
        )
        super().__init__(self.message)
