import pandas as pd

INPUT_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_200_nodup_input.csv"
DEDUPED_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_200_nodup_deduped.csv"
REMOVED_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_200_removed_records.csv"
CONTEXT_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_200_removed_with_neighbors.csv"

# Load data
df_before = pd.read_csv(INPUT_CSV_PATH)
df_after = pd.read_csv(DEDUPED_CSV_PATH)

# Find removed IDs
removed_ids = set(df_before["ID"]) - set(df_after["ID"])
print(f"{len(removed_ids)} records were removed during deduplication.")

# Save removed records directly
removed_records = df_before[df_before["ID"].isin(removed_ids)]
removed_records.to_csv(REMOVED_CSV_PATH, index=False)
print(f"Removed records saved to: {REMOVED_CSV_PATH}")

# Find neighbors: ID - 1, ID, ID + 1
neighbor_ids = set()
for rid in removed_ids:
    neighbor_ids.update([rid - 1, rid, rid + 1])

# Make sure IDs are within bounds
neighbor_ids = [i for i in neighbor_ids if 1 <= i <= df_before["ID"].max()]
context_records = df_before[df_before["ID"].isin(neighbor_ids)].sort_values("ID")
context_records.to_csv(CONTEXT_CSV_PATH, index=False)

print(f"{len(context_records)} context records (including neighbors) saved to: {CONTEXT_CSV_PATH}")
