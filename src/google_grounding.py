"""Utilities for retrieving Google Grounding references for strategies."""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Mapping, Optional, Sequence


Logger = Callable[[str], None]


def _default_warning_logger(message: str) -> None:
    logging.getLogger(__name__).warning(message)


def _safe_get(source: Any, key: str, default: Any = None) -> Any:
    """Read a key/attribute from dict-like or attribute-based objects."""

    if source is None:
        return default
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _normalise_reference(chunk: Any) -> Optional[dict[str, str]]:
    web_block = _safe_get(chunk, "web", chunk)
    if web_block is None:
        return None

    uri = _safe_get(web_block, "uri")
    title = _safe_get(web_block, "title")
    snippet = _safe_get(web_block, "snippet") or _safe_get(web_block, "description")

    if not any([uri, title, snippet]):
        return None

    reference: dict[str, str] = {
        "uri": str(uri) if uri is not None else "",
        "title": str(title) if title is not None else "",
        "snippet": str(snippet) if snippet is not None else "",
    }

    return reference


def search_google_grounding(
    strategy: Mapping[str, Any],
    client_factory: Callable[[], Any],
    *,
    logger: Optional[Logger] = None,
    use_mock: bool = False,
    test_mode: bool = False,
) -> list[dict[str, str]]:
    """Fetch supporting references for a strategy using Google Grounding search."""

    warn = logger or _default_warning_logger

    if use_mock or test_mode:
        warn("[Grounding] Skipping googleSearch because mock/test mode is enabled.")
        return []

    try:
        client = client_factory()
    except Exception as exc:  # pragma: no cover - defensive, verified via unit tests
        warn(f"[Grounding] Unable to construct Google GenAI client: {exc}")
        return []

    search_callable: Optional[Callable[[Mapping[str, Any]], Any]] = None

    try:
        tools = getattr(client, "tools", None)
        if tools is not None:
            search_callable = getattr(tools, "googleSearch", None)
        else:
            search_callable = getattr(client, "googleSearch", None)
    except Exception:  # pragma: no cover - defensive fallback
        search_callable = None

    if not callable(search_callable):
        warn("[Grounding] googleSearch tool is unavailable on the provided client.")
        return []

    query_parts: list[str] = []
    for key in ("strategy_name", "rationale", "initial_assumption"):
        value = strategy.get(key) if isinstance(strategy, Mapping) else None
        if value:
            query_parts.append(str(value))

    if not query_parts:
        query_parts.append(str(strategy))

    payload = {"query": " ".join(query_parts)}

    try:
        response = search_callable(payload)
    except Exception as exc:
        warn(f"[Grounding] googleSearch call failed: {exc}")
        return []

    metadata = _safe_get(response, "groundingMetadata", {})
    chunks: Sequence[Any] = _safe_get(metadata, "groundingChunks", []) or []

    references: list[dict[str, str]] = []
    for chunk in chunks:
        normalised = _normalise_reference(chunk)
        if normalised:
            references.append(normalised)

    return references


def default_google_grounding_client_factory() -> Any:
    """Best-effort factory for Google GenAI clients with the googleSearch tool."""

    try:
        import google.generativeai as genai
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("google.generativeai package is not installed") from exc

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not configured")

    genai.configure(api_key=api_key)

    try:
        client = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[{"googleSearch": {}}],
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(f"Failed to initialise GenerativeModel: {exc}") from exc

    tools = getattr(client, "tools", None)
    if tools is None or not hasattr(tools, "googleSearch"):
        raise RuntimeError("Generated client does not expose a googleSearch tool")

    return client

