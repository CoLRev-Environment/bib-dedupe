#! /usr/bin/env python
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

import bib_dedupe.cluster
from bib_dedupe.constants.fields import ABSTRACT
from bib_dedupe.constants.fields import ARTICLE
from bib_dedupe.constants.fields import AUTHOR
from bib_dedupe.constants.fields import BOOKTITLE
from bib_dedupe.constants.fields import DOI
from bib_dedupe.constants.fields import DUPLICATE
from bib_dedupe.constants.fields import DUPLICATE_LABEL
from bib_dedupe.constants.fields import ENTRYTYPE
from bib_dedupe.constants.fields import ID
from bib_dedupe.constants.fields import INPROCEEDINGS
from bib_dedupe.constants.fields import JOURNAL
from bib_dedupe.constants.fields import NUMBER
from bib_dedupe.constants.fields import PAGES
from bib_dedupe.constants.fields import TITLE
from bib_dedupe.constants.fields import URL
from bib_dedupe.constants.fields import VOLUME
from bib_dedupe.constants.fields import YEAR

COLREV_ORIGIN = "colrev_origin"
ISBN = "isbn"
DUPLICATE_FLAG = "duplicate_flag"


def parse_xml_osf(dirname, xml_file, *, n: int, dupes: int):
    from pathlib import Path

    print("Dataset: ", xml_file)

    Path(dirname).mkdir(parents=True, exist_ok=True)

    tree = ET.parse(Path(dirname) / xml_file)
    root = tree.getroot()

    xml_records = root.findall(".//record")

    records = []
    id_counter = 1
    for record in xml_records:
        titles = record.findall(".//titles/title/style")
        title = titles[0].text if titles else ""

        authors = record.findall(".//contributors/authors/author/style")
        author_names = [author.text for author in authors]

        pages = record.find(".//pages/style")
        if pages is not None:
            pages = pages.text
        else:
            pages = ""
        volume = record.find(".//volume/style")
        if volume is not None:
            volume = volume.text
        else:
            volume = ""
        number = record.find(".//number/style")
        if number is not None:
            number = number.text
        else:
            number = ""
        secondary_title = record.find(".//secondary-title/style")
        if secondary_title is not None:
            secondary_title = secondary_title.text
        else:
            secondary_title = ""

        captions = record.findall(".//caption")
        duplicate_flag = False
        for caption in captions:
            if (
                caption.find(".//style") is not None
                and caption.find(".//style").text == "Duplicate"
            ):
                duplicate_flag = True
                break

        xml_dict = {
            ID: str(id_counter).zfill(10),
            TITLE: title,
            YEAR: record.find(".//dates/year/style").text
            if record.find(".//dates/year/style") is not None
            else "",
            AUTHOR: " and ".join(author_names),
            PAGES: pages,
            VOLUME: volume,
            NUMBER: number,
            DUPLICATE_FLAG: duplicate_flag,
        }

        if "conference" in secondary_title:
            xml_dict[ENTRYTYPE] = INPROCEEDINGS
            xml_dict[BOOKTITLE] = secondary_title
        else:
            xml_dict[ENTRYTYPE] = ARTICLE
            xml_dict[JOURNAL] = secondary_title

        records.append(xml_dict)
        id_counter += 1

    df = pd.DataFrame(records)

    if n != df.shape[0]:
        print(f"mismatch: imported {df.shape[0]} records instead of n={n}")

    if df.empty:
        return

    df[COLREV_ORIGIN] = "source_1.bib/" + df[ID]
    df[COLREV_ORIGIN] = df[COLREV_ORIGIN].apply(lambda x: [x])

    def similarity_function(row1, row2):
        title_similarity = fuzz.token_set_ratio(row1[TITLE], row2[TITLE])
        author_similarity = fuzz.token_set_ratio(row1[AUTHOR], row2[AUTHOR])
        year_similarity = fuzz.ratio(row1[YEAR], row2[YEAR])
        return (title_similarity + author_similarity + year_similarity) / 3

    # Reconstruct the merged-origins
    origin_pairs = []
    duplicate_rows = df[df[DUPLICATE_FLAG]]
    for index, row in duplicate_rows.iterrows():
        similarity_scores = df[df[ID] != row[ID]].apply(
            lambda r: similarity_function(row, r), axis=1
        )
        most_similar_index = similarity_scores.idxmax()
        most_similar_row = df.loc[most_similar_index]
        origin_pairs.append([row[COLREV_ORIGIN][0], most_similar_row[COLREV_ORIGIN][0]])

    origin_pairs_df = pd.DataFrame(origin_pairs, columns=[f"{ID}_1", f"{ID}_2"])
    origin_pairs_df[DUPLICATE_LABEL] = DUPLICATE

    origin_pairs = bib_dedupe.cluster.connected_components(origin_pairs_df)

    origin_pairs_df = pd.DataFrame({"merged_origins": origin_pairs})
    origin_pairs_df.to_csv(Path(dirname) / "merged_record_origins.csv", index=False)

    if dupes != df[DUPLICATE_FLAG].sum():
        print(
            "mismatch in number of duplicates: ",
            df[DUPLICATE_FLAG].sum(),
            " instead of ",
            dupes,
        )
    df = df.drop(columns=[DUPLICATE_FLAG])

    df[ID] = df[ID].astype(str)
    df.to_csv(Path(dirname) / "records_pre_merged.csv", index=False)


def parse_csv(data_dir, csv_path):
    print(data_dir)
    DUPLICATE_COLREV_ORIGIN = "duplicate_colrev_origin"
    MREGED_COLREV_ORIGIN = "merged_colrev_origin"
    RECORD_ID = "RecordID"
    DUPLICATE_ID = "DuplicateID"

    df = pd.read_csv(Path(data_dir) / csv_path, encoding="latin1")

    df[ID] = df[RECORD_ID].apply(lambda id_counter: str(id_counter).zfill(10))
    df[DUPLICATE_ID] = df[DUPLICATE_ID].apply(
        lambda id_counter: str(id_counter).zfill(10)
    )
    df[COLREV_ORIGIN] = "source_1.bib/" + df[ID]
    df[COLREV_ORIGIN] = df[COLREV_ORIGIN].apply(lambda x: [x])

    df[DUPLICATE_COLREV_ORIGIN] = "source_1.bib/" + df[DUPLICATE_ID].astype(str)
    df[DUPLICATE_COLREV_ORIGIN] = df[DUPLICATE_COLREV_ORIGIN].apply(lambda x: [x])

    selected_columns = df[[DUPLICATE_COLREV_ORIGIN, COLREV_ORIGIN]]
    selected_columns = selected_columns[
        selected_columns[DUPLICATE_COLREV_ORIGIN] != selected_columns[COLREV_ORIGIN]
    ]
    df[MREGED_COLREV_ORIGIN] = df[COLREV_ORIGIN] + df[DUPLICATE_COLREV_ORIGIN]
    origin_pairs = df[MREGED_COLREV_ORIGIN].values.tolist()

    origin_pairs_df = pd.DataFrame(origin_pairs, columns=[f"{ID}_1", f"{ID}_2"])
    origin_pairs_df[DUPLICATE_LABEL] = DUPLICATE

    origin_pairs = bib_dedupe.cluster.connected_components(origin_pairs_df)
    origin_pairs = [pair for pair in origin_pairs if len(pair) > 1]

    origin_pairs_df = pd.DataFrame({"merged_origins": origin_pairs})
    origin_pairs_df.to_csv(Path(data_dir) / "merged_record_origins.csv", index=False)

    columns_to_select = [
        "Author",
        "Year",
        "Journal",
        "DOI",
        "Title",
        "Pages",
        "Volume",
        "Number",
        "Abstract",
        "ISBN",
        "Url",
        ID,
        COLREV_ORIGIN,
    ]
    df = df[[col for col in columns_to_select if col in df.columns]]
    df.columns = [col.lower() if col != ID else col for col in df.columns]
    df.loc[:, ENTRYTYPE] = ARTICLE
    df.loc[df[JOURNAL].str.contains("conf", na=False), ENTRYTYPE] = INPROCEEDINGS
    df.loc[:, ID] = df[ID].astype(str)
    columns_to_select = [
        ID,
        COLREV_ORIGIN,
        ENTRYTYPE,
        AUTHOR,
        YEAR,
        TITLE,
        JOURNAL,
        VOLUME,
        NUMBER,
        PAGES,
        ABSTRACT,
        DOI,
        ISBN,
        URL,
    ]
    df = df[[col for col in columns_to_select if col in df.columns]]

    df.to_csv(Path(data_dir) / "records_pre_merged.csv", index=False)


Path(__file__).resolve().parent.cwd()


# XML files available at OSF:
# https://osf.io/dyvnj/

# Note: the number in the docx description is incorrect
parse_xml_osf("cytology_screening", "Cytology screening.xml", n=1956, dupes=1404)
parse_xml_osf("haematology", "Haematology.xml", n=1415, dupes=246)
parse_xml_osf("stroke", "Stroke.xml", n=1292, dupes=507)
parse_xml_osf("respiratory", "Respiratory.xml", n=1988, dupes=799)


# csvs available at OSF:
# https://osf.io/c9evs/
# directory: final_data
parse_csv("cardiac", "final_labelled_Cardiac_duplicates_calc_performance.csv")
parse_csv("depression", "final_labelled_depression_duplicates_calc_performance.csv")
parse_csv("diabetes", "final_labelled_Diabetes_duplicates_calc_performance.csv")
parse_csv("neuroimaging", "final_labelled_Neuroimaging_duplicates_calc_performance.csv")
parse_csv("srsr", "final_labelled_SRSR_duplicates_calc_performance.csv")
