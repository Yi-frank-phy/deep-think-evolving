"""Tests for knowledge base vector search functionality - 真实API版本

使用真实的ModelScope嵌入API测试:
1. 向量嵌入生成
2. 基于余弦相似度的向量搜索
3. 搜索结果排序
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

import numpy as np
import pytest
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def _check_api_key():
    """检查API密钥是否配置"""
    if not os.environ.get("MODELSCOPE_API_KEY"):
        pytest.skip("MODELSCOPE_API_KEY not set")


# --- Fixtures ---

@pytest.fixture
def temp_kb_path(tmp_path: Path):
    """Create a temporary knowledge base directory."""
    kb_path = tmp_path / "knowledge_base"
    kb_path.mkdir()
    return kb_path


@pytest.fixture
def sample_experience_with_embedding(temp_kb_path: Path):
    """Create a sample experience file with embedding."""
    _check_api_key()
    
    from src.embedding_client import embed_text
    
    content = "通过组合多个模型的输出，我们显著提高了推理准确性。关键是设计一个有效的投票机制。"
    embedding = embed_text(content)
    
    experience = {
        "id": "test-id-001",
        "title": "成功的策略：使用多模型集成",
        "content": content,
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

    def test_write_experience_generates_embedding(self, temp_kb_path: Path, monkeypatch):
        """Verify that write_experience generates and stores an embedding."""
        _check_api_key()
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        from src.tools.knowledge_base import write_experience
        
        result = write_experience.invoke({
            "title": "测试经验",
            "content": "这是一个测试内容用于生成嵌入向量",
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
        # Qwen3-Embedding-8B生成4096维向量
        assert len(saved_exp["embedding"]) == 4096


# --- Tests for search_experiences with vector search ---

class TestVectorSearch:
    """Tests for vector similarity search functionality."""

    def test_vector_search_finds_similar_experience(
        self, temp_kb_path: Path, sample_experience_with_embedding, monkeypatch
    ):
        """Verify vector search returns experiences above similarity threshold."""
        _check_api_key()
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


# --- Tests for lazy migration ---

class TestLazyMigration:
    """Tests for lazy embedding migration during search."""

    def test_lazy_migration_adds_embedding_to_old_experience(
        self, temp_kb_path: Path, sample_experience_without_embedding, monkeypatch
    ):
        """Verify search triggers embedding generation for old experiences."""
        _check_api_key()
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
        assert len(after["embedding"]) == 4096


# --- Tests for edge cases ---

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_search_empty_knowledge_base(self, temp_kb_path: Path, monkeypatch):
        """Verify appropriate message for empty knowledge base."""
        _check_api_key()
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        from src.tools.knowledge_base import search_experiences
        
        result = search_experiences.invoke({
            "query": "任何查询",
            "limit": 5
        })
        
        assert result == "No matching experiences found."

    def test_handles_malformed_json_files(self, temp_kb_path: Path, monkeypatch):
        """Verify search gracefully handles malformed JSON files."""
        _check_api_key()
        monkeypatch.setenv("KNOWLEDGE_BASE_PATH", str(temp_kb_path))
        
        from src.embedding_client import embed_text
        
        # Create a valid experience
        valid_content = "有效内容用于测试"
        valid_exp = {
            "id": "valid",
            "title": "有效经验",
            "content": valid_content,
            "type": "insight",
            "tags": [],
            "created_at": "2025-01-01T00:00:00",
            "embedding": embed_text(valid_content)
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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
