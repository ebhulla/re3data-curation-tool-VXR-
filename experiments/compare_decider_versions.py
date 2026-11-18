"""Show exactly which pair decisions changed between two versions of decider.py. Run from the repo root:

    python experiments/compare_decider_versions.py              # committed version (HEAD) vs your working copy, on the train pairs
    python experiments/compare_decider_versions.py HEAD~1 val   # any git ref, any split (train, val, test)

Prints accuracy for both versions, how many decisions changed, which changes moved a pair from right to wrong or wrong to right
(against the AI judge's label), and examples of each. Use it after every rule change: a score that drops is not enough information;
this tells you WHICH pairs moved and why. (Do not run it on the test split while developing.)
Developed with AI assistance (Claude); see docs/AUTHORSHIP.md.
"""
import os
import subprocess
import sys
import types
from collections import Counter

import pandas as pd

sys.path.insert(0, os.getcwd())
ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
split = sys.argv[2] if len(sys.argv) > 2 else "train"

src = subprocess.run(["git", "show", f"{ref}:decider.py"], capture_output=True, text=True, encoding="utf-8", check=True).stdout
old = types.ModuleType("old_decider")
exec(compile(src, f"decider@{ref}", "exec"), old.__dict__)
import decider as new  # noqa: E402

df = pd.read_csv(f"data/pairs_{split}.csv")
old_pred = [old.decide(a, b) for a, b in zip(df.name_a, df.name_b)]
new_pred = [new.decide(a, b) for a, b in zip(df.name_a, df.name_b)]
labels = df["label"].tolist()
acc = lambda pred: sum(p == lab for p, lab in zip(pred, labels)) / len(df)  # noqa: E731
print(f"{split}: {len(df)} pairs   accuracy  {ref}: {acc(old_pred):.3f}   working copy: {acc(new_pred):.3f}")

rows = [(a, b, lab, o, n) for a, b, lab, o, n in zip(df.name_a, df.name_b, labels, old_pred, new_pred) if o != n]
now_right = [r for r in rows if r[4] == r[2]]
now_wrong = [r for r in rows if r[3] == r[2]]
print(f"decisions changed: {len(rows)}   fixed (wrong -> right): {len(now_right)}   broke (right -> wrong): {len(now_wrong)}")
print("changes by (old answer -> new answer):", dict(Counter((r[3], r[4]) for r in rows)))


def show(title, items, k=15):
    print(f"\n{title} (first {min(k, len(items))} of {len(items)})")
    for a, b, lab, o, n in items[:k]:
        print(f"  judge={lab:<9} {o:<9} -> {n:<9} | {a} | {b}")


show("BROKE: was right, now wrong", now_wrong)
show("FIXED: was wrong, now right", now_right)
