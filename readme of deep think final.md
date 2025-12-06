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
外循环进化出内循环的“进化规则”，内循环则在这些规则的指导下进化出具体问题的“解”。例如，外循环可以进化出用于Value_Score评估的最佳Prompt模板，或者调整探索项的平衡系数C。  
2.4. 【继承自v3.1】循环接口 - 启发式部署与验证协议 (Heuristic Deployment & Validation Protocol)  
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
| **选择 (Selection)** | 剪枝 (Pruning) | 基于 **UCB 式评分** 的排序，保留 Top-$k$。 |
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
    计算所有候选子节点的 **UCB 式评分**，选出新的 Top-$k$ 形成下一代种群。

3.2.3.4. 理论推导：从 KDE 到 UCB (Theoretical Derivation: From KDE to UCB)

**第一部分：从 KDE 到 种群微分熵 (Derivation of Entropy from KDE)**
这是宏观状态量的定义基础。

1. **概率密度场的构建**：
   假设我们在语义空间 $\Omega \subseteq \mathbb{R}^d$ 中观测到 $N$ 个策略样本 $\{v_1, \dots, v_N\}$。利用 Parzen-Rosenblatt 窗方法，空间中任意位置 $v$ 的概率密度 $\hat{p}(v)$ 为：
   $$
   \hat{p}(v) = \frac{1}{N} \sum_{i=1}^N K_h(v - v_i)
   $$
   其中 $K_h$ 为带宽为 $h$ 的归一化高斯核。

2. **种群熵 (Shannon Entropy) 的离散化计算**：
   根据香农定义，系统的微分熵为 $S = -\int \hat{p}(v) \ln \hat{p}(v) dv$。
   在实际计算中，我们采用蒙特卡洛积分的思路，利用已有的样本点 $v_i$ 作为采样点来近似该积分：
   $$
   S \approx -\frac{1}{N} \sum_{i=1}^N \ln \hat{p}(v_i)
   $$
   这个 $S$ 精确描述了当前种群在语义空间中的混乱度（Disorder）。

**第二部分：从 伪计数 到 UCB 探索项 (Derivation of UCB from Pseudo-counts)**
这是微观决策的统计学基础。

1. **从密度到有效伪计数 (Pseudo-counts)**：
   在连续空间无法计数，我们利用概率密度 $\hat{p}(v)$ 的物理含义：单位体积内的样本分布概率。
   定义特征体积元 $V_{unit}$（通常由带宽 $h$ 决定），则位置 $v$ 处的有效观测次数（Pseudo-count） $\hat{N}(v)$ 为：
   $$
   \hat{N}(v) \approx N_{total} \cdot \hat{p}(v) \cdot V_{unit}
   $$
   即：$\hat{N}(v) \propto \hat{p}(v)$。

2. **置信区间上界 (UCB) 的方差估计**：
   UCB 算法的核心是估计平均收益 $\mu$ 的置信上界：$\mu + c \cdot \sigma_{error}$。
   根据大数定律和中心极限定理，估计的标准误差 $\sigma_{error}$ 与样本量的平方根成反比：
   $$
   \sigma_{error} \propto \frac{1}{\sqrt{\hat{N}(v)}}
   $$

3. **代入推导**：
   将 $\hat{N}(v) \propto \hat{p}(v)$ 代入，得到严格的探索项形式：
   $$
   \text{Exploration Bonus} \propto \sqrt{\frac{\ln N_{total}}{\hat{p}(v)}} = \frac{\sqrt{\ln N_{total}}}{\sqrt{\hat{p}(v)}}
   $$
   这证明了探索项应与概率密度的平方根成反比 ($\frac{1}{\sqrt{p}}$)，而非对数关系。

3.2.4. 【新增】高级探索机制：基于熵的自适应温度与 UCB 式评分

**3.2.4.1. 理论背景与核心思想**

在统计力学中，正则系综在温度 $T$ 下的平衡分布为 $p(x) \propto \exp(V(x)/T)$，其中 $V(x)$ 为状态的价值（负能量）。该分布使得在给定平均价值约束下熵最大。温度 $T$ 控制着熵 $S$ 的大小：$T \to \infty$ 时分布趋于均匀，熵达到最大值 $S_{\max}$；$T \to 0$ 时分布集中于价值最高的状态，熵最小。

我们将当前种群视为一个正在演化的统计系统，其熵 $S$ 由上述核密度估计计算。我们希望随着演化的进行，温度逐渐降低以收敛到高价值区域，同时根据当前的熵动态调整冷却速率，实现成本导向的收敛。

**3.2.4.2. 数学形式化**

**1. 自适应温度 (Adaptive Temperature)**  
借鉴玻尔兹曼分布中 $T$ 与 $S$ 的单调关系，我们采用如下实用公式：
$$
T = T_{\max} \cdot \left( \min\left(1, \frac{S}{S_{\max}}\right) \right)^{\gamma}
$$
其中：

* $T_{\max}$ 是预设的最高温度，控制全局探索强度；
* $S_{\max}$ 为系统可能达到的最大熵（可通过均匀分布估计）；
* $\gamma \ge 1$ 为敏感系数，控制温度随熵下降的速度。
当熵 $S$ 较大时，温度保持高位以鼓励探索；当熵减小时，温度降低以加速收敛。

**2. 动态归一化 UCB 式评分 (Dynamic Normalized UCB‑like Score)**  
受多臂老虎机中上置信界（UCB）的启发，并结合上述我们可以推导出，将每个候选个体 $x$ 的评分设计为利用项与探索项的加权和：
$$
\text{Score}(x) = \frac{V(x) - V_{\min}}{V_{\max} - V_{\min} + \epsilon} + c \cdot T \cdot \frac{1}{\sqrt{\hat{p}(v(x))}}
$$
其中：

* $V(x)$ 为由 Judge Agent 给出的原始价值分；
* $V_{\min}$、$V_{\max}$ 分别为当前候选池中的最小、最大价值分；
* $\epsilon$ 为很小的正数（例如 $10^{-8}$），防止分母为零；
* $c$ 是一个常数超参数，用于调节探索项的相对权重；
* $\frac{1}{\sqrt{\hat{p}(v(x))}}$ 即为基于伪计数推导出的探索奖励项。

该公式确保了利用项被归一化到 $[0,1]$ 区间，而探索项与概率密度的平方根成反比，更符合统计学原理。

**3.2.4.3. 机制优势**

* **信息论基础**：使用微分熵和信息量作为多样性及探索奖励的度量，具有坚实的数学物理基础。
* **自适应收敛**：当种群多样性高 ($S$ 大) 时温度高，鼓励探索新区域；当种群趋同 ($S$ 减小) 时温度自动降低，加速收敛，节省计算资源。
* **自动平衡**：通过归一化利用项和基于概率密度的探索项，避免了量纲不匹配问题，且不需要手动设定复杂的冷却计划。

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
