#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
from colrev.loader import load_utils

BASE = Path(__file__).parent

def bib_to_df(rel_path: str) -> pd.DataFrame:
    bib_path = BASE / rel_path
    if not bib_path.is_file():
        raise FileNotFoundError(f"{bib_path} nor found")
    records = load_utils.load(filename=bib_path, unique_id_field="ID")
    df = (pd.DataFrame.from_dict(records, orient="index")
          .reset_index()
          .rename(columns={"index": "ID"}))
    df = df.reset_index(drop=True)
    return df

def main():
    df_cr = bib_to_df("mis-quarterly/data/search/CROSSREF.bib")
    df_db = bib_to_df("mis-quarterly/data/search/DBLP.bib")

    df_cr = df_cr.loc[:, ~df_cr.columns.duplicated()]
    df_db = df_db.loc[:, ~df_db.columns.duplicated()]
    df_baseline = pd.concat([df_cr, df_db], ignore_index=True)
    df_baseline.to_csv(BASE / "baseline.csv", index=False)
    print("baseline.csv", BASE / "baseline.csv")

    
    df_pdf = bib_to_df("mis-quarterly/data/search/pdfs.bib")
    df_pdf.to_csv(BASE / "pdf_only.csv", index=False)
    print("pdf_only.csv", BASE / "pdf_only.csv")

    df_pdf = df_pdf.loc[:, ~df_pdf.columns.duplicated()]
    df_mixed = pd.concat([df_baseline, df_pdf], ignore_index=True)
    df_mixed.to_csv(BASE / "mixed.csv", index=False)
    print("mixed.csv", BASE / "mixed.csv")

if __name__ == "__main__":
    main()

