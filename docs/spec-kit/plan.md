# Deep Think Evolving - 实施计划

## 里程碑 1：规范基线完善

- 审阅 `rules.md`，将约束迁移至宪章并补充质量门禁。
- 建立 `.speckit/` 配置与 `docs/spec-kit/` 文档结构。
- 更新 README，记录 Spec Kit 使用方式与自检命令。

## 里程碑 2：现有架构梳理

- 分析 `src/` 模块、`main.py` 流水线与 `server.py` WebSocket 逻辑。
- 在 `spec.md` 中描述模块职责、数据流与接口约束。
- 在 `tasks.md` 中拆解后续迭代任务，为进一步开发留出挂载点。

## 里程碑 3：质量与运行保障

- 定义 `specify check` 作为基础质量门禁，确保工具链可用。
- 记录运行流水线与 WebSocket 服务的指令，方便演示。
- 在 CI/本地新增 `pytest -m smoke` 离线冒烟用例，验证 `use_mock` 流程不依赖外部服务。
- 后续若引入新功能，需在 PR 中同步更新规范与任务列表。

## 里程碑 4：PR 积压清理与流程固化

- 根据《项目综合分析报告》梳理未合并 PR，补齐缺失的测试与规范文档后再合入。
- 将上下文历史限制、Google 搜索助手、冒烟测试离线模式等需求拆分为独立任务，指派给 Codex 代理。
- 建立 PR 模板与分支治理准则，确保合并后自动删除临时分支并开启 main 保护规则。
- 设计面向架构师的验收日志/报告脚本，使验收仅依赖终端输出即可完成。

### 分支治理

1. **自动删除临时分支**
   - GitHub 仓库 **Settings → General → Pull Requests** 中勾选 “Automatically delete head branches”。
   - 在项目例会上确认该选项保持开启，必要时在 PR 模板中提醒合并人核对（见 `.github/pull_request_template.md`）。
2. **Main 分支保护规则**
   - 进入 **Settings → Branches**，为 `main` 新增 Branch protection rule。
   - 启用以下约束：至少一名审查者、禁止强制推送、在合并前通过 `specify check`、`pytest`、`pytest -m smoke`、`npm run test` 等必需状态检查。
   - 如仓库启用 Required Conversation Resolution，需在回归时再次确认该设置未被关闭。
3. **PR 质量门禁**
   - 要求所有 PR 使用统一模板，明确引用 `docs/spec-kit/spec.md` / `docs/spec-kit/tasks.md` 的章节编号及测试日志。
   - 评审时核对模板勾选项与日志内容，确保验收信息可追踪；若缺失则标记为变更请求。

## 风险与缓解

- **外部 API 依赖**：Gemini/Ollama 不可用时需准备降级方案；目前 `generate_summary` 已提供本地回退。
- **知识库膨胀**：定期清理 `knowledge_base/`，或引入滚动归档策略。
- **多人协作**：要求 PR 引用宪章与规范，降低信息错位风险。

## 里程碑 5：动态报告生成与硬剪枝 (2025-12-14)

### 设计理念

**报告 = 剪枝信号**。被综合的策略立即硬剪枝，价值通过两条路径保留：

1. **报告** - 综合的结论和洞见
2. **向量数据库** - 分支选择逻辑、经验、推理过程

### 实施内容

- 移除固定 `Writer` 节点，改为 Executor 动态执行综合任务
- Architect 通过 `strategy_id=null` 触发综合任务
- 综合后硬剪枝 (`status="pruned_synthesized"`)
- 归档到知识库 (`write_strategy_archive`)

### 优势

- 防止上下文腐烂 (Context Rot)
- 降低 Token 成本
- 保留所有有价值信息

### 关联任务

- T-037 至 T-044

## 后续规划指引

- 扩展测试覆盖率，建议为上下文管理与 WebSocket 编写单元/集成测试。
- 评估是否需要持久化存储（如 SQLite/Vector DB），并在 Spec Kit 文档中预先描绘演进路径。
