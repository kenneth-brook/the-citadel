import requests
from core.config import CONFIG

def call_llm(system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": CONFIG.llm_model,
        "prompt": f"<system>{system_prompt}</system>\n<user>{user_prompt}</user>",
        "stream": False
    }

    resp = requests.post(CONFIG.llm_endpoint, json=payload, timeout=600)
    resp.raise_for_status()
    data = resp.json()

    # Ollama uses "response" or "output" depending on model
    return data.get("response") or data.get("output") or str(data)
