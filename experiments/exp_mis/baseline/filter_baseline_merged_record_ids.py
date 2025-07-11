#!/usr/bin/env python3
import csv
from pathlib import Path

BASE     = Path(__file__).parent      # exp_mis/baseline
IN_FILE  = BASE / "merged_record_ids.csv"
TMP_FILE = BASE / "merged_record_ids.tmp.csv"

# 1) 先把原来的内容全读进列表
with IN_FILE.open("r", encoding="utf-8") as src:
    reader = csv.reader(src)
    all_rows = list(reader)

if not all_rows:
    print(f"{IN_FILE} is empty. Nothing to do.")
    exit(1)

header, data_rows = all_rows[0], all_rows[1:]

# 2) 对每一行，只保留不以 P_ 开头的 ID
processed = []
for row in data_rows:
    ids = row[0].split(";")
    filtered_ids = [rid for rid in ids if not rid.startswith("P_")]
    # 如果过滤后还有至少一个 ID，就保留；如果都被删光了，就跳过
    if filtered_ids:
        processed.append([";".join(filtered_ids)])

# 3) 写到临时文件
with TMP_FILE.open("w", newline="", encoding="utf-8") as dst:
    writer = csv.writer(dst)
    writer.writerow(header)
    writer.writerows(processed)

# 4) 覆盖回原文件
TMP_FILE.replace(IN_FILE)
print(f"Rewrote {IN_FILE} with P_-IDs removed ({len(processed)} clusters remain).")
