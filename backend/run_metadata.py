# backend/run_metadata.py
"""Metadata stamping shared by the CLI (run_evaluation.py) and the API (api.py)."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.llm_client import MODEL_NAME

RUN_ID_FORMAT = "%Y%m%d_%H%M%S_%f"


def read_dataset_version(dataset_path, strict=False):
    """Best-effort read of dataset_version from the dataset file; None if unavailable."""
    try:
        with open(dataset_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("dataset_version") if isinstance(data, dict) else None
    except (OSError, ValueError) as error:
        if strict:
            raise error
        return None


def stamp_metadata(
    result: dict[str, Any],
    *,
    prompt_path: str | Path,
    dataset_path: str | Path,
    started: datetime | None = None,
) -> dict[str, Any]:
    """Add run_id, timestamp, prompt_version, model, dataset, status to an evaluator result (in place)."""
    started = started or datetime.now()
    prompt_path, dataset_path = Path(prompt_path), Path(dataset_path)

    result["run_id"] = started.strftime(RUN_ID_FORMAT)
    result["timestamp"] = started.isoformat()
    result["prompt_version"] = prompt_path.stem
    result["model"] = MODEL_NAME
    result["dataset"] = dataset_path.name
    result["dataset_name"] = dataset_path.name
    # setdefault: if the evaluator already recorded a dataset_version, keep it.
    result.setdefault("dataset_version", read_dataset_version(dataset_path))

    # If EVERY case errored the run is useless; mark it FAILED instead of "0% accuracy".
    total = result.get("total_cases", 0)
    error_count = sum(1 for case in result.get("results", []) if case.get("error"))
    result["error_count"] = error_count
    result["status"] = "FAILED" if total > 0 and error_count == total else "COMPLETED"
    return result
