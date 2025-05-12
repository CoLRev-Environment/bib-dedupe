import os
import pandas as pd
from bib_dedupe.bib_dedupe import prep, block, match, cluster, merge

PDF_CSV_PATH = "/Users/jiangmingxin/.colrev/curated_metadata/journal-of-management-information-systems/data/search/pdfs.csv"
SAMPLE_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_200_nodup_input.csv"
DEDUPED_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_200_nodup_deduped.csv"

def run():
    os.makedirs(os.path.dirname(SAMPLE_CSV_PATH), exist_ok=True)

    pdf_df = pd.read_csv(PDF_CSV_PATH)
    if pdf_df.empty:
        print("Error: PDF dataset is empty.")
        return

    print(f"Original PDF dataset size: {pdf_df.shape[0]} records")

    sample_df = pdf_df.head(200).copy()
    sample_df["ID"] = range(1, len(sample_df) + 1)

    sample_df.to_csv(SAMPLE_CSV_PATH, index=False)
    print(f"Saved sample of 200 PDF records to: {SAMPLE_CSV_PATH}")

    print("Starting deduplication...")
    df = pd.read_csv(SAMPLE_CSV_PATH)

    print(f"Dataset size before deduplication: {df.shape[0]} records")

    df = prep(df)
    blocked_df = block(df)
    matched_df = match(blocked_df)
    duplicate_id_sets = cluster(matched_df)
    # Save duplicate clusters to file
    with open("/Users/jiangmingxin/Desktop/bib-dedupe-1/output/duplicate_clusters.txt", "w") as f:
        f.write(str(duplicate_id_sets))

    deduped_df = merge(df, duplicate_id_sets=duplicate_id_sets)

    deduped_df.to_csv(DEDUPED_CSV_PATH, index=False)
    print(f"Deduplicated dataset saved to: {DEDUPED_CSV_PATH}")
    print(f"Dataset size after deduplication: {deduped_df.shape[0]} records")

if __name__ == "__main__":
    run()
