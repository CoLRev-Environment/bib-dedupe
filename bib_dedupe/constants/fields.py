#!/usr/bin/env python
"""Field constants for bib-dedupe"""
# pylint: disable=too-few-public-methods


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

ORIGIN = "origin"
SEARCH_SET = "search_set"

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

DUPLICATE_LABEL = "duplicate_label"
CLUSTER_ID = "cluster_ID"

DUPLICATE = "duplicate"
MAYBE = "maybe"
