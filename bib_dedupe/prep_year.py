#! /usr/bin/env python
"""Preparation of year field"""
import numpy as np


def prep_year(year_array: np.array) -> np.array:
    def process_year(value: str) -> str:
        try:
            int_value = int(float(value))

            if not 1900 < int_value < 2100:
                return ""

        except ValueError:
            return ""
        return str(int_value)

    return np.array([process_year(year) for year in year_array])
