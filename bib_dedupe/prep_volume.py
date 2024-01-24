#! /usr/bin/env python
"""Preparation of volume field"""
import re

import numpy as np


def prep_volume(volume_array: np.array) -> np.array:
    volume_array = np.array(
        [
            re.search(r"(\d+) \(.*\)", volume).group(1)  # type: ignore
            if re.search(r"(\d+) \(.*\)", volume) is not None
            # pages included: "6 51-6"
            else re.search(r"(\d+) .*", volume).group(1)  # type: ignore
            if re.search(r"(\d+) \d+-\d+", volume) is not None
            else volume
            for volume in volume_array
        ]
    )
    volume_array = np.array(
        [
            re.search(r"(\d+) suppl \d+", volume.lower()).group(1)  # type: ignore
            if re.search(r"(\d+) suppl \d+", volume.lower()) is not None
            else volume
            for volume in volume_array
        ]
    )
    volume_array = np.array(
        [re.sub(r"[^\d\(\)]", "", volume) for volume in volume_array]
    )

    volume_array = np.array(
        [
            re.search(r"(\d+)", volume).group(0)  # type: ignore
            if re.search(r"(\d+)", volume) is not None
            else volume.replace("(", "").replace(")", "")
            for volume in volume_array
        ]
    )
    return np.array(
        [
            "" if volume == "nan" or len(volume) > 100 else volume
            for volume in volume_array
        ]
    )
