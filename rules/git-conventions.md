---
name: git-conventions
version: v1.2.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-14
description: Git 规范 — Conventional Commits、分支/PR 规范（RULE-011/012）
applies_to:
  agents: ['全部 Agent']
  phases: ['全程']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# Git 规范 (Git Conventions)
> **本文件落实**: RULE-011（不要安装未经确认的依赖）、RULE-012（不要直接修改 main/master 分支）

> **适用范围**: 通用原则，适用于所有项目。项目特定规范见项目根目录 `tech-stack.md`。

本文件定义项目中所有 Git 操作的强制性规范，AI 编码代理必须严格遵守。

## Commit Message 格式

使用 Conventional Commits 规范：

```
type(scope): description
```

### type（类型）

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 Bug |
| `refactor` | 重构（不改变行为） |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响逻辑） |
| `test` | 测试相关 |
| `chore` | 构建/工具链变更 |
| `perf` | 性能优化 |
| `ci` | CI/CD 配置变更 |
| `build` | 构建系统或外部依赖变更 |

### scope（范围，可选）

- 标明影响的模块或组件，如 `api`、`auth`、`frontend`

### description（描述）

- 语言遵循项目约定：默认英文；中文项目可使用中文，但同一仓库保持一致
- 使用祈使句，如 `add user login endpoint`
- 首字母小写，末尾不加句号

### 示例

```
feat(auth): add JWT token refresh endpoint
fix(api): resolve N+1 query in skill tree listing
refactor(database): extract common base model
```

### 归属 trailer（Agent 归因，v1.2.0 增补）

多工具/多代理共用同一 git 身份时（本仓实测：全部提交同属一人，授权链只能靠提交信息考古），提交级归因靠 trailer：

- 所有提交（**含 merge 提交**）必须在 body 尾部带一行 `Agent: <工具>-<角色>`，如 `Agent: dsh-lead`、`Agent: trae-dev`、`Agent: codebuddy-fix`；
- 代用户执行的操作照常使用用户 git 身份，trailer 只标注**执行体**，不改变 author/committer；
- 目的：审计归因（谁做的生产回滚 / 谁绕过门禁 / 谁合的 PR）不再依赖考古；
- 判定：`hooks/scripts/branch-hygiene-check.mjs` 对 HEAD 缺 trailer 给 WARN（观察期）。

## 分支规范

- **禁止**直接提交到 `main` / `master` 分支
- 功能分支：`feature/xxx`
- 修复分支：`fix/xxx`
- 紧急修复：`hotfix/xxx`
- 分支命名使用 `kebab-case`
- **分支流转生命周期**（创建→合并→删除、release 策略、Tag 发布）见 `rules/branch-strategy.md`

## Pull Request 规范

- 单个 PR 的变更量**建议**控制在 400 行以内，以保证可审查性
- 超过 400 行时优先按依赖拆分为多个 PR；确因内聚性无法拆分时，在 PR 描述中说明理由（**不硬性阻断**）
- PR 描述说明变更内容、影响范围和测试方式
- PR 必须通过 CI 检查后才能合并

## 工作流

1. 从 `main` 创建功能分支
2. 在功能分支上开发和提交
3. 创建 PR，确保 CI 通过
4. Code Review 通过后合并到 `main`

---

## 禁止事项

- ❌ 直接提交到 `main` / `master` 分支
- ❌ 同一仓库内 commit message 语言或风格不统一
- ❌ 单个 PR 变更过大且未说明拆分理由
- ❌ 提交未经 CI 检查的代码
- ❌ Commit message 不符合 Conventional Commits 格式
- ❌ 分支命名使用下划线或驼峰（如 `feature/user_login` 或 `feature/addUser`）
