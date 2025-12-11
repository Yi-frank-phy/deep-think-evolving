"""
Knowledge Base Tools for Outer Loop Memory System.

Provides tools for LLM agents to:
1. Write lessons/experiences to the knowledge base
2. Retrieve relevant past experiences

The knowledge base is a vectorized file system that persists across sessions.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import numpy as np
from langchain_core.tools import tool

from src.embedding_client import embed_text


# Default knowledge base directory
DEFAULT_KB_PATH = Path("knowledge_base")


def get_kb_path() -> Path:
    """Get the knowledge base directory path from env or default."""
    kb_path = Path(os.environ.get("KNOWLEDGE_BASE_PATH", DEFAULT_KB_PATH))
    kb_path.mkdir(parents=True, exist_ok=True)
    return kb_path


@tool
def write_experience(
    title: str,
    content: str,
    experience_type: str,
    tags: Optional[List[str]] = None,
    related_strategy: Optional[str] = None,
) -> str:
    """
    Write a lesson learned or successful experience to the knowledge base.
    
    Use this tool when you observe:
    - A strategy that failed for a noteworthy reason (lesson learned)
    - A strategy that succeeded and the insight is worth preserving
    - A pattern that emerged across multiple strategies
    - An important realization during evaluation
    
    Args:
        title: Short descriptive title for this experience
        content: Detailed description of the lesson/experience
        experience_type: One of "lesson_learned", "success_pattern", "failure_pattern", "insight"
        tags: Optional list of tags for categorization (e.g., ["logic_error", "assumption_flaw"])
        related_strategy: Optional name of the strategy this relates to
        
    Returns:
        Confirmation message with the file path
    """
    kb_path = get_kb_path()
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = str(uuid.uuid4())[:8]
    safe_title = "".join(c if c.isalnum() or c in "_ -" else "_" for c in title)[:50]
    filename = f"{timestamp}_{experience_type}_{safe_title}_{short_id}.json"
    
    # Build experience record
    experience = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "type": experience_type,
        "tags": tags or [],
        "related_strategy": related_strategy,
        "created_at": datetime.now().isoformat(),
        "metadata": {
            "source": "judge_agent",
            "version": "1.0"
        }
    }

    # Generate embedding
    embedding_text = f"{title}\n{content}\nTags: {', '.join(tags or [])}"
    embedding = embed_text(embedding_text)
    if embedding:
        experience["embedding"] = embedding
    
    # Write to file
    file_path = kb_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(experience, f, ensure_ascii=False, indent=2)
    
    return f"Experience saved: {file_path.name}"


@tool
def search_experiences(
    query: str,
    experience_type: Optional[str] = None,
    limit: int = 5,
) -> str:
    """
    Search the knowledge base for relevant past experiences.
    
    Use this tool to retrieve lessons learned or success patterns that might
    be relevant to the current problem or strategy evaluation.
    
    Args:
        query: Search query describing what you're looking for
        experience_type: Optional filter by type ("lesson_learned", "success_pattern", etc.)
        limit: Maximum number of results to return
        
    Returns:
        JSON string of matching experiences
    """
    kb_path = get_kb_path()
    
    if not kb_path.exists():
        return "Knowledge base is empty."
    
    experiences = []
    
    # Generate query embedding
    query_embedding = embed_text(query)
    use_vector_search = bool(query_embedding)

    # Load all experience files
    for file_path in kb_path.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                exp = json.load(f)
                
                # Filter by type if specified
                if experience_type and exp.get("type") != experience_type:
                    continue

                similarity_score = 0.0
                match_found = False

                if use_vector_search:
                    # Check for existing embedding or generate one (lazy migration)
                    if "embedding" not in exp or not exp["embedding"]:
                        embedding_text = f"{exp.get('title', '')}\n{exp.get('content', '')}\nTags: {', '.join(exp.get('tags', []))}"
                        exp_embedding = embed_text(embedding_text)
                        if exp_embedding:
                            exp["embedding"] = exp_embedding
                            # Save back to file
                            with open(file_path, "w", encoding="utf-8") as f_out:
                                json.dump(exp, f_out, ensure_ascii=False, indent=2)

                    if "embedding" in exp and exp["embedding"]:
                        # Calculate cosine similarity
                        vec_a = np.array(query_embedding)
                        vec_b = np.array(exp["embedding"])
                        norm_a = np.linalg.norm(vec_a)
                        norm_b = np.linalg.norm(vec_b)

                        if norm_a > 0 and norm_b > 0:
                            similarity_score = np.dot(vec_a, vec_b) / (norm_a * norm_b)
                            if similarity_score > 0.3:  # Threshold for relevance
                                match_found = True
                else:
                    # Fallback to simple text matching
                    query_lower = query.lower()
                    title_match = query_lower in exp.get("title", "").lower()
                    content_match = query_lower in exp.get("content", "").lower()
                    tag_match = any(query_lower in tag.lower() for tag in exp.get("tags", []))
                    if title_match or content_match or tag_match:
                        match_found = True
                        similarity_score = 1.0 # arbitrary score for exact matches

                if match_found:
                    experiences.append({
                        "title": exp.get("title"),
                        "type": exp.get("type"),
                        "content": exp.get("content")[:200] + "..." if len(exp.get("content", "")) > 200 else exp.get("content"),
                        "tags": exp.get("tags"),
                        "created_at": exp.get("created_at"),
                        "score": float(similarity_score)
                    })
        except Exception as e:
            print(f"[KB] Warning: Error loading {file_path.name}: {e}")
            continue
    
    # Sort by similarity score (descending)
    experiences.sort(key=lambda x: x.get("score", 0), reverse=True)
    experiences = experiences[:limit]
    
    if not experiences:
        return "No matching experiences found."
    
    # Remove score before returning to keep output clean, or keep it?
    # The original implementation didn't return metadata, but returning score might be useful.
    # I'll keep it simple and match the return format mostly, maybe adding score is fine.
    # The type definition says it returns JSON string.

    return json.dumps(experiences, ensure_ascii=False, indent=2)


def get_all_experiences_for_embedding() -> List[Dict[str, Any]]:
    """
    Load all experiences from knowledge base for vectorization.
    
    Returns:
        List of experience dictionaries
    """
    kb_path = get_kb_path()
    experiences = []
    
    if not kb_path.exists():
        return experiences
    
    for file_path in kb_path.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                exp = json.load(f)
                experiences.append(exp)
        except Exception as e:
            print(f"[KB] Warning: Error loading experience {file_path.name}: {e}")
            continue
    
    return experiences


def format_experiences_for_context(experiences: List[Dict[str, Any]]) -> str:
    """
    Format experiences list into a string for LLM context injection.
    """
    if not experiences:
        return ""
    
    lines = ["## 历史经验参考 (来自知识库)\n"]
    
    for i, exp in enumerate(experiences, 1):
        exp_type = exp.get("type", "unknown")
        type_label = {
            "lesson_learned": "🔴 教训",
            "success_pattern": "🟢 成功模式",
            "failure_pattern": "🔴 失败模式",
            "insight": "💡 洞见"
        }.get(exp_type, exp_type)
        
        lines.append(f"### {i}. [{type_label}] {exp.get('title', 'Untitled')}")
        lines.append(exp.get("content", "")[:500])
        if exp.get("tags"):
            lines.append(f"标签: {', '.join(exp['tags'])}")
        lines.append("")
    
    return "\n".join(lines)
