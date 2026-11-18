---
name: finishing-branch
version: v1.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "功能开发完成、verification 与 code-review 通过后使用。处理最终验证、合并/PR 选项、工作树清理。触发词: 合并分支、收尾、提PR、清理分支。"
updated: 2026-08-13
depends_on: [git-commit, verification]
composes: []
---
# Finishing Branch


## 负责代理

`architect` — 分支收尾由架构师代理负责，确保合并、清理和版本管理规范。

## 何时使用

- 功能开发完成，所有任务已执行完毕
- `verification` 技能确认所有检查通过
- `code-review` 技能确认审查通过
- 准备将工作成果整合到主分支时

**触发关键词**: "合并"、"merge"、"提 PR"、"完成分支"、"清理分支"

## 前置条件

在进入此技能前，必须确认:
- ✅ 所有测试通过 (`verification` 技能确认)
- ✅ 代码审查通过 (`code-review` 技能确认)
- ✅ 无未提交的临时变更
- ✅ 分支名称和提交历史清晰

### 合并前硬性 Gate（三项，任一未过即阻断合并）

> 与 CI 的 rules-gate 阻断链一致，任何一项为 ❌ 都**禁止合并**，先修复再回到本检查点。

| Gate | 检查项 | 通过标准 | 状态 |
|------|--------|---------|------|
| **G1 验证通过** | 运行 `verification` 技能 | 全部测试通过，无失败用例（post-test 无 FAIL 检出） | ☐ |
| **G2 审查通过** | 运行 `code-review` 技能并产出 JSON | `findings` 为空或 `verdict` 为 `approve`，无未修复 `critical` | ☐ |
| **G3 工作区干净** | `git status` / `git diff` | 无未提交变更，无临时文件，分支历史清晰 | ☐ |

**阻断规则**：
- 三项 Gate 全部为 ✅ 后方可进入「执行流程」的合并/提 PR 步骤。
- 任一 Gate 为 ❌ 时，先修复对应问题，重新跑 `verification` / `code-review`，不得强行合并。
- `code-review` 的机器可读 JSON（`docs/reviews/code-review-<YYYYMMDD>.json`）作为 G2 的客观凭证。

## 执行流程

### 1. 最终状态确认

```bash
# 检查分支状态
git status
git log --oneline -10

# 确认工作区干净
git diff
git diff --cached
```

### 2. 呈现选项

向用户展示以下选项:

#### 选项 A: 本地合并到主分支

```bash
git checkout main
git merge --no-ff <feature-branch> -m "feat: 合并 <feature-name>"
git branch -d <feature-branch>
```

适用于: 小团队、个人项目、快速迭代

#### 选项 B: 创建 Pull Request

```bash
git push origin <feature-branch>
# 通过 GitHub/GitLab 创建 PR
```

适用于: 团队协作、需要正式审查流程

#### 选项 C: 保留分支

保留当前分支不合并，等待后续决策。

适用于: 功能未完全完成、需要进一步验证

#### 选项 D: 丢弃分支

```bash
git checkout main
git branch -D <feature-branch>
```

适用于: 实验性分支、方向错误需要废弃

### 3. 用户决策

- 清晰展示每个选项的**适用场景和风险**
- 等待用户明确选择
- 执行用户选择的操作

### 4. 清理工作

合并或丢弃后:
- 删除本地分支 (如适用)
- 删除远程分支 (如适用)
- 确认工作区状态干净
- 汇报最终状态

## 硬性规则

- ✅ **测试未全部通过不得合并** — 这是底线
- ✅ **必须让用户做最终决定** — 不可替用户选择
- ✅ 合并前**必须确认工作区干净**
- ✅ 使用 `--no-ff` 保留合并历史 (选项 A)
- ✅ 提交信息遵循 **Conventional Commits** 规范
- ❌ 禁止在测试失败时合并
- ❌ 禁止不确认就删除分支
- ❌ 禁止 force push 到受保护的分支
- ❌ 禁止跳过 `verification` 和 `code-review` 直接合并

## 反模式

- ❌ 测试还有失败就直接 merge — 引入不稳定代码到主分支
- ❌ 不问用户直接 merge — 用户失去了最终决策权
- ❌ merge 后不清理分支 — 工作区越来越乱
- ❌ 使用 `git push --force` — 破坏团队协作历史
- ❌ 丢弃分支前不确认 — 可能丢失有价值的代码
