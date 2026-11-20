"""Normalize institution names: one command from the raw re3data institution list to a clean, reviewable table.

    python normalize.py                                              # uses data/institutions_clean.csv, writes to out/
    python normalize.py --input my_institutions.csv --out results/

Input : a CSV with columns repo_id and institution_name (one row per repository-institution link).
Output (in --out):
    normalized_names.csv   one row per distinct name: cluster_id, canonical_name, parent_name, parent_canonical, n_repos, cluster_size
    review_list.csv        names a human should check (see review.py), with the reason
    report.txt             counts and the five largest clusters

The method is rules only (decider.py), so the same input always gives the same output. See docs/ for how it was measured.
Developed with AI assistance (Claude); see docs/AUTHORSHIP.md.
"""
import argparse
import os

import pandas as pd

from cluster import build_table
from review import review_flags


def normalize(input_csv: str, out_dir: str) -> dict:
    inst = pd.read_csv(input_csv).dropna(subset=["institution_name"])
    inst["institution_name"] = inst["institution_name"].astype(str)
    repo_counts = inst.groupby("institution_name").repo_id.nunique()
    names = sorted(repo_counts.index)            # sorted so the output never depends on file order

    table = build_table(names, repo_counts)
    flags = review_flags(table)

    os.makedirs(out_dir, exist_ok=True)
    table.to_csv(os.path.join(out_dir, "normalized_names.csv"), index=False, encoding="utf-8")
    flags.to_csv(os.path.join(out_dir, "review_list.csv"), index=False, encoding="utf-8")

    n_clusters = table.cluster_id.nunique()
    sizes = table.groupby(["cluster_id", "canonical_name"]).size().reset_index(name="n")
    biggest = sizes.sort_values(["n", "canonical_name"], ascending=[False, True]).head(5)     # ties broken by name, so the order is fixed
    lines = [
        f"input rows (repository-institution links): {len(inst)}",
        f"distinct names: {len(table)}",
        f"institutions (clusters): {n_clusters}",
        f"names merged into another spelling: {len(table) - n_clusters}",
        f"names with a parent link: {int(table.parent_name.notna().sum())}",
        f"names flagged for human review: {len(flags)}",
        "",
        "five largest clusters (number of spellings, canonical name):",
    ]
    for _, row in biggest.iterrows():
        lines.append(f"  {row.n:>3}  {row.canonical_name}")
    with open(os.path.join(out_dir, "report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return {"names": len(table), "clusters": n_clusters, "flagged": len(flags), "report": "\n".join(lines)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--input", default="data/institutions_clean.csv", help="CSV with repo_id and institution_name")
    ap.add_argument("--out", default="out", help="folder for the results")
    args = ap.parse_args()
    result = normalize(args.input, args.out)
    print(result["report"])
    print(f"\nwrote {args.out}/normalized_names.csv, review_list.csv, report.txt")
