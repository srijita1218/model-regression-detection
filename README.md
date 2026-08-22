# ModelWatch

ModelWatch is an LLM prompt regression detection system.

It compares different prompt versions against an evaluation dataset and identifies regressions before prompt changes are deployed.

## Tech Stack

### Frontend
- Rust
- Leptos
- WebAssembly
- Tailwind CSS

### Backend
- Python
- FastAPI
- Ollama
- SQLite

## Project Structure

```text
modelwatch/
├── frontend/    # Rust + Leptos frontend
├── backend/     # FastAPI backend and evaluation engine
├── prompts/     # Versioned YAML prompts
└── datasets/    # Evaluation datasets