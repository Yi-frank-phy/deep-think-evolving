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

3.2.2. 【v3.6 核心更新】新增：人机协同的策略分叉 (Human-in-the-Loop Strategy Forking)  
此机制由系统协调器 (System Orchestrator)（见5.1节）在关键节点（如初始步骤或搜索停滞时）启动和管理：

1. **架构师生成 (Architect Generation)**: 系统协调器调用一个专用的“**战略架构师 (Strategy Architect)**”LLM，其任务不是解决问题，而是生成一份包含所有可能方向的“战略蓝图”。

   【优化版提示词】  
   System Prompt:  
   你是一位'战略系统架构师' (Strategic Systems Architect)。你的主要职能是对复杂问题进行元层面分析。你不直接解决问题，而是识别并绘制出所有通往解决方案的基础战略路径。你的分析必须广博、多样，并专注于概念上截然不同的方法。  
   **User Prompt**: 分析以下问题状态：  
   \[问题状态：包含完整的上下文、当前进展，以及遇到的具体困境或决策点\]  
   你的任务是生成一份详尽的、包含所有从此状态出发的、相互排斥的战略方向清单。对每一个方向，请提供一个简洁的名称、清晰的理由和其所依赖的核心假设。  
   **约束**:

   1. ## **最大化多样性: 策略之间必须存在根本性差异。避免对同一核心思想的微小改动。**

   2. **仅限高层次**: 不要提供详细的程序步骤。专注于“做什么”和“为什么”，而不是“怎么做”。  
   3. **保持中立**: 不要对策略表示任何偏好或进行评估。你的角色是绘制蓝图，而非评判。

      **请将结果输出为单一的JSON对象数组。每个对象必须包含以下三个键**:

   * strategy\_name: 一个简短的、描述性的中文标签 (例如, "几何构造法")。  
   * rationale: 一句解释该策略核心逻辑的中文描述。  
   * initial\_assumption: 一句描述该策略若要可行所必须依赖的关键假设的中文描述。  
2. **人类确认与迭代 (Human Confirmation & Iteration)**: “战略架构师”生成的JSON输出，会通过**人类在环 (HIL) 接口**（见5.2节）呈现给人类专家。专家可以：  
   * **确认 (Confirm)**: 勾选所有他们认为可行或值得探索的战略方向。  
   * **修改 (Modify)**: 编辑某个策略的描述或其核心假设。  
   * **补充 (Add)**: 手动添加LLM未能想到的全新战略方向。  
   * 否决 (Reject): 要求系统基于新的指示重新生成蓝图。  
     这个“建议-返工-修改”的循环会一直持续，直到人类专家对战略分叉的最终方案感到满意。  
3. **强制并行实例化 (Forced Parallel Instantiation)**: 系统协调器接收到**经人类最终确认**的战略方向列表后，为每一个方向启动一个**全新的、独立的并行搜索线程**，并施加硬约束。

3.2.3. 【v3.5 核心修正】线程内的在线进化 (Intra-Thread Online Evolution)  
每一个并行线程内部，都独立运行基于种群熵的在线进化搜索算法。此算法是实现无偏UCB估计的关键。  
**3.2.3.1. 算法流程 (Algorithm Flow)**  
在每个推理步骤 (depth d):

1. **繁殖 (Propagation)**: 对当前种群（大小为k的波束）中的每个候选路径，调用“生成器”LLM，产生多个潜在的下一步，形成一个更大的“后代池 (offspring pool)”。  
2. 评估 (Evaluation): 对“后代池”中的每一个新候选者 c，计算其最终适应度分数：  
   Final\_Score(c) \= Value\_Score(c) \+ C \* Exploration\_Bonus(c)  
3. **选择 (Selection)**: 从“后代池”中，选择Final\_Score最高的k个候选者，形成深度为d+1的新一代种群（新波束）。

**3.2.3.2. 空间熵与探索奖励 (Spatial Entropy & Exploration Bonus)**

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

**2. 多样性加权 UCB (Diversity-Weighted UCB)**
$$ Score(x) = \tilde{V}(x) + c \cdot T \cdot \sigma_{local}(x) $$
* $\tilde{V}(x)$: 归一化的价值评分 (Normalized Value Score)。
* $T$: 由全局熵决定的“探索幅度” (Standard Deviation Scale)。
* $\sigma_{local}(x)$: 候选解 $x$ 的**局部唯一性 (Local Uniqueness)**。
    $$ \sigma_{local}(x) = \min_{y \in Population, y \neq x} (1 - \text{sim}(v(x), v(y))) $$
    *注：此项奖励那些“离现有种群最远”的新解。*

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
