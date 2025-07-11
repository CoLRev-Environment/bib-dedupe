#!/usr/bin/env python3
import warnings
from pathlib import Path
from datetime import datetime

import pandas as pd
from bib_dedupe.bib_dedupe import prep, block, match, cluster, merge
from bib_dedupe.dedupe_benchmark import DedupeBenchmarker

# 抑制那些 FutureWarning 和 pandas 链式赋值警告
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

BASE     = Path(__file__).parent
DATASETS = ["baseline", "mixed"]

def evaluate(subset: str):
    print(f"\n=== Evaluating {subset} ===")

    # DedupeBenchmarker 会自动加载：
    #  - records_pre_merged.csv 作为 records_df
    #  - merged_record_ids.csv 作为真值
    bench = DedupeBenchmarker(benchmark_path=BASE / subset)
    records_df = bench.get_records_for_dedupe()
    print(f"{datetime.now()}  Loaded {len(records_df)} records")

    # --- 清洗可能的 NaN/float 字段，特别是作者 AUTHOR 字段 ---
    from bib_dedupe.constants.fields import AUTHOR
    if AUTHOR in records_df.columns:
        records_df[AUTHOR] = records_df[AUTHOR].fillna("").astype(str)

    # 1) prep
    timestamp = datetime.now()
    df1 = prep(records_df)

    # 2) block
    df2 = block(df1)

    # 3) match
    df3 = match(df2)

    # 4) cluster
    dup_sets = cluster(df3)

    # 5) merge （此时 AUTHOR 列已全是字符串，merge 不会再报 float 长度错误）
    merged_df = merge(records_df, duplicate_id_sets=dup_sets)

    # 6) 比对指标
    result = bench.compare_dedupe_id(
        records_df=records_df,
        merged_df=merged_df,
        timestamp=timestamp
    )

    # 打印关键指标
    print(f"\nResults for {subset}:")
    print(f"  TP  = {result['TP']}")
    print(f"  FP  = {result['FP']}")
    print(f"  FN  = {result['FN']}")
    print(f"  TN  = {result.get('TN', 'n/a')}")
    print(f"  Precision            = {result['precision']:.4f}")
    print(f"  Recall (Sensitivity) = {result['sensitivity']:.4f}")
    print(f"  Specificity          = {result['specificity']:.4f}")
    print(f"  F1 Score             = {result['f1']:.4f}")

def main():
    for ds in DATASETS:
        evaluate(ds)

if __name__ == "__main__":
    main()
