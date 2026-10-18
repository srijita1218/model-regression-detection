# backend/test_api.py
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.api as api

client = TestClient(api.app)


@pytest.fixture(autouse=True)
def isolated_runs_dir(tmp_path, monkeypatch):
    """Every test saves runs into a throwaway folder, never your real results/runs."""
    monkeypatch.setattr(api, "RUNS_DIR", tmp_path)


def fake_result(flags, error=None):
    """Minimal evaluator-shaped result; `flags` is a list of correct/incorrect booleans."""
    results = [
        {
            "id": f"TC{i:03d}",
            "expected_category": "billing",
            "actual_category": "billing" if ok else "other",
            "category_correct": ok,
            "summary_score": 0.9 if ok else 0.4,
            "latency_ms": 100.0,
            "error": error,
        }
        for i, ok in enumerate(flags, start=1)
    ]
    return {
        "total_cases": len(results),
        "correct_categories": sum(flags),
        "category_accuracy": sum(flags) / len(flags),
        "average_summary_score": 0.7,
        "latency": {"p95_ms": 100.0},
        "tokens": {},
        "results": results,
    }


def use_fake_pipeline(monkeypatch, result):
    """Pretend Ollama is up, paths exist, and the evaluator returns `result`."""
    monkeypatch.setattr(api, "ollama_is_up", lambda: True)
    monkeypatch.setattr(api, "resolve_project_path", lambda p: Path(p))
    monkeypatch.setattr(api, "evaluate_dataset", lambda dataset_path, prompt_path: result)


BODY = {"prompt_path": "prompts/v1.yaml", "dataset_path": "datasets/golden_dataset.json"}


def test_health_reports_ollama_down(monkeypatch):
    monkeypatch.setattr(api, "ollama_is_up", lambda: False)
    data = client.get("/health").json()
    assert data["api"] == "ok"
    assert data["ollama"] is False


def test_missing_run_returns_404():
    assert client.get("/runs/does_not_exist").status_code == 404


def test_unsafe_run_id_rejected():
    assert client.get("/runs/bad.id").status_code == 400


def test_post_saves_run_and_get_returns_it(monkeypatch):
    use_fake_pipeline(monkeypatch, fake_result([True, True, False]))

    posted = client.post("/evaluations", json=BODY)
    assert posted.status_code == 200
    run = posted.json()
    assert run["status"] == "COMPLETED"
    assert run["prompt_version"] == "v1"

    fetched = client.get(f"/runs/{run['run_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["run_id"] == run["run_id"]

    listing = client.get("/runs").json()
    assert [r["run_id"] for r in listing] == [run["run_id"]]


def test_post_returns_503_when_ollama_down(monkeypatch):
    use_fake_pipeline(monkeypatch, fake_result([True]))
    monkeypatch.setattr(api, "ollama_is_up", lambda: False)
    assert client.post("/evaluations", json=BODY).status_code == 503


def test_post_returns_409_when_busy(monkeypatch):
    use_fake_pipeline(monkeypatch, fake_result([True]))
    api.EVAL_LOCK.acquire()
    try:
        assert client.post("/evaluations", json=BODY).status_code == 409
    finally:
        api.EVAL_LOCK.release()


def test_all_cases_errored_marks_run_failed(monkeypatch):
    use_fake_pipeline(monkeypatch, fake_result([False, False], error="boom"))
    run = client.post("/evaluations", json=BODY).json()
    assert run["status"] == "FAILED"
    assert run["error_count"] == 2


def test_compare_two_saved_runs():
    api.save_run("base", {**fake_result([True, True, True, True]), "run_id": "base"})
    api.save_run("cur", {**fake_result([True, True, False, False]), "run_id": "cur"})

    response = client.get("/compare", params={"baseline": "base", "current": "cur"})
    assert response.status_code == 200
    assert response.json()["regression_count"] == 2


def test_compare_missing_run_returns_404():
    response = client.get("/compare", params={"baseline": "nope", "current": "nada"})
    assert response.status_code == 404