import os
import pandas as pd
from pybtex.database import parse_file, Person
from bib_dedupe.bib_dedupe import block, match, merge, prep
from bib_dedupe.constants.fields import ABSTRACT, AUTHOR, BOOKTITLE, CHAPTER, DOI, EDITOR, ENTRYTYPE, ID, INSTITUTION, ISBN, JOURNAL, NUMBER, PAGES, PUBLISHER, TITLE, VOLUME, YEAR

# Data Paths
DATA_SOURCES = {
    "CROSSREF": "/Users/jiangmingxin/.colrev/curated_metadata/journal-of-management-information-systems/data/search/CROSSREF.bib",
    "DBLP": "/Users/jiangmingxin/.colrev/curated_metadata/journal-of-management-information-systems/data/search/DBLP.bib",
    "PDFs": "/Users/jiangmingxin/.colrev/curated_metadata/journal-of-management-information-systems/data/search/pdfs.bib",
}

# Fields to Keep
FIELDS_TO_KEEP = ["ID", "author", "title", "year", "journal", "volume", "number", "pages", "url", "doi"]

# Output Directory
OUTPUT_DIR = "/Users/jiangmingxin/Desktop/bib-dedupe/output/"

def format_author(persons):
    """
    Convert Pybtex Person object to author string
    """
    if not persons:
        return ""
    
    authors = []
    for person in persons:
        if isinstance(person, str):
            authors.append(person)
        elif isinstance(person, Person):
            parts = []
            if person.first_names:
                parts.extend(person.first_names)
            if person.middle_names:
                parts.extend(person.middle_names)
            if person.last_names:
                parts.extend(person.last_names)
            authors.append(" ".join(parts))
    
    return " and ".join(authors)

def convert_bib_to_csv(bib_file_path, csv_file_path, fields_to_keep):
    """
    Convert .bib file to .csv file, fill missing fields with empty values.
    """
    try:
        if not os.path.exists(bib_file_path):
            print(f"Error: .bib file does not exist at {bib_file_path}")
            return

        print(f"Converting {bib_file_path} to {csv_file_path}")

        bib_data = parse_file(bib_file_path)
        print(f"Parsed {len(bib_data.entries)} entries from {bib_file_path}")

        rows = []
        for entry_key, entry in bib_data.entries.items():
            row = {"ID": entry_key}

            if "author" in fields_to_keep:
                row["author"] = format_author(entry.persons.get("author", []))
            
            for field in fields_to_keep:
                if field != "author" and field != "ID":
                    row[field] = entry.fields.get(field, "")
            
            rows.append(row)

        if not rows:
            print(f"No entries found in .bib file: {bib_file_path}")
            return

        df = pd.DataFrame(rows)
        
        for field in fields_to_keep:
            if field not in df.columns:
                df[field] = ""

        df = df[fields_to_keep]

        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        df.to_csv(csv_file_path, index=False)
        print(f"CSV file created: {csv_file_path}")

    except Exception as e:
        print(f"Error during conversion: {e}")

def dedupe_records(csv_file_path):
    """
    Apply dedupe to the records from CSV using the provided dedupe functions.
    """
    try:
        df = pd.read_csv(csv_file_path)
        if df.empty:
            print(f"No records found in {csv_file_path} to deduplicate.")
            return pd.DataFrame()

        prepped_data = prep(df)
        blocked_data = block(prepped_data)

        if blocked_data.empty:
            print(f"No blocks found for deduplication in {csv_file_path}.")
            return pd.DataFrame()

        matched_data = match(blocked_data)

        if matched_data is None or matched_data.empty:
            print(f"No matches found for deduplication in {csv_file_path}.")
            return pd.DataFrame()
        
        # Debugging output to check the matched data
        print(f"Matched data preview for {csv_file_path}:\n{matched_data.head()}\n")

        # Process 'maybe' labels to ensure correctness for merging
        matched_data.loc[matched_data['duplicate_label'] == 'maybe', 'duplicate_label'] = 'duplicate'

        # More robust check for matched_data
        if matched_data is None or matched_data.empty:
            print(f"Matched data is empty or None for {csv_file_path}.")
            return pd.DataFrame()

        merged_data = merge(prepped_data, matched_df=matched_data)
        return merged_data

    except Exception as e:
        print(f"Error during deduplication: {e}")
        return pd.DataFrame()

def main():
    for source_name, bib_file_path in DATA_SOURCES.items():
        csv_file_path = os.path.join(os.path.dirname(bib_file_path), f"{source_name}.csv")
        if not os.path.exists(csv_file_path):
            convert_bib_to_csv(bib_file_path, csv_file_path, FIELDS_TO_KEEP)
        else:
            print(f"{csv_file_path} already exists, skipping conversion.")
    print("Data conversion completed. Proceeding to deduplication...\n")

    for source_name, bib_file_path in DATA_SOURCES.items():
        csv_file_path = bib_file_path.replace(".bib", ".csv")
        merged_data = dedupe_records(csv_file_path)
        if not merged_data.empty:
            output_csv_path = os.path.join(OUTPUT_DIR, f"{source_name}_deduped.csv")
            merged_data.to_csv(output_csv_path, index=False)
            print(f"Deduplicated data saved to {output_csv_path}")
        else:
            print(f"No deduplicated data for {source_name}")

if __name__ == "__main__":
    main()
