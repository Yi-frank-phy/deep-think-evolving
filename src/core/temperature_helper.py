"""
LLM Temperature Helper - LLM温度配置辅助模块

支持两种模式:
- decoupled: 固定温度 (默认 T=1.0)
- coupled: 温度与系统有效温度耦合
"""

from src.core.state import DeepThinkState


def get_llm_temperature(state: DeepThinkState) -> float:
    """
    获取LLM调用时应使用的温度值。
    
    配置项 (在 state["config"] 中):
    - temperature_coupling_mode: "decoupled" | "coupled"
    - fixed_llm_temperature: 解耦模式下的固定温度 (默认 1.0)
    - max_llm_temperature: 耦合模式下的温度上限 (默认 1.5)
    
    Args:
        state: 当前系统状态
        
    Returns:
        LLM temperature value (0.0 - max_llm_temperature)
    """
    config = state.get("config", {})
    mode = config.get("temperature_coupling_mode", "decoupled")
    
    if mode == "coupled":
        # 耦合模式: 使用系统的归一化温度
        tau = state.get("normalized_temperature", 1.0)
        max_temp = config.get("max_llm_temperature", 1.5)
        return min(tau, max_temp)
    else:
        # 解耦模式: 固定温度
        return config.get("fixed_llm_temperature", 1.0)


def get_temperature_config_defaults() -> dict:
    """
    获取温度配置的默认值。
    
    用于初始化 state["config"]。
    """
    return {
        "temperature_coupling_mode": "decoupled",  # "decoupled" | "coupled"
        "fixed_llm_temperature": 1.0,              # 解耦模式默认温度
        "max_llm_temperature": 1.5,                # 耦合模式温度上限
    }
