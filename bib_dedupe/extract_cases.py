import pandas as pd

data_path = "/home/gerit/ownCloud/projects/CoLRev/bib-dedupe/data/neuroimaging"
target_path = "/home/gerit/ownCloud/projects/CoLRev/bib-dedupe/data/problem_cases"

fn = pd.read_csv(f"{data_path}/matches_FN_list.csv")
fp = pd.read_csv(f"{data_path}/matches_FP_list.csv")

records_df = pd.read_csv(f"{data_path}/records_pre_merged.csv")
records_df["colrev_origin"] = records_df["colrev_origin"].apply(eval).tolist()
records_df = records_df[
    records_df["ID"].isin(fn["ID"]) | records_df["ID"].isin(fp["ID"])
]

merged_record_origins_df = pd.read_csv(f"{data_path}/merged_record_origins.csv")
merged_record_origins_df["merged_origins"] = (
    merged_record_origins_df["merged_origins"].apply(eval).tolist()
)
all_origins = [x for list in records_df["colrev_origin"].tolist() for x in list]

merged_record_origins_df = merged_record_origins_df[
    merged_record_origins_df["merged_origins"].apply(
        lambda x: all(item in all_origins for item in x)
    )
]

merged_record_origins_df.to_csv(f"{target_path}/merged_record_origins.csv", index=False)
records_df.to_csv(f"{target_path}/records_pre_merged.csv", index=False)
