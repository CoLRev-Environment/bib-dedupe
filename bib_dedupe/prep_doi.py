#! /usr/bin/env python
"""Preparation of doi field"""
import re
import urllib.parse

import numpy as np


def prep_doi(doi_array: np.array) -> np.array:
    doi_array = np.array(
        [re.sub(r"http://dx.doi.org/", "", doi.lower()) for doi in doi_array]
    )
    doi_array = np.array([re.sub(r"-", "_", doi) for doi in doi_array])
    doi_array = np.array([re.sub(r"\[doi\]", "", doi) for doi in doi_array])
    doi_array = np.array([re.sub(r"[\r\n]+", " ; ", doi) for doi in doi_array])

    doi_array = np.array(
        [
            doi.split(";")[1].lstrip()
            if ";" in doi and doi.split(";")[1].lstrip().startswith("10.")
            else doi.split(";")[0].lstrip()
            if ";" in doi and doi.split(";")[0].lstrip().startswith("10.")
            else doi
            for doi in doi_array
        ]
    )
    doi_array = np.array(
        [doi.split("[pii];")[1] if "[pii];" in doi else doi for doi in doi_array]
    )
    doi_array = np.array([urllib.parse.unquote(doi) for doi in doi_array])
    doi_array = np.array([doi if doi.startswith("10.") else "" for doi in doi_array])

    return np.array(
        ["" if doi == "nan" else doi.replace(".", "").rstrip() for doi in doi_array]
    )
