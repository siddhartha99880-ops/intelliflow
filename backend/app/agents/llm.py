from __future__ import annotations

from typing import Any

from app.core.config import get_settings


def _fallback_json(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    # Keep deterministic output so the demo runs without OpenAI credentials.
    return {
        "kind": kind,
        "input": payload,
        "output": {
            "summary": f"[fallback summary] {payload.get('text') or payload.get('message') or ''}".strip(),
            "selected_condition_key": payload.get("preferred_condition_key", "default"),
            "draft": f"[fallback draft] Please review: {payload.get('text') or payload.get('message') or ''}".strip(),
            "extracted": payload.get("extracted", payload.get("text") or payload.get("message")),
            "status": "ok",
        },
    }


async def run_llm_json(kind: str, prompt: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Centralized LLM runner.
    - If OpenAI is not configured, returns deterministic fallback JSON.
    - If configured, uses LangChain ChatOpenAI to produce JSON output.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        return _fallback_json(kind, input_payload)

    # Optional real implementation (kept intentionally simple for a demo MVP).
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )
    message = (
        "Return ONLY valid JSON. "
        "Keys you may include depending on the agent type: summary, selected_condition_key, draft, extracted.\n\n"
        f"Prompt ({kind}):\n{prompt}\n\n"
        f"Input payload:\n{input_payload}\n"
    )
    resp = await llm.ainvoke([HumanMessage(content=message)])
    # LangChain returns content as string; parse conservatively.
    import json

    try:
        parsed = json.loads(resp.content)
    except Exception:
        parsed = {"raw": resp.content}
    return {"kind": kind, "input": input_payload, "output": parsed}

