"""End-to-end test of normalize.py on a tiny made-up institution list."""
import pandas as pd

from normalize import normalize


def _write_input(path):
    rows = [("r1", "Universität Heidelberg"), ("r2", "University Heidelberg"), ("r3", "University Heidelberg"),
            ("r4", "Ohio State University"), ("r5", "Iowa State University"),
            ("r6", "Cornell University"), ("r7", "Cornell University Library"),
            ("r8", "University of Oxford"), ("r9", "University of Oxford, Oxford e-Research Centre")]
    pd.DataFrame(rows, columns=["repo_id", "institution_name"]).to_csv(path, index=False)


def test_normalize_end_to_end(tmp_path):
    src, out = tmp_path / "in.csv", tmp_path / "out"
    _write_input(src)
    result = normalize(str(src), str(out))
    table = pd.read_csv(out / "normalized_names.csv").set_index("name")

    assert result["names"] == 8        # "University Heidelberg" is used by two repositories but is one name
    for f in ("normalized_names.csv", "review_list.csv", "report.txt"):
        assert (out / f).exists()
    # spelling variants merge; the canonical name is the spelling used by the most repositories
    assert table.loc["Universität Heidelberg", "cluster_id"] == table.loc["University Heidelberg", "cluster_id"]
    assert table.loc["Universität Heidelberg", "canonical_name"] == "University Heidelberg"
    # different institutions stay apart, and a part is not merged into its parent
    assert table.loc["Ohio State University", "cluster_id"] != table.loc["Iowa State University", "cluster_id"]
    assert table.loc["Cornell University Library", "cluster_id"] != table.loc["Cornell University", "cluster_id"]
    # the comma pattern gives a parent link
    assert table.loc["University of Oxford, Oxford e-Research Centre", "parent_name"] == "University of Oxford"


def test_normalize_is_deterministic(tmp_path):
    src = tmp_path / "in.csv"
    _write_input(src)
    normalize(str(src), str(tmp_path / "a"))
    normalize(str(src), str(tmp_path / "b"))
    first = (tmp_path / "a" / "normalized_names.csv").read_text(encoding="utf-8")
    second = (tmp_path / "b" / "normalized_names.csv").read_text(encoding="utf-8")
    assert first == second
