# Deep Think Evolving - 任务拆解

| 编号 | 任务 | 负责人 | 状态 | 关联文档 |
| ---- | ---- | ------ | ---- | -------- |
| T-001 | 维护 Spec Kit 文档：每次架构或流程变化时同步更新 `spec.md`/`plan.md`/`tasks.md` | 待定 | TODO | 宪章·质量门禁 |
| T-002 | 为 `src/context_manager.py`、`src/diversity_calculator.py` 编写单元测试，覆盖主要分支 | 待定 | TODO | 规范 §3.2/§3.3 |
| T-003 | 建立自动化脚本或文档，演示如何运行 `main.py` 全流程并采集输出 | 待定 | TODO | 规范 §3.4 |
| T-004 | 扩展 `server.py` WebSocket，增加客户端订阅过滤或鉴权机制 | 待定 | Backlog | 规范 §3.5 |
| T-005 | 评估知识库持久化方案（向量数据库或外部存储），形成提案 | 待定 | Backlog | 规范 §5 |
| T-006 | 将上下文历史截断策略写入规范并实现配置化（衔接 PR#14 建议） | 待定 | TODO | 规范 §3.2 |
| T-007 | 为 `search_google_grounding` 设计可注入客户端并编写模拟测试 | 待定 | Done | 规范 §3.3 |
| T-008 | 为策略冒烟测试提供 `use_mock`/离线模式并在 CI 中启用 | 待定 | TODO | 规范 §3.4 |
| T-009 | 编写 Codex/人工协同的 PR 模板，要求引用 `spec.md`/`tasks.md` 并记录测试 | 待定 | TODO | 宪章·流程约束 |
| T-010 | 制定分支治理手册：合并后删除临时分支并设置 main 保护规则 | 待定 | TODO | 计划 §风险缓解 |
| T-011 | 定义验收日志格式与自动报告脚本，支撑非开发者验收 | 待定 | TODO | 规范 §3.4 |

> 状态取值建议：`TODO`（待开始）、`In Progress`（进行中）、`Done`（完成）、`Backlog`（暂缓）。
