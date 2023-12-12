import time
from datetime import datetime

import pandas as pd


print("Extract-cases started at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
start_time = time.time()

data_path = "../data/neuroimaging"
target_path = "../data/problem_cases"

fn = pd.read_csv(f"{data_path}/matches_FN_list.csv")
fp = pd.read_csv(f"{data_path}/matches_FP_list.csv")

records_df = pd.read_csv(f"{data_path}/records_pre_merged.csv")
records_df.reset_index(drop=True, inplace=True)
records_df = records_df[
    records_df["ID"].isin(fn["ID"]) | records_df["ID"].isin(fp["ID"])
]

merged_record_ids_df = pd.read_csv(f"{data_path}/merged_record_ids.csv")
all_ids = records_df["ID"].tolist()


merged_record_ids_df = merged_record_ids_df[
    merged_record_ids_df["case"].apply(lambda x: all(item in all_ids for item in x))
]

merged_record_ids_df.to_csv(f"{target_path}/merged_record_ids.csv", index=False)
records_df.to_csv(f"{target_path}/records_pre_merged.csv", index=False)

end_time = time.time()
print(f"Extract-cases completed after: {end_time - start_time:.2f} seconds")
