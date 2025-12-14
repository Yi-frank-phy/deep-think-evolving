# Deep Think Evolving - 任务拆解

## 架构演进相关任务

| 编号 | 任务 | 负责人 | 状态 | 关联文档 |
| ---- | ---- | ------ | ---- | -------- |
| T-016 | [Track A] 实现数学引擎 (KDE, Temp, UCB) 与单元测试 | Backend Agent | Done | spec.md §3.5 |
| T-017 | [Track A] 定义 DeepThinkState 与迁移 Architect 节点 | Backend Agent | Done | spec.md §4.1 |
| T-018 | [Track A] 实现 Judge 与 Evolution 节点 | Backend Agent | Done | spec.md §3.4, §3.5 |
| T-019 | [Track A] 实现 Research 与 Distiller 代理 (Search Grounding) | Backend Agent | Done | spec.md §3.2, §3.8 |
| T-020 | [Track A] 构建 LangGraph 工作流与运行脚本 | Backend Agent | Done | spec.md §2.1 |
| T-021 | 更新 spec.md 反映 LangGraph 多代理架构 (v2.0) | Spec Sync | Done | spec.md 全文 |
| T-022 | 增强 check_specs.py 验证代码-文档一致性 | Spec Sync | Done | spec.md §10.2 |
| T-023 | 创建 GitHub Actions SpecKit 合规工作流 | DevOps | Done | spec.md §10.2 |

## 基础设施任务

| 编号 | 任务 | 负责人 | 状态 | 关联文档 |
| ---- | ---- | ------ | ---- | -------- |
| T-001 | 维护 Spec Kit 文档：每次架构或流程变化时同步更新 `spec.md`/`plan.md`/`tasks.md` | 待定 | In Progress | 宪章·质量门禁 |
| T-002 | 为 `src/context_manager.py`、`src/diversity_calculator.py` 编写单元测试 | TDD Agent | Done | spec.md §7 |
| T-003 | 建立自动化演示脚本 | 待定 | Backlog | spec.md §9.2 |
| T-004 | 扩展 WebSocket 鉴权机制 | 待定 | Backlog | spec.md §5.2 |
| T-005 | 评估知识库持久化方案（向量数据库） | 待定 | Backlog | spec.md §6 |
| T-006 | 上下文历史截断策略配置化 | 待定 | Done | spec.md §4.1 |
| T-007 | 为 `search_google_grounding` 编写模拟测试 | Codex | Done | spec.md §3.2 |
| T-008 | 冒烟测试 `use_mock` 离线模式 | 待定 | Done | spec.md §9.2 |
| T-009 | PR 模板要求引用规范与任务 | 待定 | Done | spec.md §10.3 |
| T-010 | 分支治理与 main 保护规则 | 待定 | Done | plan.md |

## 历史完成任务

| 编号 | 任务 | 负责人 | 状态 | 关联文档 |
| ---- | ---- | ------ | ---- | -------- |
| T-011 | 定义验收日志格式与报告脚本 | Codex | Done | spec.md §9 (legacy) |
| T-012 | 整合 Google Grounding Search 功能 | Codex | Done | spec.md §3.2 |
| T-013 | 整合日志助手与验收脚本 | Codex | Done | spec.md §9 (legacy) |
| T-014 | 批量整合 `codex/*` 分支 | Codex | Done | 宪章·流程约束 |
| T-015 | 创建规范检查脚本 `check_specs.py` | Codex | Done | spec.md §10.2 |

## SpecKit 维护任务

| 编号 | 任务 | 负责人 | 状态 | 关联文档 |
| ---- | ---- | ------ | ---- | -------- |
| T-028 | 同步 spec.md 收敛条件文档 (entropy_change_threshold) | Spec Sync | Done | spec.md §2.2, §4.1 |
| T-029 | 修复 test_convergence.py 与规范一致性 | TDD Agent | Done | tests/ |
| T-030 | 配置 pytest-cov 测试覆盖率工具 | TDD Agent | Done | pytest.ini |
| T-031 | 为 context_manager.py 添加单元测试 | TDD Agent | Done | tests/test_context_manager.py |
| T-032 | 移除测试Mock依赖，使用真实API | TDD Agent | Done | tests/ |
| T-033 | 更新 StrategyNode 规范 (ucb_score, child_quota) | Spec Sync | Done | spec.md §3.3 |
| T-034 | 增强 check_specs.py 添加函数签名验证 | Spec Sync | Done | scripts/check_specs.py |
| T-035 | 实现分段取整 Boltzmann 分配 (<1四舍五入, >=1向上取整) | Backend | Done | evolution.py |
| T-036 | 添加温度耦合配置 (coupled/decoupled 模式) | Backend | Done | temperature_helper.py |

---

> 状态取值：`TODO`（待开始）、`In Progress`（进行中）、`Done`（完成）、`Backlog`（暂缓）。

## 版本历史

- **2025-12-13**: 清理过时PR任务(T-024~T-026), 新增 T-028~T-031 SpecKit维护任务
- **2025-12-12**: 新增 T-021 至 T-027，反映 SpecKit 完整集成工作
- **2025-12**: 更新架构演进任务状态 (T-016 至 T-020 标记为 Done)
- **2025-10**: 初始任务创建
