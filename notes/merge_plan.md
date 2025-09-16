# 分支合并实施计划

## 目标
- 将 `smoke-test` 分支的冒烟测试用例与 `feat` 功能分支整合，保证功能完整。
- 解决合并过程中的所有冲突，确保最终代码可运行、测试通过。

## Todo List
- [x] 梳理现有提交历史，确定 `feat` 与 `smoke-test` 对应的提交。
- [x] 将当前工作分支回退到 `feat` 最新提交，准备进行合并。
- [x] 执行 `smoke-test` 提交的合并操作，处理冲突。
- [x] 手动检查关键模块（`main.py`、`src/` 目录、`requirements.txt` 等）。
- [x] 运行必要的测试验证（`pytest -k smoke`）。
- [x] 更新文档/记录，提交代码。

## 关键信息记录
- `feat` 目标提交：`37a4cae`（Verify diversity calculation with mock data）。
- `smoke-test` 提交：`6c61319`（Add smoke tests for strategy pipeline）。
- 合并后需确认保留的文件：`README.md`、`pytest.ini`、`requirements.txt`、`tests/test_pipeline_smoke.py` 等。
- 测试依赖：需要 `GEMINI_API_KEY` 与本地 Ollama 服务；若缺失将自动跳过。
- 新增环境变量 `USE_MOCK_EMBEDDING` 支持在无 Ollama 时回退到随机嵌入，延续 smoke-test 分支的验证能力。
