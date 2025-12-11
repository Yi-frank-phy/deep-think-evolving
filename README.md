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
│  │  │  Phase 3: 进化循环                            ┌─► END (收敛)   │   │   │
│  │  │  Architect → Executor → Distiller → Judge │                   │   │   │
│  │  │       ▲                             │       └─► Evolution ─┘   │   │   │
│  │  │       └─────────────────────────────┘          (不收敛则继续)    │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
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
| **Architect** | `src/agents/architect.py` | 基于 UCB 评分调度任务执行优先级 |
| **Executor** | `src/agents/executor.py` | 执行原子任务，可生成策略变体 |
| **Judge** | `src/agents/judge.py` | 多维度评估策略质量（逻辑性、可行性、创新性） |
| **Evolution** | `src/agents/evolution.py` | 计算空间熵，执行自适应温度控制与策略剪枝 |
| **Distiller** | `src/agents/distiller.py` | 为 Judge 提供精炼的上下文摘要 |

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
git clone https://github.com/your-repo/deep-think-evolving.git
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
python main.py --max-iterations 5 --temperature-coupling auto
```

可用参数：

- `--max-iterations` - 最大进化迭代次数（默认 5）
- `--temperature-coupling` - 温度耦合模式：`auto`（动态）或 `manual`（固定 1.0）
- `--emit-spec-log` - 输出规范化日志到文件

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

### 空间熵 (Spatial Entropy)

系统通过嵌入向量计算策略间的语义多样性：

```python
H(Strategies) = -Σ p(s) * log(p(s))
```

其中概率密度通过**核密度估计 (KDE)** 从嵌入空间计算得出。

### 自适应温度 (τ)

归一化温度控制探索与利用的平衡：

```python
τ = T_eff / T_max
```

- **高 τ（接近 1）**：高熵阶段，鼓励探索，LLM temperature 升高
- **低 τ（接近 0）**：低熵阶段，收敛信号，LLM 更保守

### UCB 评分

策略选择基于改进的 UCB 公式：

```python
UCB_Score = Value_Score + C * sqrt(log(N) / n)
```

结合探索奖励（稀有概念加分）与开发价值。

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
| `entropy_threshold` | 0.01 | 收敛判定熵阈值 |
| `total_child_budget` | 6 | 每轮生成的子策略数量 |
| `t_max` | 2.0 | 最大温度上限 |
| `c_explore` | 1.0 | UCB 探索系数 |
| `temperature_coupling` | auto | 温度-LLM 耦合模式 |

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
