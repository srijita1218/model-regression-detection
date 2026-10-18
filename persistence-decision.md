# M6 — ModelWatch Persistence Decision

## Decision

ModelWatch will use JSON-file-based persistence for the current prototype.

## Why JSON?

- The project is currently a local, single-user regression detection tool.
- JSON is easy to inspect, debug, version and exchange with the frontend and API.
- The current evaluation pipeline already produces JSON results.
- It avoids adding database setup and migration complexity before it is needed.

## Storage design

- `results/latest.json`: the most recent evaluation, retained for compatibility with existing scripts.
- `results/runs/<run_id>.json`: a permanent copy of each evaluation.
- `results/run_history.json`: an index of saved runs and their metadata.

## Required operations

- Save a completed evaluation.
- List previous runs, newest first.
- Retrieve a complete run using its `run_id`.
- Return a clear error when a requested run does not exist.

## Future integration

The persistence functions will remain independent of FastAPI. The API layer can call them to retrieve runs, and the frontend can use the API to display run history.

## Future migration

SQLite can be considered if ModelWatch later requires more complex querying, concurrent writes, larger history, or stronger transactional guarantees.