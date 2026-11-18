---
name: cross-project-conflicts
version: v1.1.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-04
description: 跨项目冲突消解 — 端口/依赖/环境变量/命名空间冲突的预防与解决（项目清单已更新为 example-workspace 四仓）
applies_to:
  agents: ['architect', 'security-auditor']
  phases: ['全程']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 跨项目规则冲突检测

> 修改共享规则时，检查各项目之间是否存在规则冲突或适用性差异。

---

## 检测规则

### 1. 技术栈兼容性检测

| 项目 | 技术栈 | 需关注的规则 |
|------|--------|------------|
| `<repo-d>` | Cloudflare Workers + Hono / React 18 + Supabase（本地 `demo/backend` 为 FastAPI） | cicd, security, component-selection |
| `<repo-b>` | Cloudflare Workers + Hono / React + antd / D1·Supabase·R2 | security, cicd, directory-structure |
| `<repo-a>` | **未核实**（仓内无 `tech-stack.md`） | 待补 tech-stack 后判定 |
| `<repo-c>` | **未核实**（仓内无 `tech-stack.md`） | 待补 tech-stack 后判定 |
| `personal/*` | 个人项目，按各自技术栈 | 按 `applies_to.tech_stacks` 逐条判定 |

> 事实口径：上表仅登记已核实项；`<repo-a>`、`<repo-c>` 缺 `tech-stack.md`，在补齐前不得假定其技术栈。旧项目名（应用 C、应用 E、应用 B、ko、应用 A、应用 D）已退役，不再作为并行项目参与冲突检测。

**冲突场景**：
- `architecture.md` 中新增 Python 特定分层约束 → 只影响含 Python 子栈的项目（如 `portal` 的 `demo/backend`）
- `testing-rules.md` 中新增 pytest 要求 → 不影响纯 Workers/TS 项目，需按 `applies_to.tech_stacks` 分流

### 2. 规则适用范围标注

所有规则文件应在 frontmatter 中声明 `applies_to.tech_stacks`，新增规则时检查：
- 是否所有项目的技术栈都在列表中
- 是否遗漏了某个项目适用的技术栈

### 3. 检测流程

```
修改规则文件
    │
    ▼
检查 applies_to.tech_stacks
    │
    ├── 包含所有项目技术栈 → 无需冲突检测
    │
    └── 不包含某些技术栈 → 检查以下项目是否受影响
          ├── <repo-d> (Workers + React / 本地 FastAPI)
          ├── <repo-b> (Workers + React)
          ├── <repo-a> (未核实)
          └── <repo-c> (未核实)
              │
              ▼
          输出冲突报告
```

---

## 冲突报告模板

```markdown
## 跨项目冲突报告

### 规则变更: `<某规则文件>.md` (v1.0 → v1.1)

| 项目 | 技术栈 | 冲突点 | 建议 |
|------|--------|--------|------|
| <repo-b> | Workers + React | 规则引用 pytest，该项目无 Python 测试层 | 将 pytest 部分标注为 `[项目特定]` |
| <repo-d> | Workers + React（本地 FastAPI） | 规则引用 FastAPI 通用约束 | 限定到 `demo/backend/` 子目录 |

### 结论
- 冲突数量: N 个
- 需拆分规则: M 个
- 需通知项目: K 个
```

> **占位符约定**：报告模板中的 `<某规则文件>.md`、`N/M/K`、`v1.0 → v1.1` 均为示例占位，
> 不代表真实文件或真实数字。真实规则文件名一律不带尖括号；写报告时按实际值替换。

> 另注：`rules/applies_to.md` 底部列出的 `rules/architecture-python.md` 等 5 条
> 是**已声明的预留项**（"暂不存在，保留元数据供未来创建使用"），不是悬空引用。

---

## 使用方式

1. 修改规则文件前，先执行 `/rules-audit` 扫描影响范围
2. 检查 `rules/applies_to.md` 中的 `tech_stacks` 字段
3. 如果新增语言特定内容，优先在文内用 `<!-- [项目特定] -->` 标注；确需拆分时再创建 `rules/architecture-{lang}.md` 并同步 `applies_to.md` 与 registry
4. 发布变更时，在受影响项目根目录的 `tech-stack.md` 中注明适用的规则变更（该文件缺失的项目先补齐）
