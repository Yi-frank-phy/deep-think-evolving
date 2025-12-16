# Deep Think · Evolving

一个基于自适应进化压力的多智能体研究助理系统

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Enabled-purple.svg)](https://github.com/langchain-ai/langgraph)

---

## 项目愿景

Deep Think Evolving 是一个实验性多智能体系统，核心理念是将**进化压力**引入 AI 推理过程。系统模拟一个"思维生态"，让多条研究策略在**空间熵**的调控下竞争与进化，最终收敛至高质量解决方案。

### 核心创新

- **自适应温度控制**：系统根据策略多样性（空间熵）动态调整 LLM 的探索倾向
- **并行策略进化**：多条独立策略树同时生长，通过 UCB 评分实现"选择性存活"
- **Human-in-the-Loop**：LLM 可主动向用户请求关键输入（`ask_human` 工具）
- **实时可视化控制塔**：WebSocket 驱动的前端，实时展示策略树演化过程

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Deep Think · Evolving                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     LangGraph 状态图 (StateGraph)                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  Phase 1: 问题理解                                             │   │   │
│  │  │  TaskDecomposer → Researcher (循环) → StrategyGenerator        │   │   │
│  │  └─────────────────────────────┬────────────────────────────────┘   │   │
│  │                                ▼                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  Phase 2: 初始评估                                             │   │   │
│  │  │  Distiller → Judge → Evolution                                 │   │   │
│  │  └─────────────────────────────┬────────────────────────────────┘   │   │
│  │                                ▼                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  Phase 3: 进化循环 (探索 ↔ 利用 ↔ 综合 连续频谱)                  │   │   │
│  │  │  Architect → Executor → Distiller → Judge → Evolution         │   │   │
│  │  │       ▲         │ (可动态生成报告)        │                   │   │   │
│  │  │       └───────────────── (不收敛) ─────────┘                   │   │   │
│  │  └─────────────────────────────┬────────────────────────────────┘   │   │
│  │                                ▼ (收敛)                              │   │
│  │                               END                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│  FastAPI Server (WebSocket + REST)  ⟷  React 控制塔前端                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 智能体角色

| 智能体 | 文件路径 | 职责 |
|--------|----------|------|
| **TaskDecomposer** | `src/agents/task_decomposer.py` | 解析问题，识别子任务与信息需求 |
| **Researcher** | `src/agents/researcher.py` | 通过 Google Search Grounding 收集外部信息 |
| **StrategyGenerator** | `src/agents/strategy_generator.py` | 生成多条独立的高层策略蓝图 |
| **Architect** | `src/agents/architect.py` | 基于元策略框架(探索↔利用↔综合)自主调度任务 |
| **Executor** | `src/agents/executor.py` | 执行原子任务，可生成策略变体或综合报告 |
| **Judge** | `src/agents/judge.py` | 多维度评估策略质量（逻辑性、可行性、创新性） |
| **Evolution** | `src/agents/evolution.py` | 计算空间熵，执行自适应温度控制与策略剪枝 |
| **Distiller** | `src/agents/distiller.py` | 为 Judge 提供精炼的上下文摘要 |

---

## 硬剪枝与动态报告生成

系统采用 **报告 = 剪枝信号** 的设计理念：

- **动态综合**: Architect 可分配 `strategy_id=null` 的综合任务，由 Executor 执行
- **硬剪枝**: 综合后所有活跃策略 `status="pruned_synthesized"`
- **价值保留**:
  - 报告本身 → 活跃上下文
  - 知识库归档 → 向量数据库（分支选择逻辑、经验、推理过程）

此设计防止上下文腐烂，降低 Token 成本，同时保留所有有价值信息。

---

## 核心技术栈

### 后端

- **Python 3.10+** + FastAPI
- **LangGraph** - 构建有状态的 Agent 工作流
- **Google GenAI SDK** - Gemini 模型调用（支持动态 thinking budget）
- **ModelScope Embedding** - Qwen3-Embedding-8B 向量化服务

### 前端

- **React 18** + TypeScript
- **Vite** - 构建工具
- **WebSocket** - 实时通信

---

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/Yi-frank-phy/deep-think-evolving.git
cd deep-think-evolving

# Python 虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
npm install
```

### 2. 配置环境变量

创建 `.env` 文件（参考 `.env.example`）：

```bash
# Gemini API（必需）
GEMINI_API_KEY=your_google_api_key

# ModelScope Embedding（可选，有默认值）
MODELSCOPE_API_KEY=your_modelscope_api_key
```

### 3. 启动后端服务

```bash
# 开发模式（支持热重载）
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# 或直接运行
python server.py
```

后端服务提供以下端点：

- `GET /health` - 健康检查
- `GET /api/models` - 获取可用模型列表
- `POST /api/simulation/start` - 启动进化模拟
- `POST /api/simulation/stop` - 停止模拟
- `WS /ws/simulation` - 模拟实时数据流
- `WS /ws/knowledge_base` - 知识库更新推送

### 4. 启动前端控制塔

```bash
npm run dev
```

访问 `http://localhost:5173` 打开控制塔界面。

### 5. 运行命令行流水线

如需在命令行运行完整流水线：

```bash
python main.py --max-iterations 5
```

可用参数：

- `--max-iterations` - 最大进化迭代次数（默认 5）
- `--emit-spec-log` - 输出规范化日志到文件

> **Note**: LLM 推理温度固定为 `T=1.0` (Logic Manifold Integrity)，系统温度 τ 仅控制资源分配。

---

## 项目结构

```
deep-think-evolving/
├── server.py                    # FastAPI 服务器（WebSocket + REST）
├── main.py                      # 命令行流水线入口
├── requirements.txt             # Python 依赖
├── package.json                 # 前端依赖
│
├── src/
│   ├── agents/                  # 智能体实现
│   │   ├── task_decomposer.py   #   问题分解
│   │   ├── researcher.py        #   信息收集
│   │   ├── strategy_generator.py#   策略生成
│   │   ├── architect.py         #   任务调度
│   │   ├── executor.py          #   任务执行
│   │   ├── judge.py             #   质量评估
│   │   ├── evolution.py         #   进化控制
│   │   └── distiller.py         #   上下文精炼
│   │
│   ├── core/                    # 核心框架
│   │   ├── graph_builder.py     #   LangGraph 状态图构建
│   │   └── state.py             #   全局状态定义 (DeepThinkState)
│   │
│   ├── tools/                   # Agent 工具
│   │   ├── ask_human.py         #   Human-in-the-Loop 工具
│   │   └── knowledge_base.py    #   知识库操作
│   │
│   ├── components/              # React 组件
│   │   ├── ControlTower.tsx     #   主控制台
│   │   ├── TaskGraph.tsx        #   策略树可视化
│   │   ├── KPIDashboard.tsx     #   KPI 仪表盘
│   │   ├── InterventionPanel.tsx#   人机交互面板
│   │   └── ...
│   │
│   ├── context_manager.py       # 上下文/记忆管理
│   ├── strategy_architect.py    # 策略蓝图生成器
│   ├── embedding_client.py      # 嵌入向量服务
│   ├── diversity_calculator.py  # 多样性/熵计算
│   └── google_grounding.py      # Google Search Grounding
│
├── docs/
│   ├── spec-kit/                # 项目规范文档
│   │   ├── constitution.md      #   项目宪章
│   │   ├── spec.md              #   系统规范
│   │   ├── plan.md              #   迭代计划
│   │   └── tasks.md             #   任务拆解
│   └── CONTRIBUTING.md          # 贡献指南
│
├── tests/                       # 测试套件
├── knowledge_base/              # 长期知识存储（运行时生成）
└── artifacts/                   # 运行产物/日志
```

---

## 进化算法详解

本系统的数学引擎受**统计力学**启发，将策略进化建模为一个热力学系统。

### 核心物理隐喻

| 物理概念 | 系统对应 | 代码位置 |
|---------|---------|----------|
| 粒子 (Particle) | 策略节点 (StrategyNode) | `state.py` |
| 能量 (Energy) | 策略价值 (Judge Score) | `judge.py` |
| 温度 (Temperature) | 探索倾向 (τ) | `temperature.py` |
| 熵 (Entropy) | 策略多样性 | `kde.py` |
| 配分函数 (Z) | 归一化因子 | `evolution.py` |

---

### 1. 空间熵 (Spatial Entropy)

通过 **核密度估计 (KDE)** 计算策略在嵌入空间的分布密度：

```python
# 高斯核密度估计
p(x) = (1/n) * Σ K_h(x - x_i)

# 空间熵 (差分熵)
H = -E[log p(x)] = -mean(log_densities)
```

> **高维注意**: 4096维嵌入空间中，差分熵**可能为负值**。系统使用**熵变化率**而非绝对阈值判断收敛。

**带宽估计** (Silverman规则):

```python
h = 1.06 * σ * n^(-1/5)
```

---

### 2. 有效温度 (Effective Temperature)

基于 **Value-LogDensity 线性回归** 估计系统温度：

```
ln p(v) = (1/T) * v + C
```

通过计算斜率 k = Cov(V, ln p) / Var(V)，得到：

```python
T_eff = |Var(V) / Cov(V, ln p)|
τ = T_eff / T_max  # 归一化到 [0, 1]
```

**物理意义**:

- **高 τ (接近1)**: 策略分布均匀，需要**发散探索**
- **低 τ (接近0)**: 策略趋于集中，可以**收敛利用**

---

### 3. Boltzmann 资源分配 (Soft Pruning)

**核心公式** (Ising模型):

```
n_s = f(C × exp(V_s / T) / Z)

其中:
- C = total_child_budget (总预算)
- V_s = 策略s的Judge评分 (0-1)
- T = T_eff (有效温度)
- Z = Σ exp(V_j / T) (配分函数)
```

**分段取整规则** (Piecewise Rounding):

| 原始配额 | 规则 | 示例 |
|----------|------|------|
| quota < 1 | 四舍五入 | 0.3→0, 0.5→1 |
| quota >= 1 | 向上取整 | 1.1→2, 2.3→3 |

**设计理由**:

- 低分策略通过四舍五入获得**公平机会** (尾部探索)
- 高分策略通过向上取整保证**足够资源** (头部利用)
- 总分配可能**略超**预算，这是设计预期

---

### 4. UCB 评分 (Multi-Armed Bandit)

结合**利用**与**探索**的评分公式：

```python
UCB = Score + c × τ × Normalize(1/√p_rel)

其中:
- Score = Judge 评分 (0-1)，直接使用，不再二次归一化
- p_rel = density / max(density)  # 相对密度
- Normalize() = Min-Max 归一化到 [0, 1]
- c = c_explore 探索系数 (默认 1.0)
- τ = 归一化温度
```

**数学基础**：不确定性 σ ∝ 1/√(有效样本量) ∝ 1/√(density)

> 详细推导见 [docs/math_proof_ucb.md](./docs/math_proof_ucb.md)

低密度（新颖/少探索）策略获得**探索奖励**，保证 UCB ≥ Score（上确界性质）。

---

### 5. 热力学控制机制 (Thermodynamic Control Mechanism)

系统温度 τ **严格控制计算资源分配**（采样数 N、Beam Width），而非 LLM 的采样温度。

> **设计原则 (Logic Manifold Integrity)**: LLM 的内在推理温度固定为 `T=1.0`，以保持逻辑流形完整性。
> Google DeepMind 建议推理模型（如 Gemini 3）保持 `temperature=1.0`。

**资源分配公式**:

```
n_s = f(C × exp(V_s / τ) / Z)

其中:
- n_s = 策略 s 的采样/分支预算
- τ = 系统有效温度 (State Probe 估计)
- V_s = 策略 s 的 Judge 评分
- Z = Σ exp(V_j / τ) 配分函数
```

**有效温度计算** (State Probe - 逆正则系综问题):

从当前批次的**经验分布** p(v) 估计系统"多样性温度"：

```
k = Cov(V, ln p) / Var(V)
T_eff = |1 / k|
```

- `p(v)`: 当前策略批次的经验密度分布 (KDE 估计)
- 这是一个**状态探测器**：估计系统当前多样性温度，作为下一步资源分配的反馈信号

**温度语义**:

| 温度状态 | 含义 | 资源分配行为 |
|---------|------|-------------|
| 高 τ (接近1) | 策略分布均匀 | 广播探索 (High N) |
| 低 τ (接近0) | 策略趋于集中 | 贪婪收敛 (Low N) |

---

### 6. 收敛条件

系统在以下**任一**条件满足时终止：

1. `iteration_count >= max_iterations` (默认: 10)
2. 熵变化率稳定: `|ΔH| / max(|H|, 1.0) < threshold` (默认: 0.1)
3. 无活跃策略剩余

> **首轮跳过**: 第一次迭代无历史熵可比较，自动继续。

---

### 7. 资源分配架构

```
           ┌─────────────────┐
           │    Evolution    │
           │     (CFO)       │
           └────────┬────────┘
                    │ child_quota (数量)
                    ▼
           ┌─────────────────┐
           │    Architect    │
           │     (CTO)       │
           └────────┬────────┘
                    │ 具体任务类型
                    ▼
           ┌─────────────────┐
           │    Executor     │
           │    (Worker)     │
           └─────────────────┘
```

**职责分离**:

- **Evolution (CFO)**: 只计算 `child_quota` (探索配额数量)
- **Architect (CTO)**: 决定具体任务类型 (探索/利用/变异)
- **完全不剪枝**: 低分策略只是"冻结" (quota=0)，随时可能复活

---

## Human-in-the-Loop (HIL)

系统支持两种人机交互模式：

### Pull 模式（LLM 主动请求）

Judge Agent 可在关键决策点调用 `ask_human` 工具：

```python
from src.tools.ask_human import ask_human

response = await ask_human(
    question="策略 A 和 B 在逻辑上互斥，请确认优先保留哪个？",
    context="策略 A: ..., 策略 B: ..."
)
```

前端 `InterventionPanel` 组件展示请求并收集用户回复。

### Push 模式（用户主动干预）

通过 `/api/simulation/pause` 暂停模拟，手动修改策略后恢复。

---

## 开发指南

### 运行测试

```bash
# 全量测试
pytest

# 离线冒烟测试（无需外部服务）
pytest -m smoke

# 通过 npm 脚本
npm run test
```

### 关键配置项

在 `main.py` 或 API 请求中可调整：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_iterations` | 10 | 最大进化循环次数 |
| `entropy_change_threshold` | 0.1 | 收敛判定熵变化率阈值 |
| `total_child_budget` | 6 | 每轮生成的子策略预算 (实际可能略超) |
| `t_max` | 2.0 | 最大系统温度上限 (用于归一化) |
| `c_explore` | 1.0 | UCB 探索系数 |

> **Note**: LLM 推理温度固定为 `T=1.0` (Logic Manifold Integrity)，不可配置。

---

## 路线图

### ✅ 已完成

- [x] LangGraph 多阶段工作流（Phase 1-3）
- [x] 8 种专业化 Agent 角色
- [x] FastAPI WebSocket 实时推送
- [x] React 控制塔 UI
- [x] Human-in-the-Loop (ask_human) 工具
- [x] ModelScope Qwen3 嵌入服务集成
- [x] Google Search Grounding 整合

### 🚧 进行中

- [ ] 实时任务图可视化（节点状态/分数渲染）
- [ ] KPI 仪表盘（成本/Token 追踪）
- [ ] 可视化条件断点

### 📋 计划中

- [ ] 预算控制与告警
- [ ] 向量数据库持久化（ChromaDB）
- [ ] 元策略学习（跨任务优化）
- [ ] 引导式配置向导

详细任务列表参见 [`todo_list.md`](./todo_list.md) 和 [`ARCHITECTURE_TODO.md`](./ARCHITECTURE_TODO.md)。

---

## 相关文档

- [`docs/spec-kit/spec.md`](./docs/spec-kit/spec.md) - 完整系统规范
- [`docs/spec-kit/constitution.md`](./docs/spec-kit/constitution.md) - 项目宪章与质量门禁
- [`todo_list_backend.md`](./todo_list_backend.md) - 后端开发任务清单
- [`mcp-readme.md`](./mcp-readme.md) - MCP 模型工具链扩展指南
- [`docs/CONTRIBUTING.md`](./docs/CONTRIBUTING.md) - 贡献指南与分支治理

---

## License

MIT License - 详见 [LICENSE](./LICENSE)

---

> *"给 AI 注入进化的压力，让最优解在竞争中涌现。"*
