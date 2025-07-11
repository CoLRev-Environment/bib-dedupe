#!/usr/bin/env python3
import warnings
from pathlib import Path
from itertools import combinations

import bibtexparser
import pandas as pd

# 忽略不必要的警告
warnings.simplefilter("ignore")

from bib_dedupe.bib_dedupe import prep, block, match, cluster

# 输入：三个源的 .bib 路径 /Users/jiangmingxin/Desktop/bib-dedupe/experiments/exp_pacis/pacific-asia-conference-on-information-systems/data/search
BASE_DIR = Path("/Users/jiangmingxin/Desktop/bib-dedupe/experiments/exp_pacis/pacific-asia-conference-on-information-systems/data/search")
SOURCES = {
    "pdfs":     BASE_DIR / "pdfs.bib",
    # "crossref": BASE_DIR / "crossref.bib",
    "dblp":     BASE_DIR / "DBLP.bib",
}

# 输出目录
OUTPUT_DIR = Path("/Users/jiangmingxin/Desktop/bib-dedupe/experiments_output/output_pacis")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def bib_to_df(path: Path) -> pd.DataFrame:
    """将 .bib 读入 DataFrame，并保留所有原始字段和一列唯一 ID。"""
    with path.open(encoding="utf-8") as fh:
        db = bibtexparser.load(fh)
    df = pd.DataFrame(db.entries)
    # 确保有列 "ID"
    if "ID" not in df.columns:
        df["ID"] = df.index.astype(str)
    # 保存所有原始列名，用于后面导出
    df["__orig_index"] = df.index  # 备份行号
    return df

def run_pipeline(df: pd.DataFrame):
    """
    运行 prep→block→match→cluster，返回 dup_sets（list of sets of ID）。
    我们不再调用 merge()，因为要保留原始字段。
    """
    df1 = prep(df.copy())
    df2 = block(df1)
    df3 = match(df2)
    dup_sets = cluster(df3)
    return dup_sets

def export_clusters(name: str, df: pd.DataFrame, dup_sets: list[set]):
    """
    对每个簇大小 >1 的集合，导出到 CSV。
    每个源一个文件，包含列：cluster_id, plus all original df.columns.
    """
    rows = []
    for cid, members in enumerate(dup_sets, start=1):
        if len(members) <= 1:
            continue
        for rid in members:
            # 找到原始的整行
            rec = df[df["ID"] == rid].iloc[0]
            # 收集所有原始字段
            row = {"cluster": cid}
            for col in df.columns:
                row[col] = rec.get(col, "")
            rows.append(row)

    out_df = pd.DataFrame(rows)
    # —— 下面做一次列重排 —— 
    # 1) 把 cluster, title, author 三列拿出来放前面
    front_cols = ["cluster", "ID", "title", "author"]
    # 2) 然后加上其他所有列（排除已经在 front_cols 里的）
    other_cols = [c for c in out_df.columns if c not in front_cols]
    ordered_cols = front_cols + other_cols
    out_df = out_df[ordered_cols]

    out_path = OUTPUT_DIR / f"{name}_duplicate_clusters.csv"
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {len(out_df)} rows to {out_path}")

def main():
    for name, path in SOURCES.items():
        print(f"\nProcessing source: {name}")
        df = bib_to_df(path)
        print(f" Loaded {len(df)} records from {path.name}")
        dup_sets = run_pipeline(df)
        print(f" Found {sum(1 for s in dup_sets if len(s)>1)} duplicate clusters")
        export_clusters(name, df, dup_sets)

if __name__ == "__main__":
    main()
