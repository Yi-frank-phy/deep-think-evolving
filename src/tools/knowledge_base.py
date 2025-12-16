"""
Knowledge Base Tools for Outer Loop Memory System.

设计原则 (2024-12-14 重构):
1. Agent 自主决定写入 - 只有 LLM 真正认为有价值时才调用 write 工具
2. 只有两种保存场景:
   - 硬剪枝时保存有价值的分支信息 (write_strategy_archive)
   - 全局保存 LLM 认为值得学习的抽象经验 (write_experience)
3. 召回阈值基于向量空间距离 ε (bandwidth):
   - 距离 > 1ε: 不应召回 (超出一个标准差)
   - 只召回 distance < ε 的高度相关经验

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
from src.math_engine.kde import estimate_bandwidth


# Default knowledge base directory
DEFAULT_KB_PATH = Path("knowledge_base")


def get_kb_path() -> Path:
    """Get the knowledge base directory path from env or default."""
    kb_path = Path(os.environ.get("KNOWLEDGE_BASE_PATH", DEFAULT_KB_PATH))
    kb_path.mkdir(parents=True, exist_ok=True)
    return kb_path


def calculate_vector_distance(vec_a: List[float], vec_b: List[float]) -> float:
    """计算两个向量之间的欧几里得距离。"""
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    return float(np.linalg.norm(a - b))


def get_current_epsilon(embeddings: List[List[float]]) -> float:
    """
    基于当前嵌入集合估计 ε (带宽)。
    
    ε 代表向量空间中的"一个标准差"距离。
    如果没有足够的嵌入数据，返回默认值。
    """
    if len(embeddings) < 2:
        return 1.0  # 默认值
    
    embeddings_array = np.array(embeddings, dtype=float)
    return estimate_bandwidth(embeddings_array)


@tool
def write_experience(
    title: str,
    content: str,
    experience_type: str,
    tags: Optional[List[str]] = None,
    related_strategy: Optional[str] = None,
) -> str:
    """
    将真正有价值的经验写入知识库。
    
    ⚠️ 重要: 只有当你确信这是一个值得长期保存的普遍性经验时才调用此工具。
    不要为每个策略评估都调用此工具。
    
    适合保存的经验类型:
    - 可泛化的抽象教训 (不是具体问题的具体答案)
    - 分支决策的元策略 (如何决定何时探索 vs 利用)
    - 反复出现的失败模式 (可在未来问题中避免)
    
    Args:
        title: 简短的描述性标题
        content: 抽象化的经验描述 (避免包含具体问题细节)
        experience_type: "lesson_learned", "success_pattern", "branching_heuristic", "meta_insight"
        tags: 可选的标签列表
        related_strategy: 可选的相关策略名称
        
    Returns:
        确认消息
    """
    kb_path = get_kb_path()
    
    # 验证 experience_type
    valid_types = {"lesson_learned", "success_pattern", "branching_heuristic", "meta_insight"}
    if experience_type not in valid_types:
        return f"Error: experience_type must be one of {valid_types}"
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = str(uuid.uuid4())[:8]
    safe_title = "".join(c if c.isalnum() or c in "_ -" else "_" for c in title)[:50]
    filename = f"{timestamp}_{experience_type}_{safe_title}_{short_id}.json"
    
    # Build experience record (轻量化 - 不存储完整嵌入)
    experience = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "type": experience_type,
        "tags": tags or [],
        "related_strategy": related_strategy,
        "created_at": datetime.now().isoformat(),
        "metadata": {
            "source": "agent_autonomous_decision",
            "version": "2.0"
        }
    }

    # Generate embedding (用于语义搜索)
    embedding_text = f"{title}\n{content}"
    embedding = embed_text(embedding_text)
    if embedding:
        experience["embedding"] = embedding
    
    # Write to file
    file_path = kb_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(experience, f, ensure_ascii=False, indent=2)
    
    print(f"[KB] Experience saved: {file_path.name}")
    return f"Experience saved: {file_path.name}"


def write_strategy_archive(
    strategy: Dict[str, Any],
    synthesis_context: str,
    branch_rationale: str,
    report_version: int
) -> str:
    """
    在硬剪枝时归档有价值的策略信息。
    
    这是硬剪枝流程的一部分，不是由 Agent 自主调用的工具。
    只保存分支决策逻辑和抽象经验，不保存完整的策略内容。
    
    Args:
        strategy: 被剪枝的策略节点
        synthesis_context: 综合上下文 (为什么这个策略被综合)
        branch_rationale: 分支决策理由 (为什么选择了这个方向)
        report_version: 报告版本号
        
    Returns:
        确认消息
    """
    kb_path = get_kb_path()
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = str(uuid.uuid4())[:8]
    safe_name = "".join(c if c.isalnum() or c in "_ -" else "_" for c in strategy.get("name", "unknown"))[:30]
    filename = f"{timestamp}_branch_archive_{safe_name}_{short_id}.json"
    
    # 只保存分支决策的抽象经验，而非具体策略内容
    archive = {
        "id": str(uuid.uuid4()),
        "type": "branch_archive",
        "title": f"分支决策: {strategy.get('name', 'Unknown')}",
        "content": json.dumps({
            "strategy_name": strategy.get("name"),
            "branch_rationale": branch_rationale,  # 关键: 为什么选择这个方向
            "final_score": strategy.get("score", 0),
            "synthesis_context": synthesis_context[:500],  # 截断以保持轻量
            "report_version": report_version
        }, ensure_ascii=False),
        "tags": ["branch_decision", f"report_v{report_version}"],
        "created_at": datetime.now().isoformat(),
        "metadata": {
            "source": "hard_pruning",
            "version": "2.0",
            "original_strategy_id": strategy.get("id")
        }
    }
    
    # 只为分支决策理由生成嵌入 (更轻量)
    embedding_text = f"分支决策: {branch_rationale}"
    embedding = embed_text(embedding_text)
    if embedding:
        archive["embedding"] = embedding
    
    # Write to file
    file_path = kb_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)
    
    print(f"[KB] Branch archived: {strategy.get('name')} -> {file_path.name}")
    return f"Branch archived: {file_path.name}"


def _search_experiences_impl(
    query: str,
    query_embedding: Optional[List[float]] = None,
    current_embeddings: Optional[List[List[float]]] = None,
    experience_type: Optional[str] = None,
    limit: int = 3,
    epsilon_threshold: float = 1.0,  # 距离阈值: 1ε = 一个标准差
) -> List[Dict[str, Any]]:
    """
    基于向量距离搜索知识库中的相关经验 (内部实现)。
    
    ⚠️ 只召回距离 < epsilon_threshold * ε 的高度相关经验。
    这确保了上下文的纯净性，避免召回不相关的腐烂上下文。
    
    Args:
        query: 搜索查询文本
        query_embedding: 可选的预计算查询嵌入
        current_embeddings: 当前策略空间的嵌入 (用于计算 ε)
        experience_type: 可选的类型过滤
        limit: 最大返回数量
        epsilon_threshold: 距离阈值倍数 (1.0 = 1ε, 0.25 = 1/4ε)
        
    Returns:
        匹配的经验列表 (只返回高度相关的)
    """
    kb_path = get_kb_path()
    
    if not kb_path.exists():
        return []
    
    # 计算查询嵌入
    if query_embedding is None:
        query_embedding = embed_text(query)
    
    if not query_embedding:
        print("[KB] Warning: Could not generate query embedding")
        return []
    
    # 计算当前空间的 ε (如果有嵌入数据)
    if current_embeddings and len(current_embeddings) >= 2:
        epsilon = get_current_epsilon(current_embeddings)
    else:
        # 使用默认 ε (基于高维空间的典型距离)
        epsilon = 10.0  # 高维空间的保守默认值
    
    distance_threshold = epsilon_threshold * epsilon
    print(f"[KB] Searching with ε={epsilon:.4f}, threshold={distance_threshold:.4f}")
    
    experiences = []
    
    # Load all experience files
    for file_path in kb_path.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                exp = json.load(f)
                
                # Filter by type if specified
                if experience_type and exp.get("type") != experience_type:
                    continue
                
                exp_embedding = exp.get("embedding")
                if not exp_embedding:
                    continue  # 跳过没有嵌入的经验
                
                # 计算向量距离
                distance = calculate_vector_distance(query_embedding, exp_embedding)
                
                # 只保留距离 < 阈值的经验
                if distance < distance_threshold:
                    experiences.append({
                        "title": exp.get("title"),
                        "type": exp.get("type"),
                        "content": exp.get("content")[:300] if exp.get("content") else "",
                        "tags": exp.get("tags"),
                        "distance": distance,
                        "score": 1.0 - (distance / distance_threshold),  # 归一化相关性 (兼容测试)
                        "relevance": 1.0 - (distance / distance_threshold)  # 归一化相关性
                    })
                    
        except Exception as e:
            print(f"[KB] Warning: Error loading {file_path.name}: {e}")
            continue
    
    # 按距离排序 (最近的优先)
    experiences.sort(key=lambda x: x.get("distance", float("inf")))
    experiences = experiences[:limit]
    
    if experiences:
        print(f"[KB] Found {len(experiences)} relevant experiences (closest distance: {experiences[0]['distance']:.4f})")
    else:
        print(f"[KB] No experiences within distance threshold ({distance_threshold:.4f})")
    
    return experiences


@tool
def search_experiences(
    query: str,
    experience_type: Optional[str] = None,
    limit: int = 3,
) -> str:
    """
    基于向量距离搜索知识库中的相关经验。
    
    Args:
        query: 搜索查询文本
        experience_type: 可选的类型过滤 ("lesson_learned", "success_pattern", 等)
        limit: 最大返回数量
        
    Returns:
        JSON 格式的经验列表，或 "No matching experiences found."
    """
    results = _search_experiences_impl(
        query=query,
        experience_type=experience_type,
        limit=limit
    )
    
    if not results:
        return "No matching experiences found."
    
    return json.dumps(results, ensure_ascii=False, indent=2)


def format_experiences_for_context(experiences: List[Dict[str, Any]]) -> str:
    """
    Format experiences list into a string for LLM context injection.
    
    只用于高度相关的经验。
    """
    if not experiences:
        return ""
    
    lines = ["## 相关历史经验 (高度相关)\n"]
    
    for i, exp in enumerate(experiences, 1):
        exp_type = exp.get("type", "unknown")
        type_label = {
            "lesson_learned": "🔴 教训",
            "success_pattern": "🟢 成功模式",
            "branching_heuristic": "🔀 分支启发",
            "meta_insight": "💡 元洞见",
            "branch_archive": "📦 分支归档"
        }.get(exp_type, exp_type)
        
        relevance = exp.get("relevance", 0)
        lines.append(f"### {i}. [{type_label}] {exp.get('title', 'Untitled')} (相关度: {relevance:.1%})")
        lines.append(exp.get("content", "")[:300])
        lines.append("")
    
    return "\n".join(lines)
