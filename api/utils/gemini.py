from typing import List, Dict, Any, Optional
import requests
from utils.settings import GOOGLE_API_KEY, GEMINI_MODEL

GEMINI_URL_TMPL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

def generate_answer_with_gemini(
    question: str,
    context: str,
    sources: Optional[List[Dict[str, Any]]] = None
) -> str:
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is missing. Set it in api/.env")

    source_lines = [f"- {s.get('citation', 'unknown')}" for s in (sources or [])]

    prompt = (
        "You are a helpful assistant answering questions about a YouTube video's transcript.\n"
        "Rules:\n"
        "1) Use only provided context.\n"
        "2) If context is insufficient, say so clearly.\n"
        "3) Keep answers concise and factual.\n"
        "4) Include brief citations like [video_id @ mm:ss] when possible.\n\n"
        f"Question:\n{question}\n\n"
        f"Context:\n{context}\n\n"
        f"Available citations:\n" + "\n".join(source_lines)
    )

    url = GEMINI_URL_TMPL.format(model=GEMINI_MODEL, api_key=GOOGLE_API_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
    }

    resp = requests.post(url, json=payload, timeout=45)
    resp.raise_for_status()
    data = resp.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return "I could not generate a response from the model."