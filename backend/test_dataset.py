import json, re, pathlib
import pytest

DATA = json.loads(pathlib.Path("datasets/golden_dataset.json").read_text())
CASES = DATA["cases"]
CATEGORIES = {"billing", "technical", "account", "general"}
DIFFICULTIES = {"easy", "medium", "hard"}  # match whatever you actually use

def test_wrapper():
    assert DATA["dataset_version"]
    assert len(CASES) == 50

def test_ids_unique_and_wellformed():
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"TC\d{3}", i) for i in ids)

@pytest.mark.parametrize("c", CASES, ids=lambda c: c["id"])
def test_case(c):
    assert c["expected_category"] in CATEGORIES
    assert c["difficulty"] in DIFFICULTIES
    assert c["input"]["text"].strip()
    assert c["expected_summary"].strip()