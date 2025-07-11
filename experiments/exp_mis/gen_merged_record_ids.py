#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path

import bibtexparser

# 用法检查
if len(sys.argv) != 2 or sys.argv[1] not in ("baseline", "pdf_only", "mixed"):
    print("Usage: python gen_merged_record_ids.py <baseline|pdf_only|mixed>")
    sys.exit(1)

subset = sys.argv[1]
BASE   = Path(__file__).parent
SUB    = BASE / subset
REC    = SUB / "records.bib"
OUT    = SUB / "merged_record_ids.csv"

# 来源文件名到前缀的映射
PREFIX = {
    "CROSSREF.bib": "C",
    "DBLP.bib":     "D",
    "pdfs.bib":     "P",
}

# 载入 BibTeX
with REC.open(encoding="utf-8") as bibfile:
    db = bibtexparser.load(bibfile)

# 用来提取 "文件名/ID" 这两部分
pattern = re.compile(r"([^;{}\s]+\.bib)/([^;{}\s]+)")

clusters = {}  # map: 原簇 key -> set of prefixed IDs

for entry in db.entries:
    orig = entry.get("colrev_origin", "").replace("\n", "").replace(" ", "")
    if not orig:
        continue

    # 找所有 "xxx.bib/000123" 这样的片段
    parts = pattern.findall(orig)
    if not parts:
        continue

    # for this entry, 构造一组 prefixed IDs
    prefixed_ids = []
    for fname, rid in parts:
        prefix = PREFIX.get(fname)
        if prefix:
            prefixed_ids.append(f"{prefix}_{rid}")
    if not prefixed_ids:
        continue

    # 我们用原始 origin 字符串作为簇的 key
    key = orig
    clusters.setdefault(key, set()).update(prefixed_ids)

# 写出 CSV
with OUT.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh)
    writer.writerow(["merged_ids"])
    for prefset in clusters.values():
        # 排序只是为了可读性
        row = ";".join(sorted(prefset))
        writer.writerow([row])

print(f"Wrote {len(clusters)} clusters to {OUT}")
