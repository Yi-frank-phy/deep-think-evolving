"""
Test Agent Flow - 真实API调用测试 (无Mock版本)

使用真实的 Gemini API 和 ModelScope Embedding API 进行测试。
需要配置以下环境变量:
- GEMINI_API_KEY: Gemini API 密钥
- MODELSCOPE_API_KEY: ModelScope API 密钥

运行命令:
    pytest tests/test_agent_flow_live.py -v
"""

import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

import pytest

# 检查必要的API密钥是否配置
def _check_api_keys():
    """检查必要的API密钥是否配置"""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    modelscope_key = os.environ.get("MODELSCOPE_API_KEY")
    
    if not gemini_key:
        pytest.skip("GEMINI_API_KEY not set - skipping live API tests")
    if not modelscope_key:
        pytest.skip("MODELSCOPE_API_KEY not set - skipping live API tests")


# ============================================================================
# Live API Tests for Individual Agents
# ============================================================================

class TestTaskDecomposerLive:
    """使用真实API测试TaskDecomposer代理"""
    
    def test_task_decomposer_live(self):
        """TaskDecomposer应该通过真实API返回子任务和信息需求"""
        _check_api_keys()
        
        from src.agents.task_decomposer import task_decomposer_node
        
        state = {
            "problem_state": "如何设计一个高效的分布式缓存系统？",
            "history": []
        }
        
        result = task_decomposer_node(state)
        
        # 验证返回的子任务
        assert "subtasks" in result
        assert len(result["subtasks"]) > 0
        print(f"\n[TaskDecomposer] 分解出 {len(result['subtasks'])} 个子任务:")
        for i, task in enumerate(result["subtasks"], 1):
            print(f"  {i}. {task}")
        
        # 验证信息需求
        assert "information_needs" in result
        assert len(result["information_needs"]) > 0
        print(f"\n[TaskDecomposer] 识别出 {len(result['information_needs'])} 个信息需求")
        
        # 验证历史记录
        assert len(result["history"]) > 0


class TestResearcherLive:
    """使用真实API测试Researcher代理"""
    
    def test_researcher_live(self):
        """Researcher应该通过Google Grounding收集信息"""
        _check_api_keys()
        
        from src.agents.researcher import research_node
        
        state = {
            "problem_state": "分布式缓存系统设计",
            "information_needs": [
                {"topic": "Redis集群架构", "type": "factual", "priority": 5},
                {"topic": "缓存一致性策略", "type": "conceptual", "priority": 4}
            ],
            "config": {"max_research_iterations": 3},
            "history": []
        }
        
        result = research_node(state)
        
        assert "research_context" in result
        assert result["research_context"] is not None
        assert len(result["research_context"]) > 100  # 应该有实质性内容
        
        print(f"\n[Researcher] 收集到 {len(result['research_context'])} 字符的研究背景")
        print(f"[Researcher] 状态: {result['research_status']}")
        print(f"[Researcher] 迭代次数: {result['research_iteration']}")


class TestStrategyGeneratorLive:
    """使用真实API测试StrategyGenerator代理"""
    
    def test_strategy_generator_live(self):
        """StrategyGenerator应该生成多个策略"""
        _check_api_keys()
        
        from src.agents.strategy_generator import strategy_generator_node
        
        state = {
            "problem_state": "设计高效的分布式缓存系统",
            "research_context": "Redis是流行的分布式缓存解决方案，支持主从复制和集群模式。Memcached提供简单的键值存储。缓存一致性可通过Write-through、Write-behind等策略实现。",
            "subtasks": ["选择缓存技术", "设计一致性策略", "规划扩展方案"],
            "history": []
        }
        
        result = strategy_generator_node(state)
        
        assert "strategies" in result
        assert len(result["strategies"]) >= 2
        
        print(f"\n[StrategyGenerator] 生成了 {len(result['strategies'])} 个策略:")
        for s in result["strategies"]:
            print(f"  - {s['name']}")
            assert "id" in s
            assert "rationale" in s
            assert s["status"] == "active"


class TestJudgeLive:
    """使用真实API测试Judge代理"""
    
    def test_judge_scores_strategies_live(self):
        """Judge应该为策略评分"""
        _check_api_keys()
        
        from src.agents.judge import judge_node
        
        state = {
            "problem_state": "分布式缓存系统设计",
            "strategies": [
                {
                    "id": "strategy-1",
                    "name": "Redis集群方案",
                    "rationale": "使用Redis Cluster实现自动分片和高可用",
                    "assumption": "业务可以接受最终一致性",
                    "status": "active",
                    "trajectory": []
                },
                {
                    "id": "strategy-2",
                    "name": "Memcached+一致性哈希",
                    "rationale": "简单轻量，适合读多写少场景",
                    "assumption": "不需要复杂数据结构",
                    "status": "active",
                    "trajectory": []
                }
            ],
            "judge_context": "评估分布式缓存策略的可行性和效率",
            "history": [],
            "config": {}
        }
        
        result = judge_node(state)
        
        print("\n[Judge] 策略评分结果:")
        for s in result["strategies"]:
            score = s.get("score", "N/A")
            print(f"  - {s['name']}: {score}")
            assert "score" in s
            assert s["status"] == "active"  # 无硬删除


class TestEvolutionLive:
    """使用真实嵌入API测试Evolution代理"""
    
    def test_evolution_embeds_and_calculates_live(self):
        """Evolution应该嵌入策略并计算KDE/UCB"""
        _check_api_keys()
        
        from src.agents.evolution import evolution_node
        
        state = {
            "problem_state": "分布式缓存系统设计",
            "strategies": [
                {
                    "id": "strategy-1",
                    "name": "Redis集群方案",
                    "rationale": "使用Redis Cluster实现自动分片和高可用",
                    "assumption": "业务可以接受最终一致性",
                    "milestones": [],
                    "embedding": None,  # 需要嵌入
                    "density": None,
                    "log_density": None,
                    "score": 0.8,
                    "status": "active",
                    "trajectory": [],
                    "parent_id": None
                },
                {
                    "id": "strategy-2",
                    "name": "Memcached方案",
                    "rationale": "简单轻量的缓存层",
                    "assumption": "不需要复杂数据结构",
                    "milestones": [],
                    "embedding": None,
                    "density": None,
                    "log_density": None,
                    "score": 0.6,
                    "status": "active",
                    "trajectory": [],
                    "parent_id": None
                }
            ],
            "spatial_entropy": 0.0,
            "effective_temperature": 0.0,
            "normalized_temperature": 0.0,
            "config": {
                "t_max": 2.0,
                "c_explore": 1.0,
                "total_child_budget": 6
            },
            "virtual_filesystem": {},
            "history": [],
            "iteration_count": 0
        }
        
        result = evolution_node(state)
        
        print("\n[Evolution] 进化结果:")
        print(f"  空间熵: {result['spatial_entropy']:.4f}")
        print(f"  有效温度: {result['effective_temperature']:.4f}")
        print(f"  迭代次数: {result['iteration_count']}")
        
        for s in result["strategies"]:
            if s.get("embedding"):
                print(f"  - {s['name']}: 嵌入维度={len(s['embedding'])}, quota={s.get('child_quota', 'N/A')}")
                assert len(s["embedding"]) > 0
                assert "child_quota" in s


# ============================================================================
# End-to-End Test with Real APIs
# ============================================================================

@pytest.mark.asyncio
async def test_full_pipeline_live():
    """
    真实API端到端测试
    
    使用真实的Gemini和ModelScope API运行完整流程。
    """
    _check_api_keys()
    
    from src.core.graph_builder import build_deep_think_graph
    from src.core.state import DeepThinkState
    
    app = build_deep_think_graph()
    
    initial_state: DeepThinkState = {
        "problem_state": "如何设计一个支持百万级QPS的分布式缓存系统？",
        "strategies": [],
        "research_context": None,
        "research_status": None,
        "research_iteration": 0,
        "subtasks": None,
        "information_needs": None,
        "spatial_entropy": 1.0,
        "effective_temperature": 1.0,
        "normalized_temperature": 0.5,
        "config": {
            "t_max": 2.0,
            "c_explore": 1.0,
            "beam_width": 3,
            "max_iterations": 1,  # 限制迭代次数以控制API调用
            "max_research_iterations": 1,
            "total_child_budget": 6
        },
        "virtual_filesystem": {},
        "history": [],
        "iteration_count": 0,
        "judge_context": None,
        "architect_decisions": None
    }
    
    print("\n" + "="*60)
    print("[LIVE TEST] 开始真实API端到端测试")
    print("="*60)
    
    final_state = await app.ainvoke(initial_state)
    
    # 验证结果
    print("\n[结果验证]")
    
    assert final_state.get("subtasks") is not None
    print(f"  ✓ 子任务: {len(final_state['subtasks'])} 个")
    
    assert final_state.get("research_context") is not None
    print(f"  ✓ 研究背景: {len(final_state['research_context'])} 字符")
    
    assert len(final_state["strategies"]) >= 2
    print(f"  ✓ 策略: {len(final_state['strategies'])} 个")
    
    for s in final_state["strategies"]:
        assert s.get("name")
        assert "score" in s
        print(f"    - {s['name']}: score={s.get('score', 'N/A')}")
    
    history = final_state.get("history", [])
    print(f"  ✓ 历史记录: {len(history)} 条")
    
    print("\n" + "="*60)
    print("[LIVE TEST] 真实API测试通过 ✓")
    print("="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
