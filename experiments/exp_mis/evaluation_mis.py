#!/usr/bin/env python3
# evaluation_mis.py

from datetime import datetime
from pathlib import Path
import pandas as pd

from bib_dedupe.bib_dedupe import prep, block, match, cluster, merge
from bib_dedupe.dedupe_benchmark import DedupeBenchmarker

# 1. 脚本所在目录
BASE = Path(__file__).parent  # exp_mis/

# 2. 只跑这两组
DATASETS = ["baseline", "mixed"]

def append_to_output(result: dict, *, subset: str, package_name: str):
    """把结果写到 exp_mis/<subset>/evaluation.csv"""
    out_dir = BASE / subset
    out_dir.mkdir(exist_ok=True)
    out_csv = out_dir / "evaluation.csv"

    # 加 dataset 和 runtime
    result["dataset"] = subset
    result["time"]    = datetime.now().strftime("%Y-%m-%d %H:%M")
    result["package"] = package_name

    # 读旧表或新建
    if out_csv.exists():
        df = pd.read_csv(out_csv)
    else:
        df = pd.DataFrame(columns=[
            "package","time","dataset",
            "TP","FP","FN","TN",
            "false_positive_rate","specificity","sensitivity","precision","f1","runtime"
        ])

    new = pd.DataFrame([result])
    # 保持列顺序
    new = new[df.columns]
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(out_csv, index=False)

def run_one(subset: str):
    path = BASE / subset
    print(f"\n=== Evaluating {subset} ===")

    # 2. 用默认逻辑加载 .bib + merged_record_ids.csv
    bench = DedupeBenchmarker(benchmark_path=path)
    records_df = bench.get_records_for_dedupe()

    # 3. 跑四步去重
    t0 = datetime.now()
    df1 = prep(records_df)
    df2 = block(df1)
    df3 = match(df2)
    dup_ids = cluster(df3)
    df_merged = merge(records_df, duplicate_id_sets=dup_ids)
    runtime = (datetime.now() - t0).total_seconds()

    # 4. 对齐 & 记录结果
    res = bench.compare_dedupe_id(
        records_df=records_df,
        merged_df=df_merged,
        timestamp=t0
    )
    res["runtime"] = runtime
    append_to_output(res, subset=subset, package_name="bib-dedupe")

if __name__ == "__main__":
    for ds in DATASETS:
        run_one(ds)
