#!/usr/bin/env python3
import warnings
from pathlib import Path
from datetime import datetime
import itertools

import pandas as pd
from bib_dedupe.bib_dedupe import prep, block, match, cluster, merge
from bib_dedupe.dedupe_benchmark import DedupeBenchmarker
from bib_dedupe.constants.fields import ID as FIELD_ID, AUTHOR, TITLE, DOI

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

BASE     = Path(__file__).parent
DATASETS = ["pdf_only", "baseline", "mixed"]

def evaluate(subset: str):
    print(f"\n=== Evaluating {subset} ===")
    subset_dir = BASE / subset

    bench = DedupeBenchmarker(benchmark_path=subset_dir)
    records_df = bench.get_records_for_dedupe()
    print(f"{datetime.now()}  Loaded {len(records_df)} records")

    if AUTHOR in records_df.columns:
        records_df[AUTHOR] = records_df[AUTHOR].fillna("").astype(str)

    timestamp = datetime.now()
    df1 = prep(records_df)
    df2 = block(df1)
    df3 = match(df2)
    dup_sets = cluster(df3)   
    merged_df = merge(records_df, duplicate_id_sets=dup_sets)

    result = bench.compare_dedupe_id(
        records_df=records_df,
        merged_df=merged_df,
        timestamp=timestamp
    )

    print(f"\nResults for {subset}:")
    print(f"  TP  = {result['TP']}")
    print(f"  FP  = {result['FP']}")
    print(f"  FN  = {result['FN']}")
    print(f"  TN  = {result.get('TN', 'n/a')}")
    print(f"  Precision            = {result['precision']:.4f}")
    print(f"  Recall (Sensitivity) = {result['sensitivity']:.4f}")
    print(f"  Specificity          = {result['specificity']:.4f}")
    print(f"  F1 Score             = {result['f1']:.4f}")

    pred_pairs = set(itertools.chain.from_iterable(
        itertools.combinations(cluster, 2) for cluster in dup_sets
    ))
    true_pairs = set(itertools.chain.from_iterable(
        itertools.combinations(tc, 2) for tc in bench.true_merged_ids
    ))
    fp_pairs = pred_pairs - true_pairs
    print(f"{datetime.now()}  Found {len(fp_pairs)} false positive pairs, exporting...")

    df_idx = records_df.set_index(FIELD_ID)
    rows = []
    for cid, pair in enumerate(fp_pairs):
        id1, id2 = sorted(pair)
        r1, r2 = df_idx.loc[id1], df_idx.loc[id2]
        rows.append({
            "cluster_id": cid,
            "id1": id1,
            "title1": r1.get(TITLE, ""),
            "author1": r1.get(AUTHOR, ""),
            "doi1": r1.get(DOI, ""),
            "id2": id2,
            "title2": r2.get(TITLE, ""),
            "author2": r2.get(AUTHOR, ""),
            "doi2": r2.get(DOI, ""), 
        })
    fp_df = pd.DataFrame(rows)
    out_fp = subset_dir / "false_positives.csv"
    fp_df.to_csv(out_fp, index=False, encoding="utf-8")
    print(f"{datetime.now()}  False positives saved to {out_fp}")

def main():
    for ds in DATASETS:
        evaluate(ds)

if __name__ == "__main__":
    main()
