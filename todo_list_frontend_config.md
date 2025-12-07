# 前端配置功能 TODO List

> 基于后端实现的可配置参数，整理前端需要暴露的配置界面。

---

## 1. 进化引擎配置 (Evolution Engine)

### 1.1 收敛控制

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_iterations` | int | 10 | 最大迭代次数 |
| `entropy_threshold` | float | 0.1 | 熵收敛阈值 (低于此值停止) |
| `total_child_budget` | int | 6 | 每轮子节点总预算 |

**前端任务**:

- [ ] 添加"进化设置"面板
- [ ] 滑块/输入框: 最大迭代次数 (1-50)
- [ ] 滑块: 熵阈值 (0.01-1.0)
- [ ] 输入框: 子节点预算 (2-20)

---

### 1.2 温度控制

| 参数 | 类型 | 选项 | 说明 |
|------|------|------|------|
| `temperature_coupling` | string | "auto" / "manual" | 温度耦合模式 |
| `manual_llm_temperature` | float | 1.0 | 手动模式固定温度 |
| `t_max` | float | 2.0 | 最大温度 (用于归一化) |
| `c_explore` | float | 1.0 | UCB 探索系数 |

**前端任务**:

- [ ] 切换开关: Auto/Manual 温度模式
- [ ] 条件显示: Manual 模式下显示温度滑块 (0.0-2.0)
- [ ] 高级设置: T_max 和 c_explore

---

## 2. 模型选择 (Model Selection)

### 2.1 各 Agent 模型配置

| Agent | 环境变量 | 默认值 | 推荐选项 |
|-------|----------|--------|----------|
| Researcher | `GEMINI_MODEL_RESEARCHER` | gemini-1.5-flash | flash/pro |
| Distiller | `GEMINI_MODEL_DISTILLER` | gemini-1.5-flash | flash |
| Architect | `GEMINI_MODEL_ARCHITECT` | gemini-2.0-flash-thinking | thinking-exp |
| Judge | `GEMINI_MODEL_JUDGE` | gemini-1.5-flash | flash/pro |
| Propagation | `GEMINI_MODEL_PROPAGATION` | gemini-1.5-flash | flash |

**前端任务**:

- [ ] 下拉菜单: 每个 Agent 的模型选择
- [ ] 模型信息提示 (cost, speed, capability)
- [ ] "全部使用同一模型" 快捷选项
- [ ] 预设方案: "快速/经济" vs "深度/高质量"

---

### 2.2 思考预算

| 参数 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `thinking_budget` | int | 1024-24576 | Thinking 模型的 token 预算 |

**前端任务**:

- [ ] 滑块: 思考预算 (分档: 1K/4K/8K/16K/24K)
- [ ] 费用估算显示

---

## 3. 知识库 (Knowledge Base)

### 3.1 知识库管理

**前端任务**:

- [ ] 知识库历史列表查看
- [ ] 单条经验详情展开
- [ ] 按类型筛选 (教训/成功模式/洞见)
- [ ] 删除/编辑经验条目
- [ ] 导出知识库 (JSON)

### 3.2 知识库设置

| 参数 | 类型 | 说明 |
|------|------|------|
| `KNOWLEDGE_BASE_PATH` | string | 存储路径 |
| 自动向量化 | bool | 是否自动向量化新条目 |

**前端任务**:

- [ ] 知识库路径显示/选择
- [ ] 知识库统计 (条目数/类型分布)

---

## 4. 实时监控显示 (Dashboard)

### 4.1 进化状态监控

**前端任务**:

- [ ] 实时显示当前迭代次数
- [ ] 温度仪表盘 (τ 值 0-2)
- [ ] 熵趋势图 (随迭代变化)
- [ ] 活跃策略数量指示

### 4.2 策略树可视化

**前端任务**:

- [ ] 策略树结构图 (父子关系)
- [ ] 节点状态颜色编码:
  - 🟢 active
  - 🔴 pruned
  - 🔵 expanded
- [ ] 节点点击查看详情
- [ ] 子节点配额显示 (Boltzmann 分配)

### 4.3 Judge 知识库写入通知

**前端任务**:

- [ ] Toast 通知: "Judge 记录了一条教训"
- [ ] 点击跳转到知识库详情

---

## 5. Human-in-the-Loop (Future)

### 5.1 人类干预接口

**前端任务**:

- [ ] 断点条件配置 (连续N轮无改善)
- [ ] 干预弹窗 (WebSocket 推送)
- [ ] 人类输入表单
- [ ] 干预历史记录

---

## 优先级

| 优先级 | 模块 | 原因 |
|--------|------|------|
| P0 | 2.1 模型选择 | 用户最常调整 |
| P0 | 4.2 策略树 | 核心可视化 |
| P1 | 1.1 收敛控制 | 影响运行时长 |
| P1 | 1.2 温度控制 | 影响探索/利用 |
| P2 | 3.x 知识库 | 外循环功能 |
| P2 | 4.1 监控 | 运行过程可视化 |
| P3 | 5.x HIL | 高级功能 |

---

## API 端点需求

后端需要提供以下 API 供前端调用:

```
POST /api/config          # 更新运行配置
GET  /api/config          # 获取当前配置
GET  /api/models          # 获取可用模型列表
GET  /api/knowledge-base  # 获取知识库条目
DELETE /api/knowledge-base/{id}  # 删除条目
GET  /api/status          # 获取当前进化状态 (WebSocket 更优)
```
