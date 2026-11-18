# 贡献指南

感谢参与。本仓库的价值在于**规则与门禁的确定性**，因此贡献有明确的硬性门槛。

## 贡献前必读

本仓库遵循 [AGENTS.md](AGENTS.md) 中的规则体系。改动本仓库前，请先按其 §2 入口路由读取对应规则。

## 硬性要求

任何 PR 必须满足以下全部条件，否则 CI 会拦截：

### 1. 规则改动需同步登记

改动 `rules/` 下的规则正文后：

- `AGENTS.md` §3 速查表需同步（含编号、主题、落点路径）
- `rules/applies_to.md` 索引需同步
- 新增规则编号必须递增，不得复用已废弃编号

由 `scripts/rules-consistency-check.py` 校验（检查位置存在、编号不重复、索引双向对齐、版本一致、悬空路径、License 交叉一致）。

### 2. 规则必须「结构性活着」

一条落点规则必须配齐四件套，否则视为结构性失效：

| 件套 | 含义 |
|------|------|
| **触发入口** | 代理能知道「什么时候该读这条规则」——须在 `AGENTS.md` §2 入口路由中登记 |
| **产物落点** | 规则要求的产物写到哪个路径 |
| **模板** | `templates/` 下有对应模板 |
| **判据** | 有可执行的检查方式（门禁脚本或明确的人工判据） |

由 `scripts/rule-liveness-check.py` 校验。**只写规则正文但不接入口 = 规则从未生效**——这是本仓库最常见也最隐蔽的失效模式。

### 3. 门禁脚本必须自证

新增或修改门禁脚本，必须实现 `--selftest`，用**负向注入**证明脚本确实会失败（防止假绿）。

示例：

```bash
python scripts/rule-liveness-check.py --selftest
```

### 4. 禁止提交敏感信息

- ❌ 真实 API Key、Token、密码、私钥
- ❌ 内网地址、内网 IP 段、`.internal` / `.local` 域名
- ❌ 个人绝对路径（`C:\Users\<用户名>\...`）
- ❌ 内部项目代号、私有仓库名

需要示例时用占位符：`<RULES_ROOT>`、`<WORKSPACE>`、`<repo-a>`、`your-key-here`。

### 5. 路径必须可迁移

脚本**不得硬编码绝对路径**。规则根用以下方式解析：

```python
# Python
ROOT = Path(__file__).resolve().parents[1]
```

```javascript
// Node.js
const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '..');
```

```powershell
# PowerShell
$RulesRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
```

## 本地校验清单

提交前跑通全部：

```bash
pip install pyyaml

python scripts/rules-consistency-check.py
python scripts/rule-liveness-check.py
python scripts/rules-audit.py
python hooks/schema-validator.py --all --fail-on-violation
python hooks/scripts/health-check.py
```

## 提交信息规范

```
<type>(<scope>): <subject>

type: feat | fix | docs | refactor | test | chore | perf
scope: 规则编号或目录名，如 rules/053、skills/code-review
```

示例：

```
feat(rules/055): spec-driven 补澄清门禁的反向断言
fix(hooks): rule-liveness C6b 误报 registry 派生项
docs(skills/verification): 补规格收敛检查的证据要求
```

## 分支命名

- `feature/<简述>` — 新功能
- `fix/<简述>` — 缺陷修复
- `agent/feature/<agent-id>-<简述>` — AI 代理分支

## 新增技能

```
skills/<skill-name>/SKILL.md
```

`SKILL.md` 需带 frontmatter：

```yaml
---
name: skill-name
version: v1.0.0
description: 一句话说明何时触发
---
```

并在 `commands/` 或 `agents/` 中登记入口，否则同样构成结构性失效。

## 新增命令

```
commands/<command-name>.md
```

## 许可

提交即表示你同意你的贡献按 [Apache-2.0](LICENSE) 授权。
