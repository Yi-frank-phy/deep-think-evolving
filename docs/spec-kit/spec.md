# Deep Think Evolving - 系统规范

## 1. 背景与目标
Deep Think Evolving 是一个多代理研究助理原型，通过 Gemini 生成策略、Ollama 嵌入向量，并将知识沉淀至本地知识库。该规范总结当前能力与预期范围，为后续迭代提供基线。

## 2. 需求概述
- **策略生成**：调用 `src/strategy_architect.py` 的 `generate_strategic_blueprint`，基于输入问题生成多条研究策略，返回 JSON 结构（名称、假设、行动步骤等）。
- **上下文管理**：`src/context_manager.py` 负责线程化管理推理日志，支持创建上下文、写入步骤、生成总结与长期反思。
- **向量化与多样性分析**：`src/embedding_client.py` 通过本地 Ollama 接口计算策略向量；`src/diversity_calculator.py` 使用余弦相似度矩阵衡量策略差异度。
- **流水线执行**：`main.py` 组织上述模块完成端到端流程，输出策略列表、相似度矩阵与总结结果。
- **知识库推送**：`server.py` 暴露 FastAPI WebSocket，实时将 `knowledge_base/` 中的反思 JSON 推送到前端。

## 3. 功能性需求
1. **策略生成接口**
   - 输入：自然语言描述的“问题状态”。
   - 输出：至少一条策略对象，每条包含 `strategy_name`、`rationale`、`initial_assumption`、`milestones` 等字段。
   - 失败处理：若 Gemini API 不可用，需记录错误并终止流水线。
2. **上下文记录**
   - 能够为每个策略创建独立目录，存储 `prompt.md`、`history.log`、总结与反思文件。
   - `append_step` 需保证写入 JSONL 格式，历史默认最多保留 50 条，可通过环境变量 `CONTEXT_HISTORY_LIMIT` 配置为正整数。
   - `generate_summary` 在缺少 API Key 时应提供本地回退摘要。
3. **嵌入与相似度**
   - `embed_strategies` 使用 `embedding_client.py` 调用本地服务，返回含 `embedding` 数组的策略。
   - `calculate_similarity_matrix` 使用 NumPy 计算余弦矩阵，支持空列表与维度不一致的防御性处理。
   - `search_google_grounding` 提供 Google 搜索 Grounding 能力：
     - 通过 Google GenAI SDK 的 `googleSearch` 工具检索来源，函数需支持传入客户端工厂以便测试时注入模拟对象。
     - 解析 `groundingMetadata.groundingChunks`，返回包含 `uri`、`title`、`snippet` 的引用列表，并保证原始策略结构附带引用字段。
     - 当 `use_mock`/`test_mode` 为真或外部依赖不可用时返回空引用，同时记录警告日志，保持流程可离线运行。
4. **流水线输出、离线模式与验收支持**
   - `main.py` 需打印关键状态，确保开发者可观察执行进度；在关键节点调用 `append_step` 记录元数据。
   - 流水线结束时，根据相似度结果决定是否触发 `record_reflection`，并将文件写入 `knowledge_base/`。
   - 提供 `use_mock`/`test_mode` 配置以跳过 `validate_api_key`，使用内置假实现生成最小可验证输出，保证 `pytest -m smoke` 在缺乏外部服务时可复现。
   - 日志助手：核心模块通过 `logging_helper`（或等效封装）输出 `[Spec-OK]` 前缀的关键事件，供验收脚本解析；工具需允许注入自定义记录器，避免破坏现有日志级别。
   - 验收报告脚本：`scripts/generate_acceptance_report.py` 读取日志与测试结果生成摘要，输出 JSON/Markdown，并在无日志时给出友好提示。
5. **WebSocket 服务**
   - WebSocket 端点 `/ws/knowledge_base` 首次连接时发送全量快照，后续按文件系统变更推送 `update/delete` 事件。
   - 提供 `/health` GET 接口用于探活。

## 4. 非功能性要求
- **可执行性**：`requirements.txt` 覆盖 FastAPI、NumPy 等依赖，需在 README 中提供运行指令。
- **可观测性**：关键模块记录日志或打印信息，方便排障；WebSocket 服务需捕获异常并关闭连接。
- **可扩展性**：策略与知识库结构采用 JSON，便于后续集成数据库或前端。
- **本地隐私**：知识库文件保存在仓库 `knowledge_base/` 目录，避免上传敏感数据。

## 5. 开放问题
- Gemini 与 Ollama API Key/模型版本如何在部署环境中安全注入。
- 需定义正式的测试套件，覆盖上下文管理与 WebSocket 推送逻辑。
- 知识库的版本管理策略与清理机制尚未确定。
