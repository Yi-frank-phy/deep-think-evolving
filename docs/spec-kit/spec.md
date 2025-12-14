# Deep Think Evolving - 系统规范 v2.0

## 1. 背景与目标

Deep Think Evolving 是一个基于 **LangGraph** 的多代理进化研究助理系统。系统通过多个专职代理协作，采用进化算法（KDE 密度估计、Ising 温度模型、UCB 多臂老虎机、Boltzmann 软剪枝）对策略空间进行探索和优化。

### 1.1 核心设计理念

- **进化驱动**：策略通过多轮迭代进化，基于空间熵收敛判断何时停止
- **软剪枝**：使用 Boltzmann 分布进行资源分配，而非硬性淘汰
- **上下文防腐**：通过 Distiller 代理定期蒸馏上下文，防止 Context Rot
- **知识沉淀**：Judge 代理在评估过程中主动将经验写入知识库

## 2. 系统架构

### 2.1 工作流概览

```text
Phase 1 (问题理解): TaskDecomposer → Researcher → StrategyGenerator
Phase 2 (初评): DistillerForJudge → Judge → Evolution
Phase 3 (执行循环): ArchitectScheduler → Executor → DistillerForJudge → Judge → Evolution → (收敛?)
```

### 2.2 收敛条件

系统在以下任一条件满足时终止进化循环：

1. `iteration_count >= max_iterations` (默认: 10)
2. 熵变化率稳定: `|Δentropy| / max(|entropy|, 1.0) < entropy_change_threshold` (默认: 0.1)
3. 无活跃策略剩余

> **设计说明**: 使用相对变化率而非绝对阈值，因为高维嵌入空间的差分熵可能为负值。
> 首次迭代自动跳过熵收敛检查（无历史数据可比较）。

## 3. 核心代理规范

### 3.1 TaskDecomposer（任务拆解专家）

**文件**: `src/agents/task_decomposer.py`

**职责**:

- 将复杂问题分解为可处理的子任务
- 生成信息需求清单，指导后续搜索

**输入**: `problem_state` (问题描述字符串)

**输出**:

- `subtasks`: 子任务列表 `List[str]`
- `information_needs`: 信息需求清单 `List[{topic, type, priority}]`

**信息需求类型**:

- `factual`: 事实性知识（定义、数据、现状）
- `procedural`: 程序性知识（方法、步骤、最佳实践）
- `conceptual`: 概念性知识（原理、理论、关系）

---

### 3.2 Researcher（深度研究专家）

**文件**: `src/agents/researcher.py`

**职责**:

- 基于信息需求清单进行 Google Search Grounding
- 在单次调用中自我反思信息充足性（成本优化设计）

**输入**:

- `problem_state`: 原始问题
- `information_needs`: 来自 TaskDecomposer 的需求清单

**输出**:

- `research_context`: 汇总的研究背景文本
- `research_status`: `"sufficient"` 或 `"insufficient"`
- `research_iteration`: 当前研究迭代计数

**配置**:

- `max_research_iterations`: 最大研究循环次数 (默认: 3)

---

### 3.3 StrategyGenerator（策略生成器）

**文件**: `src/agents/strategy_generator.py`

**职责**:

- 基于研究上下文生成所有可能的初始策略
- 仅负责生成，不负责评分或调度

**输入**:

- `problem_state`: 问题描述
- `research_context`: 研究背景
- `subtasks`: 子任务列表

**输出**:

- `strategies`: 策略节点列表 `List[StrategyNode]`

**策略节点结构** (`StrategyNode`):

```typescript
{
  id: string;                    // UUID
  name: string;                  // 策略名称
  rationale: string;             // 策略理由
  assumption: string;            // 核心假设
  milestones: Array<{title, summary}>;
  
  // 进化指标 (由 Evolution 计算)
  embedding: float[] | null;     // 嵌入向量 (4096维 for Qwen3-Embedding-8B)
  density: float | null;         // KDE 密度
  log_density: float | null;     // 对数密度
  score: float;                  // Judge评分 (0-1)
  ucb_score: float | null;       // UCB综合评分 (用于排序/展示)
  child_quota: int | null;       // Boltzmann分配的子节点配额
  
  status: "active" | "pruned" | "completed" | "expanded";
  trajectory: string[];          // 执行轨迹记录
  parent_id: string | null;      // 父策略 ID (用于树结构)
}
```

---

### 3.4 Judge（战略审查官）

**文件**: `src/agents/judge.py`

**职责**:

- 评估策略的可行性与逻辑自洽性
- 观察演化规律，主动将经验写入知识库
- 仅负责评分，不负责剪枝决策

**输入**:

- `strategies`: 待评估的策略列表
- `judge_context`: 来自 Distiller 的蒸馏上下文

**输出**:

- 更新后的 `strategies` (带评分)
- 知识库写入记录 (可选)

**评分标准** (0-10):

1. 逻辑自洽性: 理由是否支持结论
2. 假设合理性: 关键假设是否过于牵强
3. 约束符合性: 是否违背基本约束

**知识库写入类型**:

- 🔴 `lesson_learned`: 教训（失败模式、逻辑漏洞）
- 🟢 `success_pattern`: 成功模式（有效推理方式）
- 💡 `insight`: 洞见（新视角、隐含关联）

---

### 3.5 Evolution（进化引擎）

**文件**: `src/agents/evolution.py`

**职责**:

- 计算策略嵌入向量
- 计算空间熵（KDE 密度估计）
- 计算有效温度（Ising 模型）
- 使用 Boltzmann 分配决定子节点配额

**输入**:

- `strategies`: 评分后的策略列表
- `config`: 进化配置参数

**输出**:

- 更新后的 `strategies` (带嵌入、密度、UCB、子节点配额)
- `spatial_entropy`: 当前空间熵
- `effective_temperature`: 当前有效温度
- `iteration_count`: 迭代计数 +1

**数学引擎**:

- **KDE 密度估计**: `src/math_engine/kde.py`
  - `gaussian_kernel_log_density()`: 高斯核对数密度
  - `estimate_bandwidth()`: 带宽估计
- **温度模型**: `src/math_engine/temperature.py`
  - `calculate_effective_temperature()`: 基于熵值计算
  - `calculate_normalized_temperature()`: 归一化到 [0, T_max]
- **UCB 评分**: `src/math_engine/ucb.py`
  - `batch_calculate_ucb()`: 批量 UCB 计算

**Boltzmann 分配公式**:

```text
n_s = f(C * exp(V_s / T) / Z)
其中 Z = sum(exp(V_j / T)) 是配分函数
```

**分段取整规则 (Piecewise Rounding)**:

- 配额 < 1: 四舍五入 (给低分策略公平机会)
- 配额 >= 1: 向上取整 (确保高分策略获得足够资源)

> **注意**: 由于向上取整，实际总分配可能略超过 `total_child_budget`。

**LLM 温度**: 固定为 `T=1.0` (Logic Manifold Integrity)。
系统温度 τ 仅影响资源分配 (Sampling Count N / Beam Width)，不影响 LLM 推理。

---

### 3.6 ArchitectScheduler（战略调度官）

**文件**: `src/agents/architect.py`

**职责**:

- 基于 UCB 评分和 Boltzmann 配额为策略编写执行指令
- 决定每个策略的执行方向（探索、变体、深化、验证）

**输入**:

- `strategies`: 带配额的活跃策略列表
- `problem_state`: 原始问题

**输出**:

- `architect_decisions`: 执行决策列表

  ```typescript
  [{
    strategy_id: string;
    executor_instruction: string;  // 自然语言指令
    context_injection: string;     // 可选上下文注入
  }]
  ```

---

### 3.7 Executor（策略执行器）

**文件**: `src/agents/executor.py`

**职责**:

- 执行 Architect 分配的具体任务
- 可生成策略变体（添加到策略池）

**输入**:

- `architect_decisions`: 来自 Architect 的决策列表
- `strategies`: 当前策略列表
- `problem_state`: 原始问题

**输出**:

- 更新后的 `strategies` (含轨迹更新和新变体)
- 清空 `architect_decisions`

---

### 3.8 Distiller（信息蒸馏器）

**文件**: `src/agents/distiller.py`

**职责**:

- 压缩上下文，防止 Context Rot
- 为 Judge 生成清洁的评估上下文

**函数**:

- `distiller_node()`: 通用蒸馏节点
- `distiller_for_judge_node()`: 专为 Judge 准备上下文
- `should_distill()`: 动态触发检查
- `estimate_token_count()`: token 估计

**输出**:

- `judge_context`: 蒸馏后的上下文字符串

## 4. 状态管理

### 4.1 全局状态 (`DeepThinkState`)

**文件**: `src/core/state.py`

```typescript
interface DeepThinkState {
  // 输入
  problem_state: string;
  
  // 任务分解结果
  subtasks: string[] | null;
  information_needs: Array<{topic, type, priority}> | null;
  
  // 进化状态
  strategies: StrategyNode[];
  
  // 研究上下文
  research_context: string | null;
  research_status: "sufficient" | "insufficient" | null;
  research_iteration: number | null;
  
  // 全局指标
  spatial_entropy: float;
  effective_temperature: float;
  normalized_temperature: float;
  
  // 配置
  config: {
    model_name?: string;
    t_max?: float;           // 默认: 2.0
    c_explore?: float;       // UCB 探索系数，默认: 1.0
    beam_width?: int;        // 默认: 3
    thinking_budget?: int;   // 默认: 1024
    max_iterations?: int;    // 默认: 10
    entropy_change_threshold?: float; // 熵变化率阈值，默认: 0.1
    total_child_budget?: int;  // Boltzmann 总预算，默认: 6
    max_research_iterations?: int; // 默认: 3
  };
  
  // 内存
  virtual_filesystem: Dict<string, string>;
  history: string[];  // 使用 operator.add reducer
  
  // 迭代跟踪
  iteration_count: int;
  
  // Distiller 输出
  judge_context: string | null;
  
  // Architect 输出
  architect_decisions: Array<{strategy_id, executor_instruction, context_injection}> | null;
}
```

## 5. API 端点规范

### 5.1 REST 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/models` | 获取可用模型列表 |
| POST | `/api/simulation/start` | 启动进化模拟 |
| POST | `/api/simulation/stop` | 停止当前模拟 |
| POST | `/api/expand_node` | 展开节点（扩展策略描述） |
| POST | `/api/chat/stream` | 流式聊天 (SSE) |
| POST | `/api/hil/response` | 提交人机交互响应 |
| GET | `/api/hil/pending` | 获取待处理的 HIL 请求 |

### 5.2 WebSocket 端点

| 路径 | 描述 |
|------|------|
| `/ws/knowledge_base` | 知识库实时更新推送 |
| `/ws/simulation` | 模拟进度实时遥测 |

### 5.3 模拟请求格式

```typescript
interface SimulationRequest {
  problem: string;
  config: {
    model_name?: string;       // 默认: "gemini-2.5-flash"
    t_max?: float;             // 默认: 2.0
    c_explore?: float;         // 默认: 1.0
    beam_width?: int;          // 默认: 3
    thinking_budget?: int;     // 默认: 1024
    max_iterations?: int;      // 默认: 10
    entropy_threshold?: float; // 默认: 0.01
    total_child_budget?: int;  // 默认: 6
    // NOTE: LLM temperature is always 1.0 (Logic Manifold Integrity)
  };
}
```

### 5.4 WebSocket 消息类型

**模拟遥测** (`/ws/simulation`):

- `INIT`: 初始状态
- `EVOLUTION_UPDATE`: 每次迭代后的策略和指标更新
- `AGENT_LOG`: 代理执行日志
- `CONVERGENCE`: 收敛通知
- `ERROR`: 错误通知
- `HIL_REQUIRED`: 需要人类干预

**知识库** (`/ws/knowledge_base`):

- 首次连接: 全量快照
- 后续: `update` / `delete` 事件

## 6. 知识库工具

**文件**: `src/tools/knowledge_base.py`

### 6.1 write_experience

写入经验到向量知识库。由 Judge 在评估过程中调用。

```python
@tool
def write_experience(
    category: Literal["lesson_learned", "success_pattern", "insight"],
    context: str,
    content: str,
    tags: List[str] = []
) -> str
```

### 6.2 search_experiences

向量搜索知识库中的相关经验。

```python
@tool
def search_experiences(
    query: str,
    category: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]
```

## 7. 人机交互 (HIL)

**文件**: `src/tools/ask_human.py`

### 7.1 ask_human 工具

允许任意代理在执行过程中请求人类输入。

```python
@tool
def ask_human(
    question: str,
    context: str = ""
) -> str
```

### 7.2 HILManager

管理待处理的人类交互请求，通过 WebSocket 通知前端。

## 8. 嵌入服务

**文件**: `src/embedding_client.py`

### 8.1 配置

支持多个嵌入服务提供商：

| 环境变量 | 描述 |
|----------|------|
| `EMBEDDING_PROVIDER` | 提供商选择: `ollama`, `modelscope`, `openai` |
| `EMBEDDING_MODEL` | 模型名称 |
| `EMBEDDING_BASE_URL` | API 端点 |
| `MODELSCOPE_API_KEY` | ModelScope API Key |

### 8.2 Mock 模式

当 `USE_MOCK_EMBEDDING=true` 时，使用随机嵌入向量用于测试。

## 9. 离线 / Mock 模式

### 9.1 环境变量

| 变量 | 描述 |
|------|------|
| `USE_MOCK_AGENTS` | 所有代理使用 Mock 响应 |
| `USE_MOCK_EMBEDDING` | 嵌入服务使用随机向量 |
| `GEMINI_API_KEY` | Gemini API 密钥（缺失时自动启用 Mock） |

### 9.2 冒烟测试

```bash
pytest -m smoke
```

在无 API 密钥环境下可运行，验证流水线结构正确。

## 10. SpecKit 合规要求

### 10.1 必需文档

| 文件 | 描述 |
|------|------|
| `docs/spec-kit/spec.md` | 本规范文档 |
| `docs/spec-kit/plan.md` | 实施计划 |
| `docs/spec-kit/tasks.md` | 任务跟踪 |
| `docs/spec-kit/constitution.md` | 项目宪章 |

### 10.2 CI 合规检查

所有 PR 必须通过 `scripts/check_specs.py` 检查：

```bash
python scripts/check_specs.py
```

### 10.3 PR 要求

每个 PR 必须：

1. 引用相关规范章节 (`spec.md §X.X`)
2. 引用相关任务条目 (`tasks.md T-XXX`)
3. 同步更新规范文档（如涉及架构变更）

## 11. 非功能性要求

### 11.1 可观测性

- 所有代理通过 `print(f"[{AgentName}] ...")` 记录关键事件
- WebSocket 实时推送执行状态
- `history` 字段记录完整执行轨迹

### 11.2 可扩展性

- TypedDict 状态定义支持类型检查
- 模块化代理设计，易于添加新代理
- LangGraph 支持动态修改工作流

### 11.3 安全性

- CORS 限制为允许的来源列表（通过 `ALLOWED_ORIGINS` 环境变量配置）
- 知识库文件保存在 `knowledge_base/` 目录

## 12. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0 | 2025-10 | 初始版本（线性流水线） |
| 2.0 | 2025-12 | 重写为 LangGraph 多代理进化架构 |
