"""Utility helpers for Google Search Grounding."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from google.generativeai import client
from google.generativeai.client import glm


DEFAULT_GROUNDED_MODEL = "models/gemini-1.5-flash"


class GroundingSearchError(RuntimeError):
    """Raised when Google Search Grounding fails."""


def _ensure_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GroundingSearchError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please export your Gemini API key before calling Google Search Grounding."
        )
    return api_key


def _configure_clients(api_key: str) -> client.glm.GenerativeServiceClient:
    # Configure both the high-level module and the lower-level GAPIC client.
    genai.configure(api_key=api_key)
    client.configure(api_key=api_key)
    return client.get_default_generative_client()


def _extract_results(
    metadata: Optional[glm.GroundingMetadata], top_k: Optional[int]
) -> List[Dict[str, str]]:
    if not metadata:
        return []

    chunk_results: Dict[int, Dict[str, str]] = {}
    for index, chunk in enumerate(metadata.grounding_chunks):
        web_chunk = chunk.web
        if not web_chunk:
            continue
        chunk_results[index] = {
            "title": web_chunk.title or "",
            "url": web_chunk.uri or "",
            "snippet": "",
        }

    if not chunk_results:
        return []

    for support in metadata.grounding_supports:
        segment = support.segment
        if not segment or not segment.text:
            continue
        snippet_text = segment.text.strip()
        if not snippet_text:
            continue
        for chunk_index in support.grounding_chunk_indices:
            item = chunk_results.get(chunk_index)
            if not item:
                continue
            if item["snippet"]:
                if snippet_text not in item["snippet"]:
                    item["snippet"] = f"{item['snippet']} {snippet_text}".strip()
            else:
                item["snippet"] = snippet_text

    ordered_results = [chunk_results[index] for index in sorted(chunk_results.keys())]

    for entry in ordered_results:
        entry["snippet"] = entry["snippet"].strip()

    if top_k is not None and top_k > 0:
        return ordered_results[:top_k]
    return ordered_results


def search_google_grounding(
    query: str, *, top_k: Optional[int] = None, model: str = DEFAULT_GROUNDED_MODEL
) -> Dict[str, Any]:
    """Run a Google Search Grounding query.

    Args:
        query: Natural language query to send to Google Search Grounding.
        top_k: Optional cap on the number of search results returned.
        model: The Gemini model used for the underlying call.

    Returns:
        A dictionary containing ``results`` (list of dictionaries with
        ``title``, ``url``, and ``snippet``) and ``grounding_metadata`` (raw
        metadata for downstream use).

    Raises:
        GroundingSearchError: If the API key is missing, the query is empty,
            or the Google API call fails.
    """

    if not query or not query.strip():
        raise GroundingSearchError("Query must be a non-empty string.")

    if top_k is not None and top_k <= 0:
        raise GroundingSearchError("top_k must be a positive integer when provided.")

    api_key = _ensure_api_key()

    try:
        generative_client = _configure_clients(api_key)
    except Exception as exc:  # pragma: no cover - configuration errors are rare
        raise GroundingSearchError(
            "Failed to configure Google Generative AI client. "
            "Please verify your GEMINI_API_KEY and local network settings."
        ) from exc

    request = glm.GenerateContentRequest(
        model=model,
        contents=[glm.Content(role="user", parts=[glm.Part(text=query.strip())])],
        tools=[glm.Tool(google_search_retrieval=glm.GoogleSearchRetrieval())],
        generation_config=glm.GenerationConfig(candidate_count=1, temperature=0.0),
    )

    try:
        response = generative_client.generate_content(request=request)
    except google_exceptions.Unauthenticated as exc:
        raise GroundingSearchError(
            "Authentication failed when calling Google Search Grounding. "
            "Please confirm that GEMINI_API_KEY is correct and has Search "
            "Grounding access enabled."
        ) from exc
    except google_exceptions.GoogleAPICallError as exc:
        raise GroundingSearchError(
            "Unable to reach Google Search Grounding. "
            "Check your internet connection and ensure the Grounding API is available."
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise GroundingSearchError(
            "An unexpected error occurred while querying Google Search Grounding."
        ) from exc

    metadata = getattr(response, "grounding_metadata", None)
    results = _extract_results(metadata, top_k)
    raw_metadata: Optional[Dict[str, Any]] = None

    if metadata:
        try:
            raw_metadata = type(metadata).to_dict(metadata)
        except Exception:  # pragma: no cover - fallback just keeps original object
            raw_metadata = metadata  # type: ignore[assignment]

    return {
        "query": query.strip(),
        "model": model,
        "results": results,
        "grounding_metadata": raw_metadata,
    }
