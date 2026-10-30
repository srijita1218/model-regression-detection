import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

# Settings that make runs repeatable. Change them only on purpose,
# because every saved baseline depends on them.
TEMPERATURE = 0
SEED = 42


def generate(prompt: str) -> dict:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {
                "temperature": TEMPERATURE,
                "seed": SEED,
            },
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()