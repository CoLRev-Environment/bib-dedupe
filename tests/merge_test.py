import pandas as pd

from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import ID
from bib_dedupe.constants.fields import JOURNAL
from bib_dedupe.constants.fields import ORIGIN
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import YEAR
from bib_dedupe.merge import merge


def test_merge():
    records_df = pd.DataFrame(
        {
            ID: ["001", "002"],
            ORIGIN: ["source1", "source2"],
            TITLE: ["title1", "title2"],
            AUTHOR: ["AUTHOR", "author2"],
            YEAR: ["2000", "2001"],
            JOURNAL: ["journal1", "journal2"],
            PAGES: ["1", "11--20"],
        }
    )
    duplicate_id_sets = [["001", "002"]]

    merged_df = merge(
        records_df, duplicate_id_sets=duplicate_id_sets, verbosity_level=2
    )
    assert len(merged_df) == 1
    assert merged_df[ORIGIN].iloc[0] == "source1;source2"
    assert merged_df[TITLE].iloc[0] == "title1"
    assert merged_df[AUTHOR].iloc[0] == "author2"
    assert merged_df[YEAR].iloc[0] == "2001"
    assert merged_df[JOURNAL].iloc[0] == "journal1"
    assert merged_df[PAGES].iloc[0] == "11--20"
