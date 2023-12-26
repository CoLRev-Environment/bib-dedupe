#!/usr/bin/env python
"""Constants for bib-dedupe"""
# pylint: disable=too-few-public-methods


class ENTRYTYPES:
    """Constants for record ENTRYTYPEs"""

    ARTICLE = "article"
    INPROCEEDINGS = "inproceedings"
    BOOK = "book"
    INBOOK = "inbook"
    PROCEEDINGS = "proceedings"

    INCOLLECTION = "incollection"
    PHDTHESIS = "phdthesis"
    THESIS = "thesis"
    MASTERSTHESIS = "masterthesis"
    BACHELORTHESIS = "bachelorthesis"
    TECHREPORT = "techreport"
    UNPUBLISHED = "unpublished"
    MISC = "misc"
    SOFTWARE = "software"
    ONLINE = "online"
    CONFERENCE = "conference"


class Fields:
    """Constant field names"""

    ID = "ID"
    ENTRYTYPE = "ENTRYTYPE"
    DOI = "doi"
    URL = "url"
    # TBD: no LINK field?
    ISSN = "issn"
    ISBN = "isbn"
    FULLTEXT = "fulltext"
    ABSTRACT = "abstract"
    KEYWORDS = "keywords"
    CITED_BY = "cited_by"
    FILE = "file"
    INSTITUTION = "institution"
    MONTH = "month"
    SERIES = "series"
    SCHOOL = "school"
    LANGUAGE = "language"

    ORIGIN = "colrev_origin"
    STATUS = "colrev_status"

    TITLE = "title"
    AUTHOR = "author"
    YEAR = "year"
    JOURNAL = "journal"
    BOOKTITLE = "booktitle"
    CHAPTER = "chapter"
    PUBLISHER = "publisher"
    VOLUME = "volume"
    NUMBER = "number"
    PAGES = "pages"
    EDITOR = "editor"
    EDITION = "edition"
    ADDRESS = "address"

    CONTAINER_TITLE = "container_title"

    # For blocking
    AUTHOR_FIRST = "author_first"
    TITLE_SHORT = "title_short"
    CONTAINER_TITLE_SHORT = "container_title_short"

    # For similarity
    PAGE_RANGES_ADJACENT = "page_ranges_adjacent"


class FieldSet:
    """Constant field sets"""

    IDENTIFYING_FIELD_KEYS = [
        Fields.TITLE,
        Fields.AUTHOR,
        Fields.YEAR,
        Fields.JOURNAL,
        Fields.BOOKTITLE,
        Fields.CHAPTER,
        Fields.PUBLISHER,
        Fields.VOLUME,
        Fields.NUMBER,
        Fields.PAGES,
        Fields.EDITOR,
        Fields.INSTITUTION,
    ]


class ExitCodes:
    """Exit codes"""

    SUCCESS = 0
    FAIL = 1


class Colors:
    """Colors for CLI printing"""

    RED = "\033[91m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"
