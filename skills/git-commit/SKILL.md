---
name: git-commit
version: v1.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "verification 通过后、finishing-branch 之前执行 git commit 时使用。遵循 Conventional Commits 规范，智能分析变更、安全暂存并生成提交信息。触发词: 提交、commit、提交代码。"
updated: 2026-08-15
depends_on: [verification]
composes: [finishing-branch]
---

# Git Commit

## 负责代理

`architect` — 提交规范由架构师代理统一把关；所有 Agent 在提交代码时均需调用本技能。

## 何时使用

- 功能开发完成，需要提交代码时
- 用户说"提交一下"、"commit"、"提交代码"时
- `verification` 技能确认检查通过后
- 在进入 `finishing-branch` 之前

**触发关键词**: "提交"、"commit"、"提交代码"、"git commit"

## 前置条件

在进入此技能前，必须确认:
- [ ] `verification` 已确认所有测试通过
- [ ] `ai-safety-check` 已确认无安全漏洞（RULE-016）
- [ ] 代码已通过 Linter 检查（RULE-028）

## 执行流程

### 1. 分析变更

```bash
git status          # 查看未跟踪/修改文件
git diff            # 查看未暂存变更
git diff --cached   # 查看已暂存变更
git log --oneline -5  # 查看最近提交风格
```

### 2. 智能暂存

- 优先按文件名精确暂存（`git add <file>`），避免误提交敏感文件
- 禁止使用 `git add -A` / `git add .`（可能包含 `.env`、凭据等敏感文件）
- 发现 `.env`、`credentials.json` 等敏感文件时，**禁止提交**并警告用户

### 3. 生成提交信息（Conventional Commits）

```
<type>(<scope>): <subject>

<body>
```

| type | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 新增用户注册接口` |
| `fix` | Bug 修复 | `fix: 修复登录超时问题` |
| `refactor` | 重构 | `refactor: 拆分 UserService` |
| `docs` | 文档 | `docs: 更新 API 文档` |
| `test` | 测试 | `test: 补充边界用例` |
| `chore` | 杂项 | `chore: 升级依赖版本` |
| `perf` | 性能优化 | `perf: 优化查询索引` |
| `style` | 样式 | `style: 格式化代码` |

**提交信息要求**：
- subject 用祈使句，简洁（< 50 字符）
- 聚焦"为什么"而非"做了什么"
- 不引用当前任务/修复编号（属于 PR 描述）

### 4. 提交

```bash
git commit -m "feat(scope): subject"
```

### 5. 验证提交

```bash
git log --oneline -1   # 确认提交成功
git status             # 确认工作树干净
```

## 禁止事项

- ❌ 禁止提交敏感文件（`.env`、凭据、密钥）
- ❌ 禁止使用 `git add -A` 全量暂存
- ❌ 禁止跳过 pre-commit hooks（`--no-verify`）
- ❌ 禁止在提交信息中引用内部任务编号
- ❌ 禁止修改 git config（`git config` 变更需用户确认）

## 输出

- 提交成功后的 commit hash
- 变更文件清单
- 提交信息摘要
