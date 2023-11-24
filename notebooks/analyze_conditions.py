import pandas as pd

import bib_dedupe.conditions
from bib_dedupe.bib_dedupe import BibDeduper


data_path = "/home/gerit/ownCloud/projects/CoLRev/bib-dedupe/data/srsr"

try:
    fn = pd.read_csv(f"{data_path}/matches_FN_list.csv")
except pd.errors.EmptyDataError:
    fp = pd.DataFrame(columns=["colrev_origin", "case"])

try:
    fp = pd.read_csv(f"{data_path}/matches_FP_list.csv")
except pd.errors.EmptyDataError:
    fp = pd.DataFrame(columns=["colrev_origin", "case"])

pre_merged = pd.read_csv(f"{data_path}/records_pre_merged.csv")
pre_merged["colrev_origin"] = pre_merged["colrev_origin"].apply(eval).tolist()

selected_rows = pre_merged[
    pre_merged["colrev_origin"].apply(
        lambda x: any(item in x for item in fn["colrev_origin"])
    )
    | pre_merged["colrev_origin"].apply(
        lambda x: any(item in x for item in fp["colrev_origin"])
    )
]

deduper = BibDeduper()
records_for_dedupe = deduper.get_records_for_dedupe(records_df=selected_rows)

actual_blocked_df = deduper.block_pairs_for_deduplication(records_df=records_for_dedupe)

q_stats = {
    duplicate_condition: {
        # "TP": 0,
        "FP": 0,
        # "TN": 0,
        # "FN": 0
    }
    for duplicate_condition in bib_dedupe.conditions.duplicate_conditions
}

for i in range(len(actual_blocked_df)):
    item_df = actual_blocked_df.iloc[[i]]

    for duplicate_condition in bib_dedupe.conditions.duplicate_conditions:
        case = (
            f"{item_df['colrev_origin_1'].iloc[0]};{item_df['colrev_origin_2'].iloc[0]}"
        )
        if item_df.query(duplicate_condition).shape[0] > 0:
            if case in fp["case"].values:
                q_stats[duplicate_condition]["FP"] += 1
        # else:
        #     if case in fn['case'].values:
        #         q_stats[duplicate_condition]["FN"] += 1


q_stats_df = pd.DataFrame.from_dict(q_stats, orient="index")
q_stats_df.to_csv(f"{data_path}/q_stats.csv")

print(q_stats)
