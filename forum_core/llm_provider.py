from __future__ import annotations

import os
DEFAULT_LLM_MODEL = "openai/gpt-4o-mini"


class LLMProviderError(RuntimeError):
    pass


def get_llm_model() -> str:
    return DEFAULT_LLM_MODEL


def _get_dedalus_client():
    try:
        from dedalus_labs import Dedalus  # type: ignore
    except ImportError as exc:  # pragma: no cover - import guard
        raise LLMProviderError(
            "Dedalus SDK not installed. Add 'dedalus-labs' to requirements."
        ) from exc

    api_key = os.getenv("DEDALUS_API_KEY", "").strip()
    if not api_key:
        raise LLMProviderError("DEDALUS_API_KEY is not configured.")
    return Dedalus(api_key=api_key)


def _close_client(client: object) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        close()


def _extract_text_from_content(content: object) -> str:
    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, str) and item.strip():
            parts.append(item.strip())
            continue
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())

    return "\n".join(parts).strip()


def run_llm(messages: list[dict[str, str]]) -> str:
    client = _get_dedalus_client()
    try:
        try:
            completion = client.chat.completions.create(
                model=get_llm_model(),
                messages=messages,
                temperature=0,
            )
        except Exception as exc:
            raise LLMProviderError(f"Dedalus call failed: {exc}") from exc
    finally:
        _close_client(client)

    try:
        message = completion.choices[0].message
    except (AttributeError, IndexError, TypeError) as exc:
        raise LLMProviderError("Dedalus returned an empty response.") from exc

    refusal = getattr(message, "refusal", None)
    if isinstance(refusal, str) and refusal.strip():
        raise LLMProviderError(f"Dedalus refused the request: {refusal.strip()}")

    output_text = _extract_text_from_content(getattr(message, "content", None))
    if not output_text:
        raise LLMProviderError("Dedalus returned no text output.")
    return output_text
