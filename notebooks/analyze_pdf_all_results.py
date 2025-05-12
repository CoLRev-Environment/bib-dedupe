import pandas as pd

INPUT_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_all_nodup_input.csv"
DEDUPED_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_all_nodup_deduped.csv"
REMOVED_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_all_removed_records.csv"

df_before = pd.read_csv(INPUT_CSV_PATH)
df_after = pd.read_csv(DEDUPED_CSV_PATH)

removed = df_before[~df_before["ID"].isin(df_after["ID"])]

print(f"{len(removed)} records were removed during deduplication.")
print(removed[["ID", "author", "title"]].head())

removed.to_csv(REMOVED_CSV_PATH, index=False)
print(f"Removed records saved to: {REMOVED_CSV_PATH}")
