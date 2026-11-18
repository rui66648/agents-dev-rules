---
name: finish
version: v1.0.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-08-03
description: 斜杠命令：finish - "完成开发"、"合并分支"、"收尾"、"清理工作区"
---
# /finish - 分支收尾

**触发词**: "完成开发"、"合并分支"、"收尾"、"清理工作区"

---

## 命令语法

```
/finish [--merge=main|develop] [--cleanup]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--merge` | enum | 否 | `main` | 合并目标分支：`main`（主分支）、`develop`（开发分支） |
| `--cleanup` | flag | 否 | false | 合并后是否清理工作树（删除 feature 分支） |

## 触发场景

- 功能开发完成，所有测试通过，代码审查通过
- 需要合并到主分支并清理工作树
- 准备发布前的最终整理
- 需要生成 CHANGELOG 或版本标签

## 前置条件

1. 所有测试通过（`verification` 验证通过）
2. 代码审查通过（`code-review` 审查通过）
3. 无未提交的变更
4. 与目标分支无冲突

## 执行流程

1. **最终验证** — 运行全量测试，确认无回归
2. **冲突检查** — 检查与目标分支的合并冲突
3. **合并分支** — 将 feature 分支合并到目标分支
4. **清理工作树** — 删除 feature 分支（如 `--cleanup`）
5. **版本标签** — 按需打 tag（如 `v1.2.0`）

## 产出物

- 合并后的代码（目标分支已包含 feature 变更）
- 清理后的工作树（feature 分支已删除）
- 版本标签（如有）

## 错误处理

| 常见错误 | 处理方式 |
|----------|----------|
| 合并冲突 | 手动解决冲突，重新运行测试 |
| 测试未通过 | 返回 `executing-plans` 修复 |
| 审查未通过 | 返回 `code-review` 修改 |
| 未提交变更 | 提示先提交或暂存变更 |

## 示例

```
/finish --merge=main --cleanup
```

**预期输出**：
- 合并到 main 分支
- 删除 feature 分支
- 工作树清理完成

---

**执行流程**: 遵循 [finishing-branch 技能](skills/finishing-branch/SKILL.md`) 的完整流程
**负责代理**: `architect`