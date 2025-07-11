#!/usr/bin/env python3
import csv
from pathlib import Path

BASE      = Path(__file__).parent      # exp_mis/pdf_only
IN_FILE   = BASE / "merged_record_ids.csv"
TMP_FILE  = BASE / "merged_record_ids.tmp.csv"

# 1) 读入所有行
with IN_FILE.open("r", encoding="utf-8") as src:
    reader = csv.reader(src)
    all_rows = list(reader)

if not all_rows:
    print(f"{IN_FILE} is empty. Nothing to do.")
    exit(0)

header, data_rows = all_rows[0], all_rows[1:]

# 2) 只保留以 P_ 开头的 ID
processed = []
for row in data_rows:
    ids = row[0].split(";")
    pdf_ids = [rid for rid in ids if rid.startswith("P_")]
    # 只要有 PDF-only ID，就保留这条聚类（即使只有一个）
    if pdf_ids:
        processed.append([";".join(sorted(pdf_ids))])

# 3) 写到临时文件
with TMP_FILE.open("w", newline="", encoding="utf-8") as dst:
    writer = csv.writer(dst)
    writer.writerow(header)
    writer.writerows(processed)

# 4) 覆盖原文件
TMP_FILE.replace(IN_FILE)
print(
    f"Filtered PDF-only clusters written to {IN_FILE} "
    f"({len(processed)} clusters remain)."
)
