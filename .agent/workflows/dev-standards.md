---
description: deep-think-evolving 项目开发规范
---

# SpecKit 驱动的 TDD 开发规范

## 核心原则

**顺序必须是 Spec → Test → Code，绝对不能反过来！**

```
1. 更新 spec.md (定义规范)
2. 写测试 (基于规范，此时预期失败)
3. 实现代码 (使测试通过)
4. 验收 (测试通过 = 规范满足)
```

## 开发流程

### Phase 1: 规范先行

// turbo

```bash
# 1. 先更新 spec.md 定义新功能规范
# 2. 运行 check_specs 确认规范格式正确
python scripts/check_specs.py
```

### Phase 2: 测试先行

// turbo

```bash
# 3. 基于规范写测试（此时测试应该失败）
pytest tests/test_xxx.py -v --tb=short
# 预期：FAILED (因为代码还没实现)
```

### Phase 3: 实现代码

```bash
# 4. 实现代码使测试通过
# 5. 再次运行测试验证
```

### Phase 4: 验收

// turbo

```bash
# 6. 全量测试通过
pytest -v --tb=short

# 7. SpecKit 合规检查
python scripts/check_specs.py
```

## 提交前检查清单

1. [ ] spec.md 已先于代码更新
2. [ ] 测试基于规范编写（非事后补充）
3. [ ] 所有测试通过
4. [ ] check_specs.py 通过
