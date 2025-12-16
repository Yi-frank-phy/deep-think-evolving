# Release Notes

## v2.1.0 (2025-12-16)

### 🐛 Bug Fixes

- **UCB 上确界修复**: 修正 UCB 计算公式，保证 `UCB >= Score`
  - Score 直接使用 Judge 评分 (0-1)，不再二次归一化
  - Exploration 项使用相对密度倒数平方根，归一化到 [0, 1]
  - 解决高维空间 (4096维) 数值不稳定问题

- **前端显示修复**: 修复 UCB 分数在前端显示为 0.00 的问题
  - Evolution 节点现在显式返回 `strategies` 列表
  - 确保 LangGraph 流式更新正确传递到前端

### 📚 Documentation

- 新增 [数学严谨性证明](./docs/math_proof_ucb.md)
  - 从方差基础定义推导 UCB 中不确定性度量的正确性
  - 论证归一化处理的数学合理性

- 更新 README.md
  - 修正 UCB 公式描述
  - 添加数学证明文档链接

### 🔧 Technical Details

**UCB 公式变更**:

```
旧: UCB = V_norm + c × sqrt(τ × (1 - density_norm))
新: UCB = Score + c × τ × Normalize(1/√p_rel)
```

**关键提交**:

- `4e23e07`: fix: UCB 正确实现上确界性质
- `4261f56`: fix: evolution.py 显式返回 strategies 列表

---

## v2.0 (2025-12)

- 重写为 LangGraph 多代理进化架构
- 新增动态报告生成和硬剪枝机制
- 详见 [spec.md](./docs/spec-kit/spec.md) §12

## v1.0 (2025-10)

- 初始版本（线性流水线）
