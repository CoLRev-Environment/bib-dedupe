#!/usr/bin/env python3
"""
gen_records_pre_merged.py <baseline|mixed>

Reads the individual .bib sources for the given subset,
prefixes each record ID according to its origin (C_/D_/P_),
and writes out records_pre_merged.csv with all fields plus:
  - ID           (prefixed)
  - orig_ID      (original numeric ID)
  - orig_source  (crossref|dblp|pdf)
"""
import sys
from pathlib import Path

import bibtexparser
import pandas as pd

SRC_MAP = {
    "CROSSREF.bib": ("C", "crossref"),
    "DBLP.bib":     ("D", "dblp"),
    "pdfs.bib":     ("P", "pdf"),
}

if len(sys.argv) != 2 or sys.argv[1] not in ("baseline", "mixed", "pdf_only"):
    print("Usage: python gen_records_pre_merged.py <baseline|mixed|pdf_only>")
    sys.exit(1)

subset = sys.argv[1]
BASE   = Path(__file__).parent
DATA   = BASE / "mis-quarterly" / "data" / "search"
OUT    = BASE / subset / "records_pre_merged.csv"

if subset == "baseline":
    bib_files = ["CROSSREF.bib", "DBLP.bib"]
elif subset == "mixed":
    bib_files = ["CROSSREF.bib", "DBLP.bib", "pdfs.bib"]
elif subset == "pdf_only":
    bib_files = ["pdfs.bib"]
else:
    raise ValueError("Unknown subset")

all_dfs = []
for bib_file in bib_files:
    path = DATA / bib_file
    prefix, src = SRC_MAP[bib_file]
    with path.open(encoding="utf-8") as fh:
        bib = bibtexparser.load(fh)
    df = pd.DataFrame(bib.entries)
    if df.empty:
        continue
    df["orig_ID"] = df["ID"]
    df["ID"] = df["orig_ID"].apply(lambda rid: f"{prefix}_{rid}")
    df["orig_source"] = src
    all_dfs.append(df)

full = pd.concat(all_dfs, ignore_index=True)
cols = ["ID", "orig_ID", "orig_source"] + [c for c in full.columns if c not in ("ID","orig_ID","orig_source")]
full = full[cols]

full.to_csv(OUT, index=False)
print(f"Wrote {len(full)} records to {OUT}")
