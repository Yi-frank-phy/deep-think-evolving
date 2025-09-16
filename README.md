# Deep Think · Evolving

> 「普罗米修斯计划」的原型，实现多策略生成、上下文记忆与知识库可视化的全流程演示。

本仓库已脱离 Google AI Studio 的默认模板，改造成一个由 **Python 推理流水线 + 本地嵌入服务 + FastAPI 后端 + Vite 前端控制台** 组成的多模态实验环境。核心目标是验证“多策略并行探索 + 记忆反馈”这一混合智能体架构在复杂问题求解中的可行性。

## 功能总览

- **战略架构师 (src/strategy_architect.py)**：调用 Gemini 生成多条相互独立的高层策略蓝图。
- **上下文管理器 (src/context_manager.py)**：为每条策略创建独立的推理上下文、维护 SoC 日志，并生成摘要/长期反思。
- **嵌入与多样性分析 (src/embedding_client.py & src/diversity_calculator.py)**：通过本地 Ollama 嵌入模型量化策略间的相似度，形成余弦相似度矩阵。
- **全流程脚本 (main.py)**：串联以上模块，演示从问题描述到知识库落地的完整流程。
- **知识库 WebSocket 服务 (server.py)**：持续监测 `knowledge_base/`，将新增的反思条目推送给前端。
- **控制塔前端 (index.html + index.tsx)**：展示聊天面板与知识库流，支持实时查看策略反思及嵌入信息。

## 快速开始

### 1. 克隆与基础依赖

```bash
# Python 3.10+ 与 Node.js 18+ 环境
pip install -r requirements.txt
npm install
```

> 建议在虚拟环境中安装 Python 依赖，例如 `python -m venv .venv && source .venv/bin/activate`。

### 2. 配置外部服务

1. **Gemini API**：脚本依赖 `GEMINI_API_KEY` 环境变量。
   ```bash
   export GEMINI_API_KEY="your_google_api_key"
   ```
2. **Ollama 嵌入服务**：需要本地运行 Ollama，并提前拉取 `dengcao/Qwen3-Embedding-8B:Q4_K_M`。
   ```bash
   ollama pull dengcao/Qwen3-Embedding-8B:Q4_K_M
   ollama run dengcao/Qwen3-Embedding-8B:Q4_K_M --keep-alive
   ```
   默认端口 `http://localhost:11434` 可通过修改 `src/embedding_client.py` 调整。

### 3. 运行策略生成流水线

```bash
python main.py
```

该脚本将：
- 调用 Gemini 生成多条策略；
- 为每条策略创建独立的 `runtime_contexts/<strategy-id>` 目录；
- 调用 Ollama 获取嵌入并输出余弦相似度矩阵；
- 在 `knowledge_base/` 写入触发的长期反思（含嵌入向量）。

若缺少 API Key 或 Ollama 服务，脚本会在终端提示相应错误并安全退出。

### 4. 启动知识库 WebSocket 服务

```bash
uvicorn server:app --reload
```

该服务默认监听 `ws://localhost:8000/ws/knowledge_base`，实时推送 `knowledge_base/` 中的 JSON 文件变更。

### 5. 启动前端控制塔

```bash
npm run dev
```

- 访问 `http://localhost:5173` 查看控制面板。
- 如需连接远程后端，可在 `.env.local` 中配置：
  ```bash
  VITE_KNOWLEDGE_SOCKET_URL=wss://your-domain/ws/knowledge_base
  ```
  或者设置 `VITE_KNOWLEDGE_SOCKET_PORT` 覆盖默认端口。

## 目录结构

```text
.
├── main.py                    # 全流程演示脚本
├── server.py                  # FastAPI WebSocket 服务
├── requirements.txt           # Python 依赖
├── package.json               # 前端构建配置 (Vite + TypeScript)
├── src/
│   ├── context_manager.py     # 上下文/记忆管理
│   ├── strategy_architect.py  # 战略生成器
│   ├── embedding_client.py    # Ollama 嵌入客户端
│   └── diversity_calculator.py # 相似度矩阵计算
├── index.html / index.tsx     # 控制塔前端入口
├── runtime_contexts/          # 运行时自动生成的策略上下文
└── knowledge_base/            # 长期反思存储位置
```

> `runtime_contexts/` 与 `knowledge_base/` 在首次运行脚本或启动后端时会自动创建，可加入 `.gitignore` 避免提交运行时数据。

## 进一步阅读

- [`mcp-readme.md`](./mcp-readme.md)：介绍如何基于 MCP 扩展模型工具链。
- [`todo_list_backend.md`](./todo_list_backend.md)：后端演进计划与任务拆解。
- [`UI/UX设计稿.md`](./UI/UX设计稿.md)：控制塔界面设计参考。

如需向系统添加新的 Agent、策略评估指标或记忆机制，可从上述文档获取设计思路，并在 `src/` 目录中扩展相应模块。
