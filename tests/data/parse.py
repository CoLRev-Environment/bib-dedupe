#! /usr/bin/env python
import xml.etree.ElementTree as ET

import colrev.ops.dedupe
import pandas as pd
from rapidfuzz import fuzz


def parse_xml(dirname, xml_file, *, n: int, dupes: int):
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
            "ID": str(id_counter).zfill(10),
            "title": title,
            "year": record.find(".//dates/year/style").text
            if record.find(".//dates/year/style") is not None
            else "",
            "author": " and ".join(author_names),
            "pages": pages,
            "volume": volume,
            "number": number,
            "duplicate_flag": duplicate_flag,
        }

        if "conference" in secondary_title:
            xml_dict["ENTRYTYPE"] = "inproceedings"
            xml_dict["booktitle"] = secondary_title
        else:
            xml_dict["ENTRYTYPE"] = "article"
            xml_dict["journal"] = secondary_title

        records.append(xml_dict)
        id_counter += 1

    df = pd.DataFrame(records)

    if n != df.shape[0]:
        print(f"mismatch: imported {df.shape[0]} records instead of n={n}")

    if df.empty:
        return

    df["colrev_origin"] = "source_1.bib/" + df["ID"]
    df["colrev_origin"] = df["colrev_origin"].apply(lambda x: [x])

    def similarity_function(row1, row2):
        title_similarity = fuzz.token_set_ratio(row1["title"], row2["title"])
        author_similarity = fuzz.token_set_ratio(row1["author"], row2["author"])
        year_similarity = fuzz.ratio(row1["year"], row2["year"])
        return (title_similarity + author_similarity + year_similarity) / 3

    # Reconstruct the merged-origins
    origin_pairs = []
    duplicate_rows = df[df["duplicate_flag"]]
    for index, row in duplicate_rows.iterrows():
        similarity_scores = df[df["ID"] != row["ID"]].apply(
            lambda r: similarity_function(row, r), axis=1
        )
        most_similar_index = similarity_scores.idxmax()
        most_similar_row = df.loc[most_similar_index]
        origin_pairs.append(
            [row["colrev_origin"][0], most_similar_row["colrev_origin"][0]]
        )

    origin_pairs = colrev.ops.dedupe.Dedupe.connected_components(origin_pairs)

    origin_pairs_df = pd.DataFrame({"merged_origins": origin_pairs})
    origin_pairs_df.to_csv(Path(dirname) / "merged_record_origins.csv", index=False)

    if dupes != df["duplicate_flag"].sum():
        print(
            "mismatch in number of duplicates: ",
            df["duplicate_flag"].sum(),
            " instead of ",
            dupes,
        )
    df = df.drop(columns=["duplicate_flag"])

    df["ID"] = df["ID"].astype(str)
    df.to_csv(Path(dirname) / "records_pre_merged.csv", index=False)


# XML files available at OSF:
# https://osf.io/dyvnj/

parse_xml(
    "cytology_screening", "Cytology screening.xml", n=1956, dupes=1404
)  # Note: the number in the docx description is incorrect
parse_xml("haematology", "Haematology.xml", n=1415, dupes=246)
parse_xml("stroke", "Stroke.xml", n=1292, dupes=507)
parse_xml("respiratory", "Respiratory.xml", n=1988, dupes=799)
