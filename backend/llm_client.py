import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama2"


def generate(prompt: str) -> dict:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()