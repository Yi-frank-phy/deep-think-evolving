"""Tests for knowledge base vector search functionality.

This module tests:
1. Vector embedding generation during experience writing
2. Cosine similarity-based vector search
3. Lazy migration for experiences without embeddings
4. Fallback to text matching when embedding fails
5. Search result sorting by similarity score
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

import numpy as np
import pytest


# --- Fixtures ---

@pytest.fixture
def temp_kb_path(tmp_path: Path):
    """Create a temporary knowledge base directory."""
    kb_path = tmp_path / "knowledge_base"
    kb_path.mkdir()
    return kb_path


@pytest.fixture
def mock_embed_text():
    """Mock embed_text to return deterministic embeddings."""
    def _embed(text: str) -> List[float]:
        # Generate a deterministic embedding based on text hash
        np.random.seed(hash(text) % (2**32))
        return np.random.rand(768).tolist()
    
    with patch("src.tools.knowledge_base.embed_text", side_effect=_embed) as mock:
        yield mock


@pytest.fixture
def mock_embed_text_failure():
    """Mock embed_text to simulate embedding failure."""
    with patch("src.tools.knowledge_base.embed_text", return_value=[]) as mock:
        yield mock


@pytest.fixture
def sample_experience_with_embedding(temp_kb_path: Path):
    """Create a sample experience file with embedding."""
    np.random.seed(42)
    embedding = np.random.rand(768).tolist()
    
    experience = {
        "id": "test-id-001",
        "title": "成功的策略：使用多模型集成",
        "content": "通过组合多个模型的输出，我们显著提高了推理准确性。关键是设计一个有效的投票机制。",
        "type": "success_pattern",
        "tags": ["多模型", "集成学习", "投票机制"],
        "created_at": "2025-01-01T00:00:00",
        "embedding": embedding
    }
    
    file_path = temp_kb_path / "20250101_success_pattern_test_001.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(experience, f, ensure_ascii=False, indent=2)
    
    return file_path, experience, embedding


@pytest.fixture
def sample_experience_without_embedding(temp_kb_path: Path):
    """Create a sample experience file without embedding (for migration test)."""
    experience = {
        "id": "test-id-002",
        "title": "失败教训：过度依赖单一信源",
        "content": "当仅依赖一个数据源时，系统容易受到该源偏见的影响。应该始终交叉验证。",
        "type": "lesson_learned",
        "tags": ["数据偏见", "交叉验证"],
        "created_at": "2025-01-02T00:00:00"
        # No embedding field
    }
    
    file_path = temp_kb_path / "20250102_lesson_learned_test_002.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(experience, f, ensure_ascii=False, indent=2)
    
    return file_path, experience


# --- Tests for write_experience ---

class TestWriteExperienceWithEmbedding:
    """Tests for embedding generation during experience writing."""

    def test_write_experience_generates_embedding(
        self, temp_kb_path: Path, mock_embed_text, monkeypatch
    ):
        """Verify that write_experience generates and stores an embedding."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        from src.tools.knowledge_base import write_experience
        
        result = write_experience.invoke({
            "title": "测试经验",
            "content": "这是一个测试内容",
            "experience_type": "insight",
            "tags": ["测试", "单元测试"]
        })
        
        assert "Experience saved:" in result
        
        # Find the created file
        files = list(temp_kb_path.glob("*.json"))
        assert len(files) == 1
        
        with open(files[0], "r", encoding="utf-8") as f:
            saved_exp = json.load(f)
        
        assert "embedding" in saved_exp
        assert isinstance(saved_exp["embedding"], list)
        assert len(saved_exp["embedding"]) == 768
        mock_embed_text.assert_called_once()

    def test_write_experience_without_embedding_on_failure(
        self, temp_kb_path: Path, mock_embed_text_failure, monkeypatch
    ):
        """Verify experience is saved even if embedding fails."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        from src.tools.knowledge_base import write_experience
        
        result = write_experience.invoke({
            "title": "测试经验",
            "content": "这是一个测试内容",
            "experience_type": "lesson_learned"
        })
        
        assert "Experience saved:" in result
        
        files = list(temp_kb_path.glob("*.json"))
        assert len(files) == 1
        
        with open(files[0], "r", encoding="utf-8") as f:
            saved_exp = json.load(f)
        
        # Embedding should not be present when embed_text returns empty
        assert "embedding" not in saved_exp


# --- Tests for search_experiences with vector search ---

class TestVectorSearch:
    """Tests for vector similarity search functionality."""

    def test_vector_search_finds_similar_experience(
        self, temp_kb_path: Path, sample_experience_with_embedding, mock_embed_text, monkeypatch
    ):
        """Verify vector search returns experiences above similarity threshold."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        from src.tools.knowledge_base import search_experiences
        
        # Create a query that should match
        result = search_experiences.invoke({
            "query": "多模型集成策略",
            "limit": 5
        })
        
        assert result != "No matching experiences found."
        experiences = json.loads(result)
        assert len(experiences) >= 1
        assert "score" in experiences[0]
        assert experiences[0]["score"] > 0

    def test_vector_search_returns_sorted_by_score(
        self, temp_kb_path: Path, mock_embed_text, monkeypatch
    ):
        """Verify results are sorted by similarity score descending."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        # Create multiple experiences with different embeddings
        for i in range(3):
            np.random.seed(i * 100)
            exp = {
                "id": f"test-{i}",
                "title": f"经验 {i}",
                "content": f"内容 {i}",
                "type": "insight",
                "tags": [],
                "created_at": f"2025-01-0{i+1}T00:00:00",
                "embedding": np.random.rand(768).tolist()
            }
            file_path = temp_kb_path / f"exp_{i}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(exp, f)
        
        from src.tools.knowledge_base import search_experiences
        
        result = search_experiences.invoke({
            "query": "测试查询",
            "limit": 10
        })
        
        if result != "No matching experiences found.":
            experiences = json.loads(result)
            scores = [e["score"] for e in experiences]
            assert scores == sorted(scores, reverse=True), "Results should be sorted by score descending"

    def test_vector_search_respects_type_filter(
        self, temp_kb_path: Path, mock_embed_text, monkeypatch
    ):
        """Verify type filter is applied during vector search."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        # Create experiences of different types
        for exp_type in ["success_pattern", "lesson_learned", "insight"]:
            np.random.seed(hash(exp_type) % (2**32))
            exp = {
                "id": f"test-{exp_type}",
                "title": f"经验: {exp_type}",
                "content": "测试内容",
                "type": exp_type,
                "tags": [],
                "created_at": "2025-01-01T00:00:00",
                "embedding": np.random.rand(768).tolist()
            }
            file_path = temp_kb_path / f"{exp_type}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(exp, f)
        
        from src.tools.knowledge_base import search_experiences
        
        result = search_experiences.invoke({
            "query": "测试",
            "experience_type": "success_pattern",
            "limit": 10
        })
        
        if result != "No matching experiences found.":
            experiences = json.loads(result)
            for exp in experiences:
                assert exp["type"] == "success_pattern"


# --- Tests for lazy migration ---

class TestLazyMigration:
    """Tests for lazy embedding migration during search."""

    def test_lazy_migration_adds_embedding_to_old_experience(
        self, temp_kb_path: Path, sample_experience_without_embedding, mock_embed_text, monkeypatch
    ):
        """Verify search triggers embedding generation for old experiences."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        file_path, original_exp = sample_experience_without_embedding
        
        # Confirm no embedding initially
        with open(file_path, "r", encoding="utf-8") as f:
            before = json.load(f)
        assert "embedding" not in before
        
        from src.tools.knowledge_base import search_experiences
        
        # Trigger search which should perform lazy migration
        search_experiences.invoke({
            "query": "数据偏见",
            "limit": 5
        })
        
        # Check if embedding was added
        with open(file_path, "r", encoding="utf-8") as f:
            after = json.load(f)
        
        assert "embedding" in after
        assert isinstance(after["embedding"], list)
        assert len(after["embedding"]) == 768

    def test_lazy_migration_preserves_original_data(
        self, temp_kb_path: Path, sample_experience_without_embedding, mock_embed_text, monkeypatch
    ):
        """Verify lazy migration doesn't corrupt existing fields."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        file_path, original_exp = sample_experience_without_embedding
        
        from src.tools.knowledge_base import search_experiences
        
        search_experiences.invoke({
            "query": "测试",
            "limit": 5
        })
        
        with open(file_path, "r", encoding="utf-8") as f:
            migrated = json.load(f)
        
        # Verify all original fields are preserved
        assert migrated["id"] == original_exp["id"]
        assert migrated["title"] == original_exp["title"]
        assert migrated["content"] == original_exp["content"]
        assert migrated["type"] == original_exp["type"]
        assert migrated["tags"] == original_exp["tags"]


# --- Tests for fallback text search ---

class TestTextSearchFallback:
    """Tests for fallback text matching when vector search fails."""

    def test_fallback_to_text_search_on_embedding_failure(
        self, temp_kb_path: Path, mock_embed_text_failure, monkeypatch
    ):
        """Verify text matching is used when embedding generation fails."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        # Create experience without embedding
        exp = {
            "id": "test-fallback",
            "title": "关键词测试",
            "content": "这是包含关键词的内容",
            "type": "insight",
            "tags": ["关键词"],
            "created_at": "2025-01-01T00:00:00"
        }
        file_path = temp_kb_path / "fallback_test.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(exp, f, ensure_ascii=False)
        
        from src.tools.knowledge_base import search_experiences
        
        # Search with text that matches title
        result = search_experiences.invoke({
            "query": "关键词",
            "limit": 5
        })
        
        assert result != "No matching experiences found."
        experiences = json.loads(result)
        assert len(experiences) == 1
        assert experiences[0]["title"] == "关键词测试"
        assert experiences[0]["score"] == 1.0  # Text match score

    def test_text_search_matches_in_title(
        self, temp_kb_path: Path, mock_embed_text_failure, monkeypatch
    ):
        """Verify text search matches queries in title."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        exp = {
            "id": "test-title",
            "title": "独特标题词",
            "content": "普通内容",
            "type": "insight",
            "tags": [],
            "created_at": "2025-01-01T00:00:00"
        }
        file_path = temp_kb_path / "title_test.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(exp, f, ensure_ascii=False)
        
        from src.tools.knowledge_base import search_experiences
        
        result = search_experiences.invoke({
            "query": "独特标题词",
            "limit": 5
        })
        
        assert result != "No matching experiences found."

    def test_text_search_matches_in_tags(
        self, temp_kb_path: Path, mock_embed_text_failure, monkeypatch
    ):
        """Verify text search matches queries in tags."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        exp = {
            "id": "test-tag",
            "title": "普通标题",
            "content": "普通内容",
            "type": "insight",
            "tags": ["独特标签词"],
            "created_at": "2025-01-01T00:00:00"
        }
        file_path = temp_kb_path / "tag_test.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(exp, f, ensure_ascii=False)
        
        from src.tools.knowledge_base import search_experiences
        
        result = search_experiences.invoke({
            "query": "独特标签词",
            "limit": 5
        })
        
        assert result != "No matching experiences found."


# --- Tests for edge cases ---

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_search_empty_knowledge_base(
        self, temp_kb_path: Path, mock_embed_text, monkeypatch
    ):
        """Verify appropriate message for empty knowledge base."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        from src.tools.knowledge_base import search_experiences
        
        result = search_experiences.invoke({
            "query": "任何查询",
            "limit": 5
        })
        
        assert result == "No matching experiences found."

    def test_search_respects_limit(
        self, temp_kb_path: Path, mock_embed_text, monkeypatch
    ):
        """Verify search respects the limit parameter."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        # Create 10 experiences
        for i in range(10):
            np.random.seed(i)
            exp = {
                "id": f"test-{i}",
                "title": f"经验 {i}",
                "content": "内容",
                "type": "insight",
                "tags": [],
                "created_at": f"2025-01-{i+1:02d}T00:00:00",
                "embedding": np.random.rand(768).tolist()
            }
            file_path = temp_kb_path / f"exp_{i}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(exp, f)
        
        from src.tools.knowledge_base import search_experiences
        
        result = search_experiences.invoke({
            "query": "经验",
            "limit": 3
        })
        
        if result != "No matching experiences found.":
            experiences = json.loads(result)
            assert len(experiences) <= 3

    def test_content_truncation_in_results(
        self, temp_kb_path: Path, mock_embed_text, monkeypatch
    ):
        """Verify long content is truncated in search results."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        np.random.seed(42)
        long_content = "长内容" * 200  # Create content > 200 chars
        exp = {
            "id": "test-long",
            "title": "长内容测试",
            "content": long_content,
            "type": "insight",
            "tags": [],
            "created_at": "2025-01-01T00:00:00",
            "embedding": np.random.rand(768).tolist()
        }
        file_path = temp_kb_path / "long_content.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(exp, f, ensure_ascii=False)
        
        from src.tools.knowledge_base import search_experiences
        
        result = search_experiences.invoke({
            "query": "长内容",
            "limit": 5
        })
        
        if result != "No matching experiences found.":
            experiences = json.loads(result)
            # Content should be truncated to 200 chars + "..."
            assert len(experiences[0]["content"]) <= 203

    def test_handles_malformed_json_files(
        self, temp_kb_path: Path, mock_embed_text, monkeypatch
    ):
        """Verify search gracefully handles malformed JSON files."""
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        # Create a valid experience
        np.random.seed(42)
        valid_exp = {
            "id": "valid",
            "title": "有效经验",
            "content": "内容",
            "type": "insight",
            "tags": [],
            "created_at": "2025-01-01T00:00:00",
            "embedding": np.random.rand(768).tolist()
        }
        with open(temp_kb_path / "valid.json", "w", encoding="utf-8") as f:
            json.dump(valid_exp, f)
        
        # Create a malformed JSON file
        with open(temp_kb_path / "malformed.json", "w", encoding="utf-8") as f:
            f.write("{invalid json")
        
        from src.tools.knowledge_base import search_experiences
        
        # Should not raise an exception
        result = search_experiences.invoke({
            "query": "有效",
            "limit": 5
        })
        
        # Should still find the valid experience
        if result != "No matching experiences found.":
            experiences = json.loads(result)
            assert any(e["title"] == "有效经验" for e in experiences)
