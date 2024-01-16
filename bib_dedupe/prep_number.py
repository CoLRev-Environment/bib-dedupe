#! /usr/bin/env python
"""Preparation of number field"""
import re

import numpy as np


def prep_number(number_array: np.array) -> np.array:
    number_array = np.array(
        [re.sub(r"[A-Za-z.]*", "", number) for number in number_array]
    )
    number_array = np.array(
        [
            # pages included: "6 51-6"
            re.search(r"(\d+) .*", number).group(1)  # type: ignore
            if re.search(r"(\d+) \d+-\d+", number) is not None
            else number
            for number in number_array
        ]
    )

    number_array = np.array(
        [
            number.replace(" ", "").replace("(", "").replace(")", "")
            for number in number_array
        ]
    )

    return np.array(
        ["" if number in ["nan", "var.pagings"] else number for number in number_array]
    )
