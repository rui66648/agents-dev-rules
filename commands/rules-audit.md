---
name: rules-audit
version: v1.0.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-08-03
description: 斜杠命令：rules-audit - 扫描指定规则文件的引用链，评估变更影响面（对接 scripts/rules-audit.py）
---
# /rules-audit - 规则影响分析

> 扫描指定规则文件，分析其被哪些 agent、skills、项目引用，评估变更影响面。

---

## 执行流程

### Step 1: 扫描规则库

```bash
# 在规则库目录执行
python scripts/rules-audit.py <规则文件>
```

### Step 2: 输出报告

报告格式：

```markdown
## 规则影响分析: rules/security-rules.md

### 引用链

#### 被以下 Agent 引用
- agents/security-auditor.md (L23, L67)
- agents/backend-developer.md (L45)
- agents/frontend-developer.md (L38)

#### 被以下 Skills 引用
- skills/security-design/SKILL.md (L12)
- skills/api-design/SKILL.md (L5)

#### 被以下 Commands 引用
- commands/review.md (L3)

#### 被以下项目 tech-stack.md 引用
- 应用 C/tech-stack.md
- 应用 D/tech-stack.md

### 变更建议

| 变更类型 | 影响范围 | 建议操作 |
|---------|---------|---------|
| 新增规则 | security-auditor, backend-developer | 同步更新两个 agent |
| 删除规则 | 全部引用方 | 清理所有引用后删除 |
| 修改规则 | 全部引用方 | 发布变更通知 |
```

---

## 使用说明

1. 在执行 `/rules-audit` 前，确保规则库路径正确
2. 规则文件路径使用相对路径（相对于规则库根目录）
3. 报告中的行号仅供参考，实际引用可能在多处

---

## 实现脚本位置

```
scripts/rules-audit.py
```

---

## 与 applies_to.md 的关系

`rules/applies_to.md` 是静态索引，`/rules-audit` 是动态扫描：
- 新增规则时，先更新 `applies_to.md`
- 修改规则时，先用 `/rules-audit` 扫描影响面
- 两者结合，实现完整的规则变更管理
