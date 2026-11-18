
"""
ModelWatch API layer (M5).

Thin wrapper around the existing pipeline: it calls evaluate_dataset()
and compare_runs() and never re-implements their logic.

Run from the project root:
    uvicorn backend.api:app --reload --port 8000
"""

import json
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
from backend.run_metadata import stamp_metadata
from backend.run_store import (
    save_run as persist_run,
    list_runs as list_saved_runs,
    get_run as load_saved_run,
)


# ---------- configuration ----------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
RUNS_DIR = RESULTS_DIR / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/tags"

RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

# Only one evaluation at a time.
EVAL_LOCK = threading.Lock()


# ---------- app + CORS ----------

app = FastAPI(title="ModelWatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- request schema ----------

class EvaluationRequest(BaseModel):
    prompt_path: str
    dataset_path: str = "datasets/golden_dataset.json"


# ---------- helpers ----------

def ollama_is_up() -> bool:
    """Return True if Ollama responds within three seconds."""
    try:
        return requests.get(OLLAMA_URL, timeout=3).ok
    except requests.RequestException:
        return False


def resolve_project_path(relative_path: str) -> Path:
    """Resolve a client-supplied path safely inside the project."""
    candidate = (PROJECT_ROOT / relative_path).resolve()

    if not candidate.is_relative_to(PROJECT_ROOT):
        raise HTTPException(
            status_code=400,
            detail="Path must be inside the project folder.",
        )

    if not candidate.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {relative_path}",
        )

    return candidate


def validate_run_id(run_id: str) -> None:
    if not RUN_ID_PATTERN.match(run_id):
        raise HTTPException(status_code=400, detail="Invalid run id.")


# ---------- endpoints ----------

@app.get("/health")
def health():
    """Check API availability, Ollama connectivity, and evaluation status."""
    return {
        "api": "ok",
        "ollama": ollama_is_up(),
        "busy": EVAL_LOCK.locked(),
    }


@app.post("/evaluations")
def create_evaluation(body: EvaluationRequest):
    """Run one prompt version against one dataset, save the run, and return it."""

    # 1. Validate inputs before doing anything slow.
    dataset_file = resolve_project_path(body.dataset_path)
    prompt_file = resolve_project_path(body.prompt_path)

    # 2. Fail fast if Ollama is down.
    if not ollama_is_up():
        raise HTTPException(
            status_code=503,
            detail=(
                "Ollama is not reachable on localhost:11434. "
                "Start it and try again."
            ),
        )

    # 3. Allow only one evaluation at a time.
    if not EVAL_LOCK.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="Another evaluation is already running.",
        )

    try:
        started = datetime.now()

        try:
            result = evaluate_dataset(
                str(dataset_file),
                str(prompt_file),
            )
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"Evaluation crashed: {error}",
            ) from error

        # Use the same metadata stamping logic as the CLI.
                # Use the same metadata stamping logic as the CLI.
        try:
            stamp_metadata(
                result,
                prompt_path=prompt_file,
                dataset_path=dataset_file,
                started=started,
            )
        except (OSError, ValueError) as error:
            raise HTTPException(
                status_code=500,
                detail=f"Could not read dataset metadata: {error}",
            ) from error
        # Save the run and update run history.
        try:
            persist_run(result, results_dir=RESULTS_DIR)
        except FileExistsError as error:
            raise HTTPException(
                status_code=409,
                detail=str(error),
            ) from error
        except (OSError, ValueError) as error:
            raise HTTPException(
                status_code=500,
                detail=f"Could not persist evaluation run: {error}",
            ) from error

        return result

    finally:
        EVAL_LOCK.release()


@app.get("/runs")
def list_runs():
    """Return saved run summaries, newest first."""
    try:
        saved_runs = list_saved_runs(results_dir=RESULTS_DIR)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read run history: {error}",
        ) from error

    return [
        {
            "run_id": run.get("run_id"),
            "timestamp": run.get("timestamp"),
            "prompt_version": run.get("prompt_version"),
            "dataset": run.get("dataset_name"),
            "status": run.get("status"),
            "category_accuracy": run.get("category_accuracy"),
        }
        for run in saved_runs
    ]


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    """Return one saved run in full."""
    validate_run_id(run_id)

    try:
        run = load_saved_run(run_id, results_dir=RESULTS_DIR)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read run {run_id}: {error}",
        ) from error

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found",
        )

    return run


def get_saved_run_or_404(run_id: str) -> dict:
    """Load a saved run or return an appropriate HTTP error."""
    validate_run_id(run_id)

    try:
        run = load_saved_run(run_id, results_dir=RESULTS_DIR)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read run {run_id}: {error}",
        ) from error

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found",
        )

    return run


@app.get("/compare")
def compare(baseline: str, current: str):
    """Compare two saved runs using the regression comparison logic."""
    baseline_run = get_saved_run_or_404(baseline)
    current_run = get_saved_run_or_404(current)

    # A failed run has no meaningful results to compare.
    for name, run in (
        ("baseline", baseline_run),
        ("current", current_run),
    ):
        if run.get("status") == "FAILED":
            raise HTTPException(
                status_code=422,
                detail=f"The {name} run failed and can't be compared.",
            )

    try:
        return run_comparison(
            str(RUNS_DIR / f"{baseline}.json"),
            str(RUNS_DIR / f"{current}.json"),
        )
    except (KeyError, TypeError, ZeroDivisionError) as error:
        raise HTTPException(
            status_code=422,
            detail=f"These runs can't be compared: {error!r}",
        ) from error
