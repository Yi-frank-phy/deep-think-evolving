"""
Test Embedding Client - 真实API测试 (无Mock版本)

测试ModelScope Qwen3-Embedding-8B嵌入服务的真实调用。
"""

import os
import pytest
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src import embedding_client as ec


def _check_api_key():
    """检查API密钥是否配置"""
    if not os.environ.get("MODELSCOPE_API_KEY"):
        pytest.skip("MODELSCOPE_API_KEY not set")


class TestEmbedTextLive:
    """使用真实API测试embed_text函数"""
    
    def test_embed_text_returns_vector(self):
        """embed_text应该返回有效的嵌入向量"""
        _check_api_key()
        
        vector = ec.embed_text("这是一个测试文本用于生成嵌入向量")
        
        # 应该返回非空向量
        assert vector is not None
        assert len(vector) > 0
        
        # Qwen3-Embedding-8B 应该是 4096 维
        assert len(vector) == 4096
        
        print(f"[embed_text] 成功返回 {len(vector)} 维向量")
    
    def test_embed_text_empty_string_returns_empty(self):
        """空字符串应该返回空列表"""
        result = ec.embed_text("")
        assert result == []
    
    def test_embed_text_whitespace_only_returns_empty(self):
        """纯空格应该返回空列表"""
        result = ec.embed_text("   ")
        assert result == []


class TestEmbedStrategiesLive:
    """使用真实API测试embed_strategies函数"""
    
    def test_embed_strategies_success(self):
        """embed_strategies应该为策略生成嵌入"""
        _check_api_key()
        
        strategies = [
            {
                "strategy_name": "Redis集群方案",
                "rationale": "使用Redis Cluster实现分布式缓存",
                "initial_assumption": "业务可接受最终一致性"
            },
            {
                "strategy_name": "Memcached方案",
                "rationale": "简单高效的键值缓存",
                "initial_assumption": "不需要复杂数据结构"
            }
        ]
        
        result = ec.embed_strategies(strategies)
        
        # 应该返回相同数量的策略
        assert len(result) == 2
        
        # 每个策略应该有嵌入
        for s in result:
            assert "embedding" in s
            assert len(s["embedding"]) > 0
            print(f"  - {s['strategy_name']}: {len(s['embedding'])} 维")
    
    def test_embed_strategies_empty_list(self):
        """空列表应该返回空列表"""
        result = ec.embed_strategies([])
        assert result == []


class TestEmbeddingDimension:
    """测试嵌入维度配置"""
    
    def test_embedding_dimension_is_4096(self):
        """确认配置的嵌入维度是4096"""
        assert ec.EMBEDDING_DIMENSION == 4096


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
