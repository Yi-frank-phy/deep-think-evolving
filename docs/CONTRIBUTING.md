# 贡献指南

## 分支治理设置

### 启用自动删除临时分支
1. 打开 GitHub 仓库页面的 **Settings → General**。
2. 滚动到 **Pull Requests** 部分，勾选 **Automatically delete head branches**。
3. 保存设置后，已合并的 PR 会自动清理其源分支。

### 配置主干分支保护
1. 前往 **Settings → Branches**，在 **Branch protection rules** 中点击 **Add rule**。
2. 在 **Branch name pattern** 中输入 `main`。
3. 勾选以下选项以强化质量门禁：
   - **Require a pull request before merging**（可选启用最少审查者数量）。
   - **Require status checks to pass before merging**，并将 `specify check`、CI 测试等必需检查加入列表。
   - **Require branches to be up to date before merging**（避免落后主干）。
   - **Include administrators** 与 **Restrict who can push to matching branches**（视团队规模选择）。
4. 保存规则后，`main` 将禁止直接推送与强制更新。

## 提交流程提醒
- 在 PR 中引用 `docs/spec-kit/spec.md` 与 `docs/spec-kit/tasks.md` 相关章节，说明变更动机与验收标准。
- 按照 `.github/pull_request_template.md` 填写背景、测试与验收日志。
- 合并后手动确认临时分支已被删除（若自动删除失败），保持仓库整洁。
