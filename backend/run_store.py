
"""Persistence helpers for ModelWatch evaluation runs."""

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"


def _read_json(path: Path) -> Any:
    """Read a JSON file as Python data."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, data: Any) -> None:
    """Write JSON safely, using a temporary file before replacing the target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")

    temporary_path.replace(path)


def _history_path(results_dir: Path) -> Path:
    return results_dir / "run_history.json"


def _run_metadata(run: dict[str, Any], run_path: Path) -> dict[str, Any]:
    """Extract lightweight metadata for the history index."""
    metrics = run.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}

    return {
    "run_id": run["run_id"],
    "timestamp": run.get("timestamp"),
    "model": run.get("model"),
    "prompt_version": run.get("prompt_version"),
    "dataset_name": run.get("dataset_name") or run.get("dataset"),
    "status": run.get("status"),
    "category_accuracy": run.get("category_accuracy"),
    "metrics": metrics,
    "result_file": str(Path("runs") / run_path.name),
}


def save_run( 
    run: dict[str, Any],
    results_dir: Path = DEFAULT_RESULTS_DIR,
) -> dict[str, Any]:
    """Save one evaluation permanently and update latest.json and run_history.json."""
    if not run.get("run_id"):
        raise ValueError("A run must contain a non-empty run_id.")

    results_dir = Path(results_dir)
    runs_dir = results_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    run_id = str(run["run_id"])

    # Keep run IDs safe to use as filenames.
    if Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a simple filename-safe identifier.")

    run_path = runs_dir / f"{run_id}.json"

    if run_path.exists():
        raise FileExistsError(
            f"Run {run_id!r} already exists. Generate a unique run_id."
        )

    _write_json(run_path, run)
    _write_json(results_dir / "latest.json", run)

    history_path = _history_path(results_dir)
    if history_path.exists():
        history = _read_json(history_path)
    else:
        history = {"runs": []}

    if not isinstance(history, dict) or not isinstance(
        history.get("runs"), list
    ):
        raise ValueError("run_history.json must contain a 'runs' list.")

    metadata = _run_metadata(run, run_path)
    history["runs"] = [
        item
        for item in history["runs"]
        if item.get("run_id") != run_id
    ]
    history["runs"].append(metadata)
    history["runs"].sort(
        key=lambda item: item.get("timestamp") or "",
        reverse=True,
    )

    _write_json(history_path, history)
    return run


def list_runs(
    results_dir: Path = DEFAULT_RESULTS_DIR,
) -> list[dict[str, Any]]:
    """Return saved run metadata, newest first."""
    results_dir = Path(results_dir)
    history_path = _history_path(results_dir)

    if not history_path.exists():
        return []

    history = _read_json(history_path)
    if not isinstance(history, dict) or not isinstance(
        history.get("runs"), list
    ):
        raise ValueError("run_history.json must contain a 'runs' list.")

    return sorted(
        history["runs"],
        key=lambda item: item.get("timestamp") or "",
        reverse=True,
    )


def get_run(
    run_id: str,
    results_dir: Path = DEFAULT_RESULTS_DIR,
) -> dict[str, Any] | None:
    """Return the full saved run, or None if it does not exist."""
    results_dir = Path(results_dir)
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        return None

    run_path = results_dir / "runs" / f"{run_id}.json"
    if not run_path.is_file():
        return None

    run = _read_json(run_path)
    if run.get("run_id") != run_id:
        raise ValueError("Saved run ID does not match its filename.")

    return run
