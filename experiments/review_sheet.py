"""Build the human-review spreadsheet for librarians. Run from the repo root:  python experiments/review_sheet.py

One row per MERGED name: the tool put `name` in the same cluster as `canonical_name`. A reviewer reads the two names side by
side (with the ROR registry's record for each, as a hint) and picks a decision from a dropdown.

  Output: review/merge_review.xlsx   (sheets: Instructions, Review)

Decision words (dropdown in the sheet):
  Accepted   the two names are the same institution (the merge is right)
  Rejected   related but NOT the same: one is a part of the other (department, library, program)
  Unrelated  two completely different institutions
  Not sure   cannot tell from what is shown

ROR is only a hint: ROR matches are automatic and sometimes wrong, so reviewers are told to trust the names first.
Rows are sorted so the likeliest mistakes come first. Developed with AI assistance (Claude); see docs/AUTHORSHIP.md.
"""
import json
import os
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from rapidfuzz import fuzz

sys.path.insert(0, os.getcwd())
from decider import norm  # noqa: E402

TABLE, ROR = "data/normalized_names.csv", "data/ror_matches.jsonl"
OUT = "review/merge_review.xlsx"
os.makedirs("review", exist_ok=True)
DECISIONS = ["Accepted", "Rejected", "Unrelated", "Not sure"]

table = pd.read_csv(TABLE)
ror = {}
for line in open(ROR, encoding="utf-8"):
    r = json.loads(line)
    hit = [c for c in r["candidates"] if c.get("chosen")]
    if hit:
        ror[r["name"]] = hit[0]


def ror_text(name):
    h = ror.get(name)
    return (f"{h['ror_name']} ({', '.join(h.get('countries') or [])})", h["ror_id"]) if h else ("no ROR match", "")


def flags(a, b):
    """Reasons a reviewer should look closely. a = merged name, b = canonical name."""
    out = []
    ha, hb = ror.get(a), ror.get(b)
    if ha and hb and ha["ror_id"] != hb["ror_id"]:
        out.append("ROR IDs differ")
    na, nb = norm(a), norm(b)
    if na != nb and (na.startswith(nb) or nb.startswith(na)):
        out.append("one name contains the other")
    wa, wb = set(na.split()), set(nb.split())
    da, db = wa - wb, wb - wa
    if len(da) == 1 and len(db) == 1 and fuzz.ratio(next(iter(da)), next(iter(db))) < 75:
        out.append("differ by one word")
    if not ha or not hb:
        out.append("no ROR match")
    return out


rows = []
merged = table[table.name != table.canonical_name]
for _, r in merged.iterrows():
    f = flags(r["name"], r["canonical_name"])
    strong = [x for x in f if x != "no ROR match"]
    priority = "1 High" if strong else ("2 Medium" if f else "3 Low")
    na, ia = ror_text(r["name"])
    nb, ib = ror_text(r["canonical_name"])
    rows.append({"priority": priority, "name": r["name"], "canonical": r["canonical_name"], "ror_a": na, "id_a": ia, "ror_b": nb, "id_b": ib,
                 "why": "; ".join(f) if f else "", "repos": int(r["n_repos"])})
rows.sort(key=lambda x: (x["priority"], x["name"].lower()))

wb = Workbook()
ins = wb.active
ins.title = "Instructions"
text = [
    ("How to review", True),
    ("Each row shows two institution names that our tool grouped together. Please decide if the grouping is right.", False),
    ("", False),
    ("Choose one word in the 'Your decision' column (dropdown):", True),
    ("Accepted: the two names are the SAME institution (spelling, abbreviation, translation or typo).", False),
    ("Rejected: related but NOT the same: one is a part of the other (a library, department or program of the larger institution).", False),
    ("Unrelated: two completely different institutions.", False),
    ("Not sure: you cannot tell from what is shown. Add a note if you can.", False),
    ("", False),
    ("Tips", True),
    ("Trust the names first. The ROR columns are an automatic guess from the Research Organization Registry and can be wrong.", False),
    ("'Look closely because' lists reasons the tool is less certain. Rows are sorted so the likeliest mistakes come first.", False),
    ("You do not have to finish. Even 50 rows helps. Save the file and send it back.", False),
]
for i, (t, bold) in enumerate(text, 1):
    c = ins.cell(row=i, column=1, value=t)
    c.font = Font(bold=bold, size=13 if bold else 11)
    c.alignment = Alignment(wrap_text=True, vertical="top")
ins.column_dimensions["A"].width = 110

ws = wb.create_sheet("Review")
heads = ["Row", "Priority", "Name in re3data", "Tool grouped it with", "ROR record for the name", "ROR record for the grouped name",
         "Look closely because", "Repositories", "Your decision", "Notes (optional)"]
ws.append(heads)
for i, r in enumerate(rows, 1):
    ws.append([i, r["priority"], r["name"], r["canonical"], r["ror_a"], r["ror_b"], r["why"], r["repos"], None, None])
    for col, key in ((5, "id_a"), (6, "id_b")):
        if r[key]:
            ws.cell(row=i + 1, column=col).hyperlink = r[key]
for c in ws[1]:
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="2A78D6")
    c.alignment = Alignment(wrap_text=True, vertical="center")
for col, w in zip("ABCDEFGHIJ", (6, 10, 42, 42, 38, 38, 26, 12, 16, 34)):
    ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2):
    for c in row:
        c.alignment = Alignment(wrap_text=True, vertical="top")
    row[8].fill = PatternFill("solid", fgColor="FFF4CC")
ws.freeze_panes = "C2"
ws.auto_filter.ref = ws.dimensions
dv = DataValidation(type="list", formula1='"' + ",".join(DECISIONS) + '"', allow_blank=True, showErrorMessage=True,
                    errorTitle="Pick from the list", error="Choose Accepted, Rejected, Unrelated or Not sure.")
ws.add_data_validation(dv)
dv.add(f"I2:I{len(rows) + 1}")
wb.save(OUT)

counts = pd.Series([r["priority"] for r in rows]).value_counts().sort_index().to_dict()
print(f"wrote {OUT}: {len(rows)} rows to review; by priority: {counts}")
