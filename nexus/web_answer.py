"""`web_answer` tool — Google Search grounding bilan faktik/yangilik savollariga javob.

Gemini Interactions API (google-genai 2.24: `client.aio.interactions.create(model=...,
input=..., tools=[{"type": "google_search"}], generation_config={...})`) orqali
matnli model (`GEMINI_TEXT_MODEL`, standart `gemini-3.8-flash`) ishlatiladi.

Kengaytma kontrakti (registry): `TOOL_DECLARATIONS: list[dict]`,
`HANDLERS: dict[name, async handler(args) -> dict]`.

Javob strukturasi (SDK introspeksiyasi): `Interaction.output_text` (SDK
`steps` dan yig'adi) yoki `interaction.steps[-1].content[*].type == "text"` →
`.text`; `GoogleSearchResultStep.result` — manbalar (ixtiyoriy).
"""
from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any

log = logging.getLogger("nexus.web_answer")

MAX_ANSWER_CHARS = 1500
MAX_OUTPUT_TOKENS = 4096
DEFAULT_THINKING_LEVEL = "medium"
REQUEST_TIMEOUT_S = 45.0

TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "web_answer",
        "description": (
            "Answer a factual/current-events question using Google Search grounding; use when the user "
            "asks something you don't know or that needs fresh info (weather, news, prices, facts)."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "question": {
                    "type": "STRING",
                    "description": "The question to answer, in the user's language (uz/ru/en).",
                },
            },
            "required": ["question"],
        },
    },
]


# ---------------------------------------------------------------------------
# Toza yordamchilar
# ---------------------------------------------------------------------------
def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_text(interaction: Any) -> str:
    """Interaction javobidan matnni ajratadi (`output_text` → oxirgi model_output step → text itemlar)."""
    text = _get(interaction, "output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()
    steps = list(_get(interaction, "steps", None) or [])
    for step in reversed(steps):
        if _get(step, "type") == "user_input":
            break
        content = _get(step, "content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif _get(item, "type") in (None, "text"):
                    parts.append(str(_get(item, "text") or ""))
            joined = "".join(parts).strip()
            if joined:
                return joined
        direct = _get(step, "text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
    return ""


def extract_sources(interaction: Any, limit: int = 5) -> list[str]:
    """Google Search natijalaridan URL/sarlavhalar (bo'lsa)."""
    out: list[str] = []
    for step in list(_get(interaction, "steps", None) or []):
        if _get(step, "type") not in ("google_search_result", "retrieval_result"):
            continue
        result = _get(step, "result")
        items = result if isinstance(result, list) else [result] if result else []
        for it in items:
            uri = _get(it, "uri") or _get(it, "url")
            title = _get(it, "title")
            if uri:
                out.append(f"{title} — {uri}" if title else str(uri))
            if len(out) >= limit:
                return out
    return out


def truncate(text: str, limit: int = MAX_ANSWER_CHARS) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:") + "…"


def build_request(question: str, model: str, thinking_level: str | None) -> dict[str, Any]:
    return {
        "model": model,
        "input": question,
        "tools": [{"type": "google_search"}],
        "generation_config": {
            "thinking_level": (thinking_level or DEFAULT_THINKING_LEVEL).lower(),
            "max_output_tokens": MAX_OUTPUT_TOKENS,
        },
    }


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------
_client_factory: Any = None  # testlarda almashtiriladi


def _make_client(api_key: str) -> Any:
    if _client_factory is not None:
        return _client_factory(api_key)
    from google import genai

    return genai.Client(api_key=api_key)


async def _create(client: Any, request: dict[str, Any]) -> Any:
    aio = getattr(client, "aio", None)
    inter = getattr(aio, "interactions", None) if aio is not None else None
    if inter is not None and hasattr(inter, "create"):
        res = inter.create(**request)
        if inspect.isawaitable(res):
            return await res
        return res
    inter = getattr(client, "interactions", None)
    if inter is None:
        raise RuntimeError("SDK'da interactions API yo'q (google-genai>=2.24 kerak)")
    return await asyncio.to_thread(inter.create, **request)


async def web_answer(args: dict[str, Any]) -> dict[str, Any]:
    from nexus.config import settings

    question = str(args.get("question") or "").strip()
    if not question:
        return {"ok": False, "output": "", "error": "Savol bo'sh"}
    api_key = (getattr(settings, "gemini_api_key", "") or "").strip()
    if not api_key:
        return {"ok": False, "output": "", "error": "GEMINI_API_KEY sozlanmagan — web qidiruv ishlamaydi"}
    model = str(getattr(settings, "gemini_text_model", "") or "gemini-3.8-flash")
    request = build_request(question, model, getattr(settings, "thinking_level", "") or None)
    try:
        client = _make_client(api_key)
        interaction = await asyncio.wait_for(_create(client, request), timeout=REQUEST_TIMEOUT_S)
    except TimeoutError:
        return {"ok": False, "output": "", "error": "Web qidiruv vaqti tugadi (45 s)"}
    except Exception as e:  # noqa: BLE001
        log.warning("web_answer xatosi: %s: %s", type(e).__name__, e)
        msg = str(e)
        if "API key" in msg or "401" in msg or "403" in msg or "PERMISSION" in msg.upper():
            return {"ok": False, "output": "", "error": "Gemini API kaliti yaroqsiz yoki ruxsat yo'q"}
        return {"ok": False, "output": "", "error": f"Web qidiruv xatosi: {type(e).__name__}: {msg[:200]}"}

    text = extract_text(interaction)
    if not text:
        return {"ok": False, "output": "", "error": "Model javob qaytarmadi"}
    result: dict[str, Any] = {"ok": True, "output": truncate(text)}
    sources = extract_sources(interaction)
    if sources:
        result["note"] = "Manbalar: " + "; ".join(sources)
    return result


HANDLERS: dict[str, Any] = {"web_answer": web_answer}

__all__ = [
    "HANDLERS",
    "MAX_ANSWER_CHARS",
    "TOOL_DECLARATIONS",
    "build_request",
    "extract_sources",
    "extract_text",
    "truncate",
    "web_answer",
]
