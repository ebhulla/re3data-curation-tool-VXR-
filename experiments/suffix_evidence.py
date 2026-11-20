"""For pairs where one name is the other plus exactly ONE extra word (no commas), show how the AI judge labeled them, per extra word.
Run from the repo root:  python experiments/suffix_evidence.py [split]      (default: train; do not use test while developing)

This is the evidence for the allow-list in decider.py: a word is safe to treat as a harmless suffix only if the pairs it appears in are
mostly judged 'duplicate'. If they are mostly 'hierarchy', the word names a part (library, department...) and must NOT be allowed.
Developed with AI assistance (Claude); see docs/AUTHORSHIP.md.
"""
import os
import sys
from collections import Counter, defaultdict

import pandas as pd

sys.path.insert(0, os.getcwd())
from decider import norm  # noqa: E402

split = sys.argv[1] if len(sys.argv) > 1 else "train"
df = pd.read_csv(f"data/pairs_{split}.csv")
by_word = defaultdict(Counter)
for a, b, lab in zip(df.name_a, df.name_b, df.label):
    na, nb = norm(a), norm(b)
    if len(na) == len(nb) or "," in a or "," in b:
        continue
    long_n, short_n = (na, nb) if len(na) > len(nb) else (nb, na)
    if long_n.startswith(short_n):
        extra = long_n[len(short_n):].split()
        if len(extra) == 1:
            by_word[extra[0]][lab] += 1

rows = sorted(by_word.items(), key=lambda kv: -sum(kv[1].values()))
print(f"{split}: pairs where one name = the other + exactly one word   (judge labels)")
print(f"{'extra word':<16}{'n':>3}  {'duplicate':>9}  {'hierarchy':>9}  {'unrelated':>9}")
for w, c in rows:
    print(f"{w:<16}{sum(c.values()):>3}  {c['duplicate']:>9}  {c['hierarchy']:>9}  {c['unrelated']:>9}")
