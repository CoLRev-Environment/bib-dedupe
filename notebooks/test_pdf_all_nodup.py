import os
import pandas as pd
from bib_dedupe.bib_dedupe import prep, block, match, cluster, merge
import multiprocessing

PDF_CSV_PATH = "/Users/jiangmingxin/.colrev/curated_metadata/journal-of-management-information-systems/data/search/pdfs.csv"
INPUT_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_all_nodup_input.csv"
DEDUPED_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_all_nodup_deduped.csv"

def run():
    os.makedirs(os.path.dirname(INPUT_CSV_PATH), exist_ok=True)

    df = pd.read_csv(PDF_CSV_PATH)
    if df.empty:
        print("Error: PDF dataset is empty.")
        return

    print(f"Original PDF dataset size: {df.shape[0]} records")

    df["ID"] = range(1, len(df) + 1)
    df.to_csv(INPUT_CSV_PATH, index=False)
    print(f"Saved full PDF dataset to: {INPUT_CSV_PATH}")

    print("Starting deduplication...")
    df_before = pd.read_csv(INPUT_CSV_PATH)
    print(f"Dataset size before deduplication: {df_before.shape[0]} records")

    df_prepared = prep(df_before.copy())
    blocked_df = block(df_prepared)
    matched_df = match(blocked_df)
    duplicate_id_sets = cluster(matched_df)
    df_after = merge(df_prepared, duplicate_id_sets=duplicate_id_sets)

    df_after.to_csv(DEDUPED_CSV_PATH, index=False)
    print(f"Deduplicated dataset saved to: {DEDUPED_CSV_PATH}")
    print(f"Dataset size after deduplication: {df_after.shape[0]} records")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    run()
