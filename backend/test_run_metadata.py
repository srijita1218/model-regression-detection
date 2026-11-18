import json
from datetime import datetime
from pathlib import Path

from backend.llm_client import MODEL_NAME
from backend.run_metadata import read_dataset_version, stamp_metadata


def test_read_dataset_version_valid(tmp_path):
    dataset_file = tmp_path / "test_data.json"
    dataset_file.write_text(json.dumps({"dataset_version": "v3.1", "cases": []}))
    assert read_dataset_version(dataset_file) == "v3.1"


def test_read_dataset_version_missing_file(tmp_path):
    assert read_dataset_version(tmp_path / "non_existent.json") is None


def test_read_dataset_version_invalid_json(tmp_path):
    bad_file = tmp_path / "corrupt.json"
    bad_file.write_text("{not valid json")
    assert read_dataset_version(bad_file) is None


def test_read_dataset_version_not_a_dict(tmp_path):
    list_file = tmp_path / "list.json"
    list_file.write_text("[]")
    assert read_dataset_version(list_file) is None


def test_stamp_metadata_completed(tmp_path):
    dataset_file = tmp_path / "golden.json"
    dataset_file.write_text(json.dumps({"dataset_version": "1.0"}))
    prompt_file = tmp_path / "prompts" / "v1.yaml"

    result = {
        "total_cases": 2,
        "results": [
            {"id": "T1", "category_correct": True, "error": None},
            {"id": "T2", "category_correct": False, "error": None},
        ],
    }

    fixed_time = datetime(2026, 11, 18, 12, 0, 0, 123456)
    stamped = stamp_metadata(
        result,
        prompt_path=prompt_file,
        dataset_path=dataset_file,
        started=fixed_time,
    )

    assert stamped["run_id"] == "20261118_120000_123456"
    assert stamped["timestamp"] == fixed_time.isoformat()
    assert stamped["prompt_version"] == "v1"
    assert stamped["model"] == MODEL_NAME
    assert stamped["dataset"] == "golden.json"
    assert stamped["dataset_name"] == "golden.json"
    assert stamped["dataset_version"] == "1.0"
    assert stamped["error_count"] == 0
    assert stamped["status"] == "COMPLETED"


def test_stamp_metadata_failed_when_all_cases_error(tmp_path):
    dataset_file = tmp_path / "dataset.json"
    dataset_file.write_text(json.dumps({"dataset_version": "2.0"}))

    result = {
        "total_cases": 2,
        "results": [
            {"id": "T1", "category_correct": False, "error": "Connection error"},
            {"id": "T2", "category_correct": False, "error": "Timeout"},
        ],
    }

    stamped = stamp_metadata(
        result,
        prompt_path="prompts/v2.yaml",
        dataset_path=dataset_file,
    )

    assert stamped["error_count"] == 2
    assert stamped["status"] == "FAILED"


def test_stamp_metadata_preserves_existing_dataset_version(tmp_path):
    dataset_file = tmp_path / "dataset.json"
    dataset_file.write_text(json.dumps({"dataset_version": "from_file"}))

    result = {
        "total_cases": 1,
        "dataset_version": "already_set",
        "results": [{"id": "T1", "category_correct": True, "error": None}],
    }

    stamped = stamp_metadata(
        result,
        prompt_path="prompts/v1.yaml",
        dataset_path=dataset_file,
    )

    assert stamped["dataset_version"] == "already_set"


def test_stamp_metadata_zero_cases_is_completed(tmp_path):
    dataset_file = tmp_path / "dataset.json"
    dataset_file.write_text(json.dumps({"dataset_version": "1.0"}))

    result = {
        "total_cases": 0,
        "results": [],
    }

    stamped = stamp_metadata(
        result,
        prompt_path="prompts/v1.yaml",
        dataset_path=dataset_file,
    )

    assert stamped["error_count"] == 0
    assert stamped["status"] == "COMPLETED"
