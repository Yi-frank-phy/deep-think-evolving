# **后端开发任务清单：普罗米修斯计划**

本文档根据《“自适应进化压力”下的“混合智能体”生态系统》需求文档及最新指令制定，旨在将设计蓝图分解为可执行的后端工程任务。

### **技术决策概要 (Technical Decisions Summary)**

根据我们的讨论，确认以下核心实现路径：

1.  **技术栈**: 后端将使用 **Python**，结合 **FastAPI** 框架（用于构建API和WebSocket服务）和 **LangChain/LangGraph**（用于编排Agent流程）。在需要对模型进行精细控制的场景（如动态温度、`responseSchema`），将直接使用 **Google GenAI SDK**。
2.  **`Value_Score` 生成**: `Value_Score` 将由“生成器”LLM在“繁殖”新步骤时，作为结构化输出的一部分一并返回，无需独立的评估Agent调用。
3.  **“概念”多样性计算**: 放弃硬编码的相似度阈值。我们将实现一个**基于嵌入向量余弦相似度的加权香农熵**计算方法，以更平滑、更精确地量化种群多样性。
4.  **外循环（记忆系统）**: 实现一个基于**RAG (Retrieval-Augmented Generation)** 的长期记忆系统。Agent在任务结束后将“经验笔记”存入文件系统，这些笔记被向量化后存入知识库，供后续任务检索和利用。

---

### **Area 1: 核心系统与编排器 (Core System & Orchestrator)**

这是整个系统的中枢神经，负责管理任务的生命周期、状态和各个模块间的通信。

-   [ ] **任务 1.1: 搭建项目基础框架**
    -   [ ] 初始化Python项目，集成FastAPI, LangChain/LangGraph, 和 Google GenAI SDK。
    -   [ ] 设置环境变量管理，确保 `API_KEY` 的安全加载。

-   [ ] **任务 1.2: 实现系统编排器 (System Orchestrator)**
    -   [ ] 设计并实现一个中央服务，用于接收新问题、创建和管理独立的“进化任务 (Evolutionary Run)”。
    -   [ ] 为每个任务实现状态机管理 (`PENDING_HIL`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`)。

-   [ ] **任务 1.3: 搭建实时通信层**
    -   [ ] 使用FastAPI建立一个WebSocket服务，用于向前端“控制塔”实时推送系统状态。
    -   [ ] 定义清晰的WebSocket事件协议 (`NODE_CREATED`, `NODE_STATUS_UPDATED`, `KPI_UPDATED`, `HIL_REQUIRED`) 并实现推送逻辑。

-   [ ] **任务 1.4: 设计并实现RESTful API**
    -   [ ] `POST /runs`: 创建一个新的进化任务，接收初始问题和配置（如 `T_max`）。
    -   [ ] `POST /runs/{run_id}/start`: 接收前端经HIL确认后的战略列表，启动并行搜索。
    -   [ ] `GET /runs/{run_id}`: 获取指定任务的当前完整状态（包括策略树和KPIs）。
    -   [ ] `POST /runs/{run_id}/intervention`: 接收前端的“启发式注入”指令。
    -   [ ] `POST /runs/{run_id}/pause` & `POST /runs/{run_id}/resume`: 实现任务的暂停与恢复。

---

### **Area 2: 内循环：并行进化搜索引擎 (Inner Loop: Parallel Evolutionary Search Engine)**

这是系统解决具体问题的核心实时引擎。

-   [ ] **任务 2.1: 实现“人机协同的策略分叉”流程**
    -   [ ] **2.1.1: “战略架构师”Agent**: 创建一个调用“战略架构师”LLM的模块。
        -   [ ] 严格使用`readme`中定义的System Prompt。
        -   [ ] 使用 `responseSchema` 强制输出为包含 `strategy_name`, `rationale`, `initial_assumption` 的JSON数组。
        -   [ ] 创建一个API端点 (e.g., `POST /runs/{run_id}/generate-strategies`) 触发此Agent。
    -   [ ] **2.1.2: 并行线程实例化**: 在 `POST /runs/{run_id}/start` 接口中，根据HIL确认后的战略列表，为每个战略创建初始根节点，并启动独立的异步工作单元（并行搜索线程）。

-   [ ] **任务 2.2: 实现线程内的在线进化算法**
    -   [ ] **2.2.1: 繁殖 (Propagation) 模块**:
        -   [ ] 创建一个“生成器”Agent，输入为父节点，输出多个“后代”节点。
        -   [ ] **【核心】** Agent的输出必须是结构化JSON，包含新步骤的`content`, `concept`, 和 `Value_Score`。
        -   [ ] **【核心】** 实现模型生成温度的动态耦合：LLM调用的`temperature`参数必须动态绑定到当前系统的实时温度 `T`。
    -   [ ] **2.2.2: “概念指纹”与加权熵计算模块**:
        -   [ ] 创建一个概念管理服务，用于缓存“概念”及其嵌入向量。
        -   [ ] 实现一个函数，输入新概念时，调用Gemini Embedding API获取向量。
        -   [ ] 实现**加权香农熵 `H(Concepts)`** 的计算逻辑，权重基于概念向量间的余弦相似度。
    -   [ ] **2.2.3: 评估与温度控制模块**:
        -   [ ] 实现 `Final_Score(c) = Value_Score(c) + C * Exploration_Bonus(c)` 的计算逻辑。`Exploration_Bonus`基于概念的稀有度。
        -   [ ] 实现自适应温度控制器：`T = T_max * (H(Concepts) / H_max)`。
    -   [ ] **2.2.4: 选择 (Selection) 与智能剪枝模块**:
        -   [ ] 实现基于Metropolis准则的概率性剪枝规则：以 `P = exp(-ΔScore / T)` 的概率接受分数较低的候选解。

-   [ ] **任务 2.3: 实现Google Search Grounding集成**
    -   [ ] 为需要外部信息的Agent，构建直接使用 **Google GenAI SDK** 的调用函数。
    -   [ ] 确保在配置中明确加入 `tools: [{googleSearch: {}}]`。
    -   [ ] 实现从 `response.candidates[0].groundingMetadata.groundingChunks` 中提取来源URI和标题的逻辑，并将其附加到对应节点的元数据中。

---

### **Area 3: 外循环：基于RAG的记忆系统 (Outer Loop: RAG-based Memory System)**

-   [ ] **任务 3.1: 搭建持久化记忆存储**
    -   [ ] 设计一个简单的文件系统结构，用于存储已完成任务的“经验笔记”（纯文本文件）。
    -   [ ] 实现一个Agent或模块，在任务成功结束后，能自动总结最高分路径的策略、关键决策点和使用的概念，并写入笔记。
-   [ ] **任务 3.2: 实现记忆向量化与检索**
    -   [ ] 建立一个后台进程或触发器，用于监控笔记文件的变化。
    -   [ ] 当新笔记产生时，自动读取、分块，并调用Gemini Embedding API进行向量化。
    -   [ ] 将文本块及其向量存入一个向量数据库 (e.g., ChromaDB, FAISS)。
-   [ ] **任务 3.3: 集成RAG到Agent工作流**
    -   [ ] 在任务开始时（例如，在“战略架构师”Agent运行前），根据当前问题，从向量数据库中检索最相关的历史经验。
    -   [ ] 将检索到的信息作为上下文注入到初始Prompt中，以引导Agent的思考。