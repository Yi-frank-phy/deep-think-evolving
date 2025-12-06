# Deep Think Evolving - 任务拆解

| 编号 | 任务 | 负责人 | 状态 | 关联文档 |
| ---- | ---- | ------ | ---- | -------- |
| T-001 | 维护 Spec Kit 文档：每次架构或流程变化时同步更新 `spec.md`/`plan.md`/`tasks.md` | 待定 | TODO | 宪章·质量门禁 |
| T-002 | 为 `src/context_manager.py`、`src/diversity_calculator.py` 编写单元测试，覆盖主要分支 | 待定 | TODO | 规范 §3.2/§3.3 |
| T-003 | 建立自动化脚本或文档，演示如何运行 `main.py` 全流程并采集输出 | 待定 | TODO | 规范 §3.4 |
| T-004 | 扩展 `server.py` WebSocket，增加客户端订阅过滤或鉴权机制 | 待定 | Backlog | 规范 §3.5 |
| T-005 | 评估知识库持久化方案（向量数据库或外部存储），形成提案 | 待定 | Backlog | 规范 §5 |
| T-006 | 将上下文历史截断策略写入规范并实现配置化（衔接 PR#14 建议） | 待定 | Done | 规范 §3.2 |
| T-007 | 为 `search_google_grounding` 设计可注入客户端并编写模拟测试（`tests/test_google_grounding.py`） | Codex Integration Pod | Done | 规范 §3.3 |
| T-008 | 为策略冒烟测试提供 `use_mock`/离线模式并在 CI 中启用 | 待定 | TODO | 规范 §3.4 |
| T-009 | 编写 Codex/人工协同的 PR 模板，要求引用 `spec.md`/`tasks.md` 并记录测试 | 待定 | Done | 宪章·流程约束 |
| T-010 | 制定分支治理手册：合并后删除临时分支并设置 main 保护规则 | 待定 | Done | 计划 §风险缓解 |
| T-011 | 定义验收日志格式与自动报告脚本，支撑非开发者验收 | Codex Integration Pod | Done | 规范 §3.4 |
| T-013 | 整合 `codex/add-logging-helper-and-generate-acceptance-report` 分支，统一日志/验收脚本规范 | Codex Integration Pod | Done | 规范 §3.4 |
| T-012 | 整合 `codex/implement-google-grounding-search-functionality` 分支，保留主干规范并补充搜索助手条款 | Codex Integration Pod | Done | 规范 §3.3 |
| T-014 | 批量整合其余 `codex/*` 分支，记录冲突清单并同步规范/任务状态 | Codex Integration Pod | Done | 宪章·流程约束 |
| T-015 | 创建规范检查脚本 `scripts/check_specs.py` 以自动验证文档一致性 | Codex Integration Pod | Done | 规范 §3.4 |
| T-016 | [Track A] 实现数学引擎 (KDE, Temp, UCB) 与单元测试 | Backend Agent | Done | Readme §3 |
| T-017 | [Track A] 定义 DeepThinkState 与迁移 Architect 节点 | Backend Agent | Done | Readme §3 |
| T-018 | [Track A] 实现 Judge 与 Evolution 节点 | Backend Agent | Done | Readme §3 |
| T-019 | [Track A] 实现 Research 与 Distiller 代理 (Search Grounding) | Backend Agent | Done | Readme §3 |
| T-020 | [Track A] 构建 LangGraph 工作流与运行脚本 | Backend Agent | Done | Readme §3 |

> 状态取值建议：`TODO`（待开始）、`In Progress`（进行中）、`Done`（完成）、`Backlog`（暂缓）。

## 冲突合并备注

- 2024-05：合并 `codex/add-logging-helper-and-generate-acceptance-report` 时，保留了 `SpecLogger` `[Spec-OK]` 前缀输出以及验收报告脚本对缺失日志的兼容性要求，确保主干文档与实现保持一致。
- 2025-11：清理了过时的远程分支 `origin/52eajn-ctrategic-blueprintts-for-st`，确认主干为最新状态。
