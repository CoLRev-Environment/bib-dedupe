#! /usr/bin/env python
"""Preparation of pages field"""
import re

import numpy as np

month_dict = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def prep_pages(pages_array: np.array) -> np.array:
    def process_page(value: str) -> str:
        if value.isalpha():
            return ""

        # Fix Excel errors (e.g., "08-11" is converted to "08-Nov")
        for month, num in month_dict.items():
            if month in value.lower():
                value = value.lower().replace(month, num)
                break

        def roman_to_int(s: str) -> int:
            rom_val = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
            int_val = 0
            for i in range(len(s)):
                if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
                    int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
                else:
                    int_val += rom_val[s[i]]
            return int_val

        # Check if the value is a roman numeral range
        roman_numeral_range = re.match(r"([IVXLCDM]+)-([IVXLCDM]+)", value, re.I)
        if roman_numeral_range:
            # Convert the roman numerals to integers
            from_page = roman_to_int(roman_numeral_range.group(1).upper())
            to_page = roman_to_int(roman_numeral_range.group(2).upper())
            return f"{from_page}-{to_page}"

        # Remove leading zeros in groups of digits
        value = re.sub(r"\b0+([0-9]+)", r"\1", value)

        value = re.sub(r"[A-Za-z. ]*", "", value)
        if re.match(r"^\d+\s*-?-\s*\d+$", value):
            from_page_str, to_page_str = re.findall(r"(\d+)", value)
            if from_page_str == to_page_str:
                return from_page_str
            if len(from_page_str) > len(to_page_str):
                return (
                    f"{from_page_str}-{from_page_str[:-len(to_page_str)]}{to_page_str}"
                )
            else:
                return f"{from_page_str}-{to_page_str}"
        if value in [
            " ",
            None,
            "nan",
            "na",
            "no pages",
            "no pagination",
            "var.pagings",
        ]:
            return ""
        # re sub everything except numbers and dashes
        return re.sub(r"[^0-9-]", "", value).lstrip("-").rstrip("-")

    return np.vectorize(process_page)(pages_array)
