"""Google Grounding 搜索辅助工具。

该模块封装了一个通过 Gemini Grounding 接口搜索网页引用的帮助函数，
支持通过依赖注入替换底层 SDK 客户端，方便在测试中模拟返回数据。
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional


GroundingResult = Dict[str, Optional[str]]
GroundingResponse = Dict[str, Any]
ClientFactory = Callable[[], Any]


def _default_client_factory() -> Any:
    """延迟导入 `google.generativeai`，以便在未安装 SDK 时也能运行测试。"""
    import google.generativeai as genai

    # 这里默认使用最新的 Gemini 1.5 Pro 模型以获取 Grounding 数据。
    return genai.GenerativeModel(model="gemini-1.5-pro-latest")


def _safe_get(obj: Any, *keys: str) -> Any:
    """兼容属性/字典访问，按顺序尝试返回嵌套字段。"""
    current = obj
    for key in keys:
        if current is None:
            return None
        if isinstance(current, Mapping):
            current = current.get(key)
        else:
            current = getattr(current, key, None)
    return current


def _format_chunk(chunk: Mapping[str, Any]) -> GroundingResult:
    web_info = chunk.get("web", {}) if isinstance(chunk, Mapping) else {}
    if not isinstance(web_info, Mapping):
        web_info = {}

    url = web_info.get("uri") or web_info.get("url") or web_info.get("displayUrl")
    title = web_info.get("title")
    snippet = chunk.get("text") if isinstance(chunk, Mapping) else None

    return {
        "url": url,
        "title": title,
        "snippet": snippet,
    }


def search_google_grounding(
    query: str,
    *,
    client_factory: ClientFactory = _default_client_factory,
    max_results: int = 5,
) -> GroundingResponse:
    """调用 Gemini Grounding API 并解析网页引用结果。

    返回统一结构：
    ```python
    {
        "query": 原始查询,
        "results": [
            {"url": str | None, "title": str | None, "snippet": str | None},
            ...
        ],
        "error": Optional[{"code": str, "message": str}],
    }
    ```
    """

    try:
        client = client_factory()
    except Exception as exc:  # pragma: no cover - 错误路径在单元测试中覆盖
        return {
            "query": query,
            "results": [],
            "error": {
                "code": "CLIENT_INIT_ERROR",
                "message": f"Failed to create Google Generative AI client: {exc}",
            },
        }

    try:
        response = client.generate_content(query)
    except Exception as exc:  # pragma: no cover - 在测试中通过假客户端覆盖
        return {
            "query": query,
            "results": [],
            "error": {
                "code": "API_ERROR",
                "message": str(exc),
            },
        }

    grounding_metadata = _safe_get(response, "grounding_metadata") or _safe_get(
        response, "groundingMetadata"
    )
    chunks: Iterable[Mapping[str, Any]] = (
        _safe_get(grounding_metadata, "grounding_chunks")
        or _safe_get(grounding_metadata, "groundingChunks")
        or []
    )

    results: List[GroundingResult] = []
    if isinstance(chunks, Iterable) and not isinstance(chunks, (str, bytes)):
        for chunk in chunks:
            if isinstance(chunk, Mapping):
                results.append(_format_chunk(chunk))
            else:
                # 兼容 SDK 返回对象的情况
                formatted = _format_chunk(getattr(chunk, "__dict__", {}))
                results.append(formatted)

    results = results[: max(0, max_results)]

    if not results:
        return {
            "query": query,
            "results": [],
            "error": {
                "code": "NO_RESULTS",
                "message": "Google Grounding returned no grounding chunks.",
            },
        }

    return {
        "query": query,
        "results": results,
        "error": None,
    }


__all__ = ["search_google_grounding", "GroundingResult", "GroundingResponse"]
