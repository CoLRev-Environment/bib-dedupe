#! /usr/bin/env python
"""Preparation of abstract field"""
import re

import numpy as np


def prep_abstract(abstract_array: np.array) -> np.array:
    abstract_array = np.array(
        [re.sub(r"<.*?>", " ", abstract.lower()) for abstract in abstract_array]
    )

    abstract_array = np.array(
        [
            re.sub(r"^aims\s|^objectives|^background", "", abstract)
            for abstract in abstract_array
        ]
    )

    abstract_array = np.array(
        [
            abstract[: abstract.rfind(". copyright")]
            if ". copyright" in abstract[-300:]
            else abstract[: abstract.rfind("©")]
            if "©" in abstract[-200:]
            else re.sub(r"(\s*\d{4}\s*)?the authors[.?]$", "", abstract)
            if "the authors" in abstract[-100:]
            else abstract[: abstract.rfind("springer-verlag")]
            if "springer-verlag" in abstract[-100:]
            else re.sub(r"\s*\d{4}.*$", "", abstract)
            if re.search(r"\.\s*\d{4}.*$", abstract)
            else re.sub(r" \(c\) \d{4}.*\.$", "", abstract)
            if re.search(r"\. \(c\) \d{4}.*\.$", abstract)
            else re.sub(r"\.\(abstract truncated at 400 words\)$", "", abstract)
            if ".(abstract truncated at 400 words)" in abstract[-80:]
            else abstract
            for abstract in abstract_array
        ]
    )

    # Remove "abstract " at the beginning
    abstract_array = np.array(
        [re.sub(r"^abstract ", "", abstract) for abstract in abstract_array]
    )

    # Remove trailing date
    abstract_array = np.array(
        [re.sub(r"\s*\(\d{4}\)$", "", abstract) for abstract in abstract_array]
    )

    abstract_array = np.array(
        [re.sub(r"[^A-Za-z0-9 .,]", "", abstract) for abstract in abstract_array]
    )
    abstract_array = np.array(
        [re.sub(r"\s+", " ", abstract) for abstract in abstract_array]
    )
    return np.array(
        [
            "" if abstract == "nan" else abstract.lower().rstrip(" .").lstrip(" .")
            for abstract in abstract_array
        ]
    )
