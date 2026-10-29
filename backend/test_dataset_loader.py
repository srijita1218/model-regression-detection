import json
from pathlib import Path

import pytest

from backend.dataset_loader import load_dataset

GOLDEN = Path(__file__).resolve().parent.parent / "datasets" / "golden_dataset.json"


def test_loads_wrapper_shape(tmp_path):
    real_case = json.loads(GOLDEN.read_text())["cases"][0]
    f = tmp_path / "ds.json"
    f.write_text(json.dumps({"dataset_version": "9.9", "cases": [real_case]}))

    cases, version = load_dataset(str(f))

    assert version == "9.9"
    assert len(cases) == 1
    assert cases[0].id == real_case["id"]


def test_golden_dataset_loads_50_cases():
    cases, version = load_dataset(str(GOLDEN))
    assert len(cases) == 50
    assert version


def test_bare_list_is_rejected(tmp_path):
    f = tmp_path / "ds.json"
    f.write_text(json.dumps([{"id": "TC001"}]))
    with pytest.raises(TypeError):
        load_dataset(str(f))


def test_missing_cases_key_is_rejected(tmp_path):
    f = tmp_path / "ds.json"
    f.write_text(json.dumps({"dataset_version": "1"}))
    with pytest.raises(KeyError):
        load_dataset(str(f))


def test_invalid_case_fails_validation(tmp_path):
    f = tmp_path / "ds.json"
    f.write_text(json.dumps({"dataset_version": "1", "cases": [{"id": "TC001"}]}))
    with pytest.raises(Exception):  # pydantic ValidationError
        load_dataset(str(f))