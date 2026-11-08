import os, httpx
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("LLM_BASE", "https://api.venice.ai/api/v1")
KEY = os.getenv("LLM_KEY", "")
MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b")

async def complete(prompt: str, temperature=0.8) -> str:
    headers = {}
    if KEY:
        headers["Authorization"] = "Bearer " + KEY
    async with httpx.AsyncClient(timeout=300) as h:
        r = await h.post(f"{BASE}/chat/completions",
            headers=headers,
            json={"model": MODEL, "temperature": temperature,
                  "max_tokens": 40,
                  "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
        content = (msg.get("content") or msg.get("reasoning") or "").strip()
        return content