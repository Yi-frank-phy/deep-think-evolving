# **开发需求文档：一个“自适应进化压力”下的“混合智能体”生态系统**

版本: final draft v0
日期: 2025年9月8日  
核心约束 (Core Constraint): 不可以涉及对于调用的LLM API内部参数的权重更新 (No modification to the internal weights of the called LLM APIs is allowed)。  
可控接口 (Controllable Interfaces): Google/GenAI SDK, LangChain, etc.
框架选择：建议全局使用langchain和langgraph，特别是其中的langchain google的包。但是，对于涉及到及其细粒度的控制，则直接改为Google/GenAI SDK，不建议使用其他框架，除非必须
Agent 自己可以使用的工具：mcp tools, groundings，

### **1\. 系统顶层设计哲学 (Guiding Principles)**

1.1. 从“系统设计”到“生态培育”  
1.2. 有引导的进化 (Guided Evolution)  
1.3. 经典与涌现的共生 (Symbiosis of Classic & Emergent)

### **2\. 高级系统架构：嵌套进化引擎 (Nested Evolution Engine)**

(本节内容整合自v3.2)  
为了在不改变模型权重的前提下提升智能上限，我们将系统设计为一个嵌套的双循环进化系统。  
**2.1. 内循环 (Inner Loop): 在线解法进化 (Online Solution Evolution)**

* **职责**: 针对一个具体问题，其实时推理过程本身就是一个高速的、在线的微型进化算法，旨在进化出该问题的最优解法。  
* **核心技术**: **并行进化搜索 (Parallel Evolutionary Search)**。类AlphaEvolve的遗传算法、模拟退火。

**2.2. 外循环 (Outer Loop): 离线策略进化 (Offline Strategy Evolution)**

* **职责**: 在后台运行，进化出更强大的**元策略 (Meta-Strategies)**，用于指导和配置内循环进化引擎。  
* **核心技术**: 类似agent fly 框架的对于记忆的训练

2.3. 嵌套统一关系 (Nested Unification)  
外循环进化出内循环的“进化规则”，内循环则在这些规则的指导下进化出具体问题的“解”。例如，外循环可以进化出用于Value\_Score评估的最佳Prompt模板，或者调整探索项的平衡系数C。  
2.4. 【继承自v3.1】循环接口 \- 启发式部署与验证协议 (Heuristic Deployment & Validation Protocol)  
外循环产生的新策略需经过策略暂存区 (Staging Area) 和 A/B测试，验证其有效性后才能部署到整个生态。

### **3\. 内循环：并行进化搜索引擎 (Parallel Evolutionary Search Engine)**

3.1. 核心Agent认知架构：模块化Agent设计  
(继承自v3.1，保持不变)

* **规划器 (Planner)**  
* **执行器 (Executor)**  
* **反思器 (Reflector)**  
* **记忆控制器 (Memory Controller)**

3.2. 先进的搜索算法: 并行进化搜索 (Parallel Evolutionary Search)  
本算法旨在解决LLM串行思维带来的多样性瓶颈，其核心是通过“人机协同”的模式，在关键节点进行可靠的策略分叉。  
**3.2.1. 核心挑战与对策 (Core Challenge & Strategy)**

* **挑战**: 完全依赖自主Agent（无论是单个还是多个）来生成高质量、多样化的战略分叉点，在工程上是脆弱且不可靠的。  
* **对策**: 我们采用一个\*\*“LLM生成可能性，人类进行决策 (LLM Proposes, Human Disposes)”\*\* 的人机协同流程，将LLM定位为“战略架构师”，而将人类专家定位为最终的“总设计师”。

3.2.2. 【v3.7 核心更新】冷启动与人机协同 (Cold Start & Human-in-the-Loop)

**1. 基于 Deep Research 的搜索辅助冷启动 (Search-Assisted Cold Start)**
为了打破 LLM 的“闭门造车”并解决冷启动多样性不足的问题，在生成初始策略前，系统引入**搜索辅助思考**流程：

* **任务分解**: 将复杂问题拆解为若干关键子问题。
* **广度搜索**: 针对子问题进行广泛的外部知识搜索 (借助 Google Search Grounding)，获取最新的研究成果、类似案例或多元观点。
* **信息蒸馏 (Information Distiller)**: 参考 `langchainai/open-deep-research` 的架构，引入一个专门的筛选器 Agent，负责从海量搜索结果中去噪、提炼核心观点，并生成高质量的上下文摘要（Contextual Summary）。
* **灵感注入**: 将蒸馏后的摘要作为“灵感种子”注入给战略架构师，确保生成的初始策略蓝图建立在广阔的信息视野之上。

**2. 战略架构师 (Strategy Architect)**
基于搜索结果，生成互斥的战略蓝图（JSON格式）。人类的主动输入（如新的约束或方向）主要在此阶段或通过 Judge Agent 注入。

**3. 工具化人机协作 (Tool-Use HIL)**

* **双向交互协议**:
  * **LLM -> Human (Pull)**: 系统中**任何** LLM Agent (Architect, Judge, Executor) 均可调用 `ask_human` 工具。人类的回复将直接回传给**发起调用的 Agent**，作为上下文的一部分。
  * **Human -> LLM (Push)**: 人类专家的**主动干预**（如纠偏、注入新约束）**只能**发送给 **Strategy Architect**（重构蓝图）或 **Judge Agent**（调整评分标准）。**严禁**直接干预正在执行具体原子任务的 Executor，以避免破坏其思维连贯性。

3.2.3. 【v3.8 核心重构】进化波束搜索 (Evolutionary Beam Search, EBS)

我们正式将**波束搜索 (Beam Search)** 与 **进化算法 (Evolutionary Algorithms)** 统一在同一个数学框架下。在此视角下，LLM 的推理不再是简单的文本生成，而是策略空间中的**变异算子**。

**3.2.3.1. 同构映射 (Isomorphic Mapping)**

| 进化概念 (EA) | 波束搜索概念 (Beam Search) | 本系统实现 (Implementation) |
| :--- | :--- | :--- |
| **种群 (Population)** | 波束 (Beam) | 当前保留的 $k$ 个候选推理路径 |
| **变异 (Mutation)** | 扩展 (Expansion) | **单次调用单策略 (One-Call-One-Strategy)**：<br>严禁在单次回复中生成多个变体。必须通过 $N$ 次独立的 API 调用来生成 $N$ 个子节点。<br>**理由**: Transformer 的线性思维会导致同一上下文中生成的多个策略趋同，严重损害多样性。 |
| **选择 (Selection)** | 剪枝 (Pruning) | 基于 **UCB 公式** 的评分排序，保留 Top-$k$。 |
| **适应度 (Fitness)** | 启发式评分 (Heuristic) | **Judge Agent**：评估路径的可行性与一致性。 |

**3.2.3.2. 动态提示工程与测试时计算 (Dynamic Prompting & Test-Time Scaling)**

为了最大化 **Test-Time Scaling** 收益，我们摒弃静态 Prompt 模板，采用**父子动态生成机制**：

1. **父节点定义任务 (Parent Defines Task)**:
    父 Agent 不直接生成答案，而是根据当前问题状态和多样性需求（由 $T$ 决定），为子 Agent **动态编写 Prompt**。
2. **原子化专精 (Atomic Specialization)**:
    子 Agent 的 Prompt 被严格限制在**极小粒度的原子任务**上。
    * *错误示范*: "Solve the rest of the problem."
    * *正确示范*: "Calculate the derivative of equation (3) under condition X."
3. **思维预算最大化 (Thinking Budget Optimization)**:
    通过将复杂任务拆解为大量简单的原子任务，我们确保每个子 Agent 都能将其全部的 Context Window 和推理能力（Thinking Budget）集中在当前的小点上，从而实现整体智能的涌现。

**3.2.3.3. 算法流程 (EBS Loop)**

1. **变异 (Mutation / Expansion)**:
    对波束中的每个父节点 $P$，**并行发起 $m$ 次独立的 API 调用**。每次调用使用由父节点动态生成的、略有差异的 Prompt。
2. **评估 (Evaluation)**:
    调用 **Judge Agent** 对新生成的子节点进行**可行性打分**。
    * *注*: Judge 仅关注逻辑是否自洽、是否符合物理/代码约束，不负责验证外部事实真伪（Hallucination is accepted as a capability limitation）。
3. **选择 (Selection)**:
    计算所有候选子节点的 **Dynamic Normalized UCB** 分数，选出新的 Top-$k$ 形成下一代种群。

**3.2.3.4. 空间熵与探索奖励 (Spatial Entropy & Exploration Bonus)**

1. **语义向量化 (Semantic Embedding)**: 将每个策略 $x$ 映射为高维向量 $v(x)$。
2. **空间熵 (Spatial Entropy)**: 定义为种群在语义空间中的“平均离散度”。
    $$ H_{spatial} = \frac{1}{N(N-1)} \sum_{i \neq j} (1 - \text{sim}(v_i, v_j)) $$
    其中 $\text{sim}$ 为余弦相似度。$H_{spatial}$ 越高，代表种群在语义空间分布越广（多样性越高）。

3.2.4. 【新增】高级探索机制：基于数据驱动冷却的自适应 UCB

**3.2.4.1. 核心思想：成本导向的收敛 (Cost-Driven Convergence)**

受 MCTS (蒙特卡洛树搜索) 启发，我们引入一种**正反馈冷却机制**。

* **高熵阶段**: 当解法百花齐放时，系统认为“还有很多未知领域”，保持**高温度**，鼓励进一步探索。
* **低熵阶段**: 当解法开始趋同（$H_{spatial}$ 下降）时，系统判断“已找到潜在最优域”，主动**降低温度**，加速收敛以节省计算成本。

**3.2.4.2. 数学形式化**

**1. 自适应温度 (Adaptive Temperature)**
$$ T = T_{max} \times \left( \frac{H_{spatial}}{H_{target}} \right)^\gamma $$

* $T$: 系统当前的探索率。
* $H_{target}$: 预期的最大多样性（归一化基准）。
* $\gamma$: 敏感度系数（通常 $\ge 1$），用于控制收敛速度。

**2. 动态归一化 UCB (Dynamic Normalized UCB)**
为了解决价值分与探索项的量纲失衡风险，我们引入**动态 Min-Max 归一化**：

$$ Score(x) = \frac{V(x) - V_{min}}{V_{max} - V_{min} + \epsilon} + c \cdot T \cdot \sigma_{local}(x) $$

* **利用项 (Exploitation)**: $V(x)$ 为原始价值分。通过当前候选池的 $V_{max}$ 和 $V_{min}$ 将其动态映射到 $[0, 1]$ 区间，确保其始终与探索项处于同一数量级。
* **探索项 (Exploration)**:
  * $T$: 全局温度（由 $H_{spatial}$ 决定）。
  * $\sigma_{local}(x)$: 局部唯一性，定义为 $x$ 与种群中最近邻居的余弦距离。
    $$ \sigma_{local}(x) = \min_{y \in Population, y \neq x} (1 - \text{sim}(v(x), v(y))) $$

**3.2.4.3. 机制优势**

* **自动止损**: 一旦出现统治级策略导致多样性下降，系统会自动“关火”，停止无效的广度搜索，转为深度优化。
* **动态平衡**: 在 $T$ 的调节下，系统在初期表现为“随机游走”，在后期表现为“梯度下降”，无需人工设定冷却时间表。

3.2.5. 全局协调 (Global Coordination)  
系统协调器监控所有并行线程，并可进行资源重新分配或共享关键发现。

### **4\. 外循环：先进记忆系统：从经验中学习**

* **4.1. 混合记忆架构**: 短期、情景、语义、程序化记忆。  
* **4.2. 目标导向型记忆检索**: 参数化记忆、情节控制。

### **5\. 系统交互与监控接口：Prometheus 控制塔**

本系统的核心交互与监控由一个统一的“控制塔”UI负责，旨在将人类专家从被动的“操作员”提升为主动的“总设计师”。其设计哲学、核心组件（并行进化沙盘、KPI仪表盘、情境式干预面板）与关键工作流的详细定义，请参见独立的《UI/UX设计稿.md》文档。

### **6\. 总结**

本项目旨在构建一个能够自我进化的智能生态。**v3.6的最终升级是用一个“人机协同的策略分叉”流程，取代了所有先前版本中关于如何生成多样性的复杂自主机制。** 通过将LLM定位为“战略架构师”进行广度生成，并将最终的决策权和创造力补充交由人类专家，我们构建了一个更简单、更鲁棒、也更强大的系统。这个框架完美地结合了机器的计算能力和人类的深层智慧，为解决真正开放和困难的问题提供了最坚实的基础。

另外，搜索引擎默认优先使用gemini的Google search Grounding，这个grounding部分不要使用全局的langchain，langgraph框架，直接使用genai SDK，方便search结果的metadata的传输，添加metadata处理的逻辑，通过标准的引用将可能需要的搜索链接引用回传回来

未来的可能改进：将思维树的波束搜索改为思维图中的搜索；参考eigen-1， 将外置向量经验库与搜索结果知识库合并。考虑将内置置信度改为同行评议式
