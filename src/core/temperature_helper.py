"""
LLM Temperature Helper - LLM温度配置辅助模块

设计原则 (Logic Manifold Integrity):
Google DeepMind 建议推理模型 (如 Gemini 3) 保持 temperature=1.0 以维护逻辑流形完整性。
系统的"退火"通过计算资源分配 (Test-time Compute) 实现，而非调整 Softmax 参数。

Architecture:
- LLM 推理温度: 固定 T=1.0
- 系统温度 τ: 仅控制 Sampling Count (N) / Beam Width / 资源分配
"""

from src.core.state import DeepThinkState


def get_llm_temperature(state: DeepThinkState) -> float:
    """
    获取LLM调用时应使用的温度值。
    
    LLM 推理温度始终为 1.0 (Logic Manifold Integrity)。
    
    Note:
        系统温度 τ 控制计算资源分配 (Sampling Count N)，
        而非 LLM 的 Softmax 温度。参见: Thermodynamic Control Mechanism。
    
    Args:
        state: 当前系统状态 (未使用，保留接口兼容性)
        
    Returns:
        LLM temperature value: 始终为 1.0
    """
    # Logic Manifold Integrity: LLM temperature is ALWAYS 1.0
    # System temperature τ controls Compute Budget Allocation only
    return 1.0


def get_temperature_config_defaults() -> dict:
    """
    获取温度配置的默认值。
    
    用于初始化 state["config"]。
    注意: LLM温度固定为1.0，此处仅保留系统温度相关配置。
    """
    return {
        # LLM temperature is always 1.0 (not configurable)
        # System temperature parameters for resource allocation:
        "t_max": 2.0,       # 最大系统温度上限 (用于归一化)
        "c_explore": 1.0,   # UCB 探索系数
    }
