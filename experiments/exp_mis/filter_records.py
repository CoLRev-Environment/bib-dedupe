#!/usr/bin/env python3
import bibtexparser
from pathlib import Path

BASE = Path(__file__).parent
SRC  = BASE / "mis-quarterly/data/records.bib"
with SRC.open(encoding="utf-8") as f:
    db = bibtexparser.load(f)

def write_subset(name, keep_fn):
    out = bibtexparser.bibdatabase.BibDatabase()
    out.entries = [e for e in db.entries if keep_fn(e.get("colrev_origin",""))]
    path = BASE / Path(name) / "records.bib"
    path.parent.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        bibtexparser.dump(out, f)
    print(f"Wrote {len(out.entries)} entries to {path}")

write_subset("baseline",
             lambda origin: "CROSSREF.bib" in origin or "DBLP.bib" in origin)

write_subset("pdf_only",
             lambda origin: "pdfs.bib" in origin)

write_subset("mixed",
             lambda origin: True)
