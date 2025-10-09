# Codex 协作任务拆解（Deep Think Evolving）

以下任务依据《deep-think-evolving 项目综合分析报告》整理，面向 Codex/AI 代理执行。每项均给出目标、主要步骤与交付物，方便并行推进。完成后需在 PR 中引用 `docs/spec-kit/spec.md` 与 `docs/spec-kit/tasks.md` 中对应条目，并附带自动化测试或验证结果。

## 启动工单（2024-Q4 Codex 分支整合）

- **任务编号**：T-012、T-013、T-014 已在 `tasks.md` 中标记为 `In Progress`，由 Codex Integration Pod 负责执行。
- **启动要求**：
  1. 各负责人应在整合分支创建后 24 小时内更新冲突清单，必要时在本文件“任务 F”下补充备注。
  2. 每次提交 PR 须附带 `specify check`、`pytest`、`pytest -m smoke`、`npm run test` 的最新日志，并引用相应条款。
  3. 如需额外资源或跨团队协同，请在项目看板上以 `[Codex-Integration]` 标签登记并同步会议信息。


## 任务 A：上下文历史截断配置化（对应 T-006）
- **目标**：将历史限制写入配置并同步规范，确保 `ContextManager` 默认遵循 Speckit 要求。
- **建议步骤**：
  1. 在 `config` 或模块内新增常量/配置项，允许通过环境变量覆盖历史长度。
  2. 更新 `spec.md` §3.2，明确默认值与可配置方式。
  3. 为 `_enforce_history_limit` 编写单元测试，覆盖“历史超限被截断”的情形。
- **交付物**：代码更新、规范文档、测试报告（`pytest` 片段）。

## 任务 B：Google 搜索助手可测试化（对应 T-007）
- **目标**：为 `search_google_grounding` 提供依赖注入与模拟，补齐测试空白。
- **建议步骤**：
  1. 将 Google 客户端封装为接口或可传入的工厂。
  2. 在 `tests/` 中新增针对解析逻辑的单元测试，覆盖成功、API 错误、空结果等场景。
  3. 更新 README 与 `spec.md`，说明模拟用法和测试命令。
- **交付物**：重构后的模块、测试文件、文档增补、`pytest -k grounding` 运行记录。

## 任务 C：策略冒烟测试离线模式（对应 T-008）
- **目标**：让 `tests/test_strategy_pipeline.py::test_smoke_pipeline` 在缺少外部服务时仍可运行，纳入 CI。
- **建议步骤**：
  1. 复用 `use_mock` 开关，或增加测试专用配置，绕过真实 API。
  2. 在 `pytest.ini` 注册 `smoke` 标记，并在 CI 文档中说明运行方法。
  3. 设计至少一个断言验证管线产出（非仅运行成功）。
- **交付物**：测试更新、配置说明、CI 运行截图或日志。

## 任务 D：PR 流程与模板强化（对应 T-009、T-010）
- **目标**：规范 PR 流程，确保引用 Speckit 文档并在合并后自动清理分支。
- **建议步骤**：
  1. 在 `.github/pull_request_template.md`（若不存在则新建）编写模板，包含“关联规格条款”“测试命令”等栏目。
  2. 在 `docs/spec-kit/plan.md` 增加“分支治理”章节，列出删除临时分支、启用 main 保护的要求。
  3. 如需，编写脚本或文档指导如何启用 GitHub Branch Protection 与自动删除分支设置。
- **交付物**：PR 模板文件、计划文档更新、流程说明。

## 任务 E：验收日志与报告脚本（对应 T-011）
- **目标**：让非开发者能够通过终端输出/脚本完成验收。
- **建议步骤**：
  1. 设计统一的日志格式或关键字（如 `[Spec-OK]`），在 `main.py` 和关键模块中实施。
  2. 新增脚本 `scripts/generate_acceptance_report.py`（建议）读取日志/测试结果生成摘要。
  3. 在 `docs/` 增补《验收指南》，列出运行命令与预期输出。
- **交付物**：日志规范实现、脚本、文档与示例输出。

## 任务 F：Codex 分支冲突整合
- **目标**：为所有 `codex/*` 特性分支创建整合任务，先对齐主干规范，再解决冲突并补齐测试/文档，确保迁移到主干时保持规范一致性。
- **通用要求**：
  1. 执行 `git fetch --all --prune` 后列出 `codex/*` 远程分支，登记负责人、预估时间并同步到任务台账（对应 T-014）。
  2. 每个分支基于 `integration/<branch-name>` 创建整合分支，并在该分支执行 `git merge origin/main`。
  3. 使用 `git status` 与 `git diff --name-only --diff-filter=U` 记录冲突文件及成因，在任务说明或 PR 描述中列出。
  4. 解决冲突时优先保留主干新增规范条款（如 `CONTEXT_HISTORY_LIMIT`、离线模式说明），再合入特性分支的新需求，必要时更新 `docs/spec-kit/spec.md`、相关 README 与配置文件。
  5. 合并完成后运行 `specify check`、`pytest`、`pytest -m smoke`、`npm run test`，并收集日志作为质量门禁记录。
  6. 更新 `docs/spec-kit/tasks.md` 中对应任务的状态（如 T-007、T-011），注明整合说明与测试结果链接。

### F-1：整合 `codex/implement-google-grounding-search-functionality`（对应 T-012）
- **步骤聚焦**：
  - 整合分支命名建议 `integration/codex-google-grounding`。
  - 在 `spec.md` §3.3 与 §3.4 中补充 Google Grounding 搜索助手的接口、配置与测试约束。
  - 记录冲突对 `spec.md`、`tasks.md`、实现文件的影响，并在 PR 中说明保留主干条款的处理。
- **交付物**：合并后的代码、更新的规范条款、冲突清单、完整测试日志、`tasks.md` 中 T-007=Done。

### F-2：整合 `codex/add-logging-helper-and-generate-acceptance-report`（对应 T-013）
- **步骤聚焦**：
  - 整合分支命名建议 `integration/codex-acceptance-report`。
  - 在 `spec.md` §3.4 及相关章节记录日志助手与验收报告脚本的行为，确保与主干条款兼容。
  - 如 README 有使用说明，需同步更新并注明离线/历史截断要求。
- **交付物**：合并后的代码、规范更新、测试日志、`tasks.md` 中 T-011=Done 并附整合说明。

### F-3：整合剩余 `codex/*` 分支（对应 T-014）
- **步骤聚焦**：
  - 参照 F-1/F-2 的流程，为每个分支建立专属整合分支与冲突清单。
  - 若冲突涉及规范条款，需在 `spec.md` 中建立附录或新增章节，以免覆盖主干更新。
  - 将执行与结果记录在任务看板或本文件附录，保持可追踪性。
- **交付物**：整合分支的冲突处理记录、更新后的规范/文档、完整测试日志、任务台账更新截图或链接。

> **执行要求**：每个任务在开始前运行 `specify check` 与 `pytest` 确认基线，通过后再提交 PR。所有 PR 须引用本文件及 `tasks.md` 中的任务编号，并附带测试截图/日志，便于架构师验收。
