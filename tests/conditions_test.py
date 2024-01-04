import pandas as pd
import pytest

import bib_dedupe.conditions
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import CONTAINER_TITLE
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import ENTRYTYPE
from bib_dedupe.constants.fields import ISBN
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR


def test_conditions() -> None:
    df = pd.DataFrame(
        columns=[
            AUTHOR,
            TITLE,
            VOLUME,
            PAGES,
            ABSTRACT,
            ISBN,
            CONTAINER_TITLE,
            NUMBER,
            DOI,
            YEAR,
            ENTRYTYPE,
            "page_ranges_adjacent",
            "container_title_1",
            "container_title_2",
            "doi_1",
            "doi_2",
            "volume_1",
            "volume_2",
            "title_1",
            "title_2",
            "ENTRYTYPE_1",
            "ENTRYTYPE_2",
            "number_1",
            "number_2",
            "pages_1",
            "pages_2",
            "author_1",
            "author_2",
            "abstract_1",
            "abstract_2",
            "year_1",
            "year_2",
        ]
    )

    for condition in (
        bib_dedupe.conditions.non_duplicate_conditions
        + bib_dedupe.conditions.duplicate_conditions
    ):
        try:
            print(condition)
            df.query(condition)
        except Exception as e:
            pytest.fail(f"Condition '{condition}' could not be parsed. Error: {str(e)}")
