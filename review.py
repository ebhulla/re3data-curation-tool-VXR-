"""YOUR FILE (Ekam): decide which clusters a human should look at.

`review_flags(table)` receives the normalized table (one row per name) with these columns:
    name, cluster_id, canonical_name, parent_name, parent_canonical, n_repos, cluster_size
and must return a pandas DataFrame with one row per flagged name and the columns
    name, cluster_id, reason

Ideas for reasons (the audit showed which mistakes are most common):
  - a name shares a cluster with its own parent ("University of Toronto" and "University of Toronto Libraries")
  - an unusually large cluster (many spellings: more likely a chain merge)
  - names in a cluster that differ by one distinctive word (see decider.one_word_swap)

Until you write it, this stub flags nothing, so `python normalize.py` still runs.
"""
import pandas as pd


def review_flags(table: pd.DataFrame) -> pd.DataFrame:
    # TODO(Ekam): return the flagged names. Start with ONE reason, check it on data/normalized_names.csv, then add more.
    return pd.DataFrame(columns=["name", "cluster_id", "reason"])
