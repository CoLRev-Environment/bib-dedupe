#! /usr/bin/env python
"""Preparation of year field"""
import re

import numpy as np


def prep_year(year_array: np.array) -> np.array:
    def process_year(value: str) -> str:
        try:
            match = re.match(r"^(\d{4})-\d{2}-\d{2}$", value)
            if match:
                value = match.group(1)

            int_value = int(float(value))

            if not 1900 < int_value < 2100:
                return ""

        except ValueError:
            return ""
        return str(int_value)

    return np.array([process_year(year) for year in year_array])
