# backend/api.py
"""
ModelWatch API layer (M5).
Thin wrapper around the existing pipeline: it calls evaluate_dataset() and
compare_runs() and never re-implements their logic.

Run from the project root:
    uvicorn backend.api:app --reload --port 8000
"""
import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.evaluator import evaluate_dataset
from backend.regression import compare_runs as run_comparison
# NOTE: do NOT import run_evaluation here. It has no __main__ guard, so
# importing it would start a full evaluation.

# ---------- configuration ----------

# api.py lives in backend/, so two levels up is the project root.
# Using absolute paths means nothing breaks if uvicorn is started from
# a different folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "results" / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)   # the folder must exist before we save

MODEL_NAME = "llama2"                         # keep in sync with llm_client.py
OLLAMA_URL = "http://localhost:11434/api/tags"  # lightweight "is Ollama alive?" endpoint

# Run IDs end up inside file paths, so only allow safe characters.
# This blocks things like "../../secrets".
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

# Only one evaluation at a time: it saturates Ollama on a laptop, and
# two overlapping runs would both be slow and distort latency numbers.
EVAL_LOCK = threading.Lock()

# ---------- app + CORS ----------

app = FastAPI(title="ModelWatch API")

# Lets the Leptos frontend (localhost:8080) call this server (localhost:8000).
# "*" is fine for a local single-user tool; restrict it if this is ever deployed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- request schema ----------


class EvaluationRequest(BaseModel):
    prompt_path: str                                     # e.g. "prompts/v1.yaml"
    dataset_path: str = "datasets/golden_dataset.json"   # same default as run_evaluation.py


# ---------- helpers ----------


def ollama_is_up() -> bool:
    """True if Ollama answers within 3 seconds. Used to fail fast with a clear error."""
    try:
        return requests.get(OLLAMA_URL, timeout=3).ok
    except requests.RequestException:
        return False


def resolve_project_path(relative_path: str) -> Path:
    """
    Turn a client-supplied path into a safe absolute path.
    Rejects paths that escape the project folder or don't exist, so a bad
    request returns a clean 4xx instead of crashing deep inside the evaluator.
    """
    candidate = (PROJECT_ROOT / relative_path).resolve()
    if not candidate.is_relative_to(PROJECT_ROOT):
        raise HTTPException(status_code=400, detail="Path must be inside the project folder.")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {relative_path}")
    return candidate


def validate_run_id(run_id: str) -> None:
    if not RUN_ID_PATTERN.match(run_id):
        raise HTTPException(status_code=400, detail="Invalid run id.")


def save_run(run_id: str, result: dict) -> None:
    """
    Write to a temp file first, then rename. The rename is atomic, so a crash
    mid-write can never leave a half-written (corrupt) run file behind.
    """
    final_path = RUNS_DIR / f"{run_id}.json"
    temp_path = final_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    os.replace(temp_path, final_path)


def load_run(run_id: str) -> dict:
    validate_run_id(run_id)
    path = RUNS_DIR / f"{run_id}.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Run {run_id} file is corrupted")


# ---------- endpoints ----------
# These are plain `def`, not `async def`, on purpose. They do blocking work
# (file I/O, a minutes-long evaluation). FastAPI runs plain `def` handlers in a
# worker thread, so the server stays responsive while an evaluation runs.


@app.get("/health")
def health():
    """Quick status check: is the API up, is Ollama reachable, is a run in progress?"""
    return {"api": "ok", "ollama": ollama_is_up(), "busy": EVAL_LOCK.locked()}


@app.post("/evaluations")
def create_evaluation(body: EvaluationRequest):
    """Run one prompt version against one dataset, save the run, return it."""
    # 1. Validate inputs BEFORE doing anything slow.
    dataset_file = resolve_project_path(body.dataset_path)
    prompt_file = resolve_project_path(body.prompt_path)

    # 2. Fail fast if Ollama is down (otherwise every case would error out).
    if not ollama_is_up():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not reachable on localhost:11434. Start it and try again.",
        )

    # 3. Allow only one evaluation at a time. Don't wait, just refuse.
    if not EVAL_LOCK.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another evaluation is already running.")

    try:
        # Same ID format as run_evaluation.py, so CLI and API runs look alike.
        started = datetime.now()
        run_id = started.strftime("%Y%m%d_%H%M%S")

        try:
            result = evaluate_dataset(str(dataset_file), str(prompt_file))
        except Exception as error:
            # Per-case failures are already handled inside evaluate_dataset.
            # Anything reaching here is a whole-run failure (e.g. bad dataset file).
            raise HTTPException(status_code=500, detail=f"Evaluation crashed: {error}") from error

        # Same metadata run_evaluation.py stamps on its results.
        result["run_id"] = run_id
        result["timestamp"] = started.isoformat()
        result["prompt_version"] = prompt_file.stem
        result["model"] = MODEL_NAME
        result["dataset"] = dataset_file.name

        # If EVERY case errored (e.g. Ollama died mid-run) the run is useless.
        # Mark it FAILED instead of letting it show up as a misleading "0% accuracy".
        total = result.get("total_cases", 0)
        error_count = sum(1 for case in result.get("results", []) if case.get("error"))
        result["error_count"] = error_count
        result["status"] = "FAILED" if total > 0 and error_count == total else "COMPLETED"

        save_run(run_id, result)
        return result
    finally:
        EVAL_LOCK.release()   # always release, even if something above raised


@app.get("/runs")
def list_runs():
    """Short summary of every saved run, newest first. The dashboard will need this."""
    summaries = []
    # Run IDs are timestamps, so reverse alphabetical order = newest first.
    for path in sorted(RUNS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue   # skip an unreadable file instead of breaking the whole list
        summaries.append({
            "run_id": data.get("run_id", path.stem),
            "timestamp": data.get("timestamp"),
            "prompt_version": data.get("prompt_version"),
            "dataset": data.get("dataset"),
            "status": data.get("status"),
            "category_accuracy": data.get("category_accuracy"),
        })
    return summaries


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    """Return one saved run in full."""
    return load_run(run_id)


@app.get("/compare")
def compare(baseline: str, current: str):
    """Compare two saved runs with the McNemar + regression logic."""
    baseline_run = load_run(baseline)   # 400/404 if invalid or missing
    current_run = load_run(current)

    # A failed run has no meaningful results to compare.
    for name, run in (("baseline", baseline_run), ("current", current_run)):
        if run.get("status") == "FAILED":
            raise HTTPException(status_code=422, detail=f"The {name} run failed and can't be compared.")

    try:
        # compare_runs() takes file paths, not dicts.
        return run_comparison(
            str(RUNS_DIR / f"{baseline}.json"),
            str(RUNS_DIR / f"{current}.json"),
        )
    except (KeyError, TypeError, ZeroDivisionError) as error:
        # Malformed run files, or a baseline P95 of 0, shouldn't produce a bare 500.
        raise HTTPException(status_code=422, detail=f"These runs can't be compared: {error!r}")