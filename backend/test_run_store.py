
import pytest

from backend.run_store import get_run, list_runs, save_run


def make_run(run_id, timestamp, accuracy):
    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "model": "llama2",
        "prompt_version": "v1",
        "dataset": "golden_dataset.json",
        "status": "COMPLETED",
        "total_cases": 10,
        "correct_categories": 8,
        "category_accuracy": accuracy,
        "average_summary_score": 0.7,
        "latency": {"average_ms": 5000},
        "tokens": {"total_tokens": 100},
        "results": [],
    }


def test_save_run_creates_files(tmp_path):
    run = make_run("run_001", "2026-10-18T10:00:00", 0.8)

    save_run(run, tmp_path)

    assert (tmp_path / "runs" / "run_001.json").is_file()
    assert (tmp_path / "latest.json").is_file()
    assert (tmp_path / "run_history.json").is_file()
    assert get_run("run_001", tmp_path) == run


def test_list_runs_returns_newest_first(tmp_path):
    save_run(make_run("old", "2026-10-17T10:00:00", 0.7), tmp_path)
    save_run(make_run("new", "2026-10-18T10:00:00", 0.9), tmp_path)

    runs = list_runs(tmp_path)

    assert [run["run_id"] for run in runs] == ["new", "old"]


def test_missing_run_returns_none(tmp_path):
    assert get_run("missing", tmp_path) is None


def test_empty_history_returns_empty_list(tmp_path):
    assert list_runs(tmp_path) == []


def test_duplicate_run_id_is_rejected(tmp_path):
    run = make_run("run_001", "2026-10-18T10:00:00", 0.8)
    save_run(run, tmp_path)

    with pytest.raises(FileExistsError):
        save_run(run, tmp_path)


def test_unsafe_run_id_is_rejected(tmp_path):
    run = make_run("../outside", "2026-10-18T10:00:00", 0.8)

    with pytest.raises(ValueError):
        save_run(run, tmp_path)
