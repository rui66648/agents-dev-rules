---
name: verification
version: v1.3.0
type: skill
enabled: true
mode: [standard, creator]
description: "在声称工作\"完成\"、\"已修复\"、\"测试通过\"之前使用。强制进行实际验证并提供证据，不接受假设；L2/L3 追加规格收敛检查（FR 覆盖 + spec 门禁）。触发词: 完成了、修好了、验证一下、没问题了。"
updated: 2026-11-07
depends_on: [code-review]
composes: [git-commit]
---
# Verification


## 负责代理

`architect` — 完成前验证由架构师代理统一把关，确保所有验收标准被实际验证通过；`test-engineer`、`code-reviewer`、`verifier` 在其职责范围内共同调用该技能。

## 何时使用

- 在声称任何工作"完成"之前
- 在声称 Bug "已修复"之前
- 在声称"测试通过"之前
- 在准备合并分支之前 (作为 `code-review` 的前置条件)

**触发关键词**: "完成了"、"修好了"、"通过了"、"没问题了"、"验证一下"

## 执行流程

> **快捷方式**：步骤 1-3 的测试/Lint/构建门禁可用确定性脚本一次跑完并自动收集证据（按项目传入命令）：
> `powershell -File <规则库根>/skills/verification/scripts/run-gates.ps1 -TestCmd "pytest -q" -LintCmd "ruff check ." -BuildCmd "pnpm build"`
> （`<规则库根>` = 共享规则库根目录，如 `<RULES_ROOT>`；脚本从当前项目目录执行，证据日志写入当前目录 `.verify-evidence/<时间戳>/`）
> 脚本输出 PASS/FAIL 与证据日志路径，直接用于第 6 步验证报告；仍须人工完成步骤 4-5。

### 1. 运行完整测试套件

```bash
# 后端
pytest --tb=short -q

# 前端
pnpm test -- --run
```

**验收标准**: 所有测试通过，0 失败。

### 2. Lint 检查

```bash
# 后端
ruff check .
ruff format --check .

# 前端
pnpm lint --max-warnings 0
pnpm typecheck
```

**验收标准**: 0 error，0 warning (或仅有已确认的 warning)。

### 3. 构建验证

```bash
# 前端生产构建
pnpm build

# 后端 (如适用)
docker compose build
```

**验收标准**: 构建成功，无编译错误。

### 4. 手动验证核心功能

根据功能类型选择验证方式:
- **API 接口**: 通过 Swagger (`/docs`) 测试关键接口
- **前端页面**: 通过浏览器访问验证 UI 渲染和交互
- **数据库**: 检查数据一致性、索引是否生效
- **文件变更**: `git diff` 确认只修改了预期文件


### 5. 设计 → 实现一致性检查

> 在验证流程中增加一致性检查，确保设计文档中的 API 和功能点全部在实现中被覆盖。

#### 检查流程

```
读取设计文档的 API 集成矩阵
    │
    ▼
扫描前端代码，提取所有 API 调用模式
（如 apiClient.get/post/put/delete、fetch()、axios.get/post 等）
    │
    ▼
比对：设计文档列出的 API 端点是否全部出现在前端代码中
    │
    ▼
输出比对报告：
- 已对接：设计文档中的 API 在前端代码中找到对应调用
- 未对接：设计文档中的 API 在前端代码中未找到
- 额外对接：前端代码中调用了设计文档未列出的 API
```

#### 一致性检查报告模板

```markdown
## 设计 → 实现一致性检查

### API 对接状态

| # | 设计文档 API | 前端代码调用 | 状态 |
|---|-------------|-------------|------|
| 1 | GET /api/xxx | apiClient.get('/api/xxx') | 已对接 |
| 2 | POST /api/yyy | 未找到 | 未对接 |

### 结论

- 已对接: N 个
- 未对接: M 个
- 额外对接: K 个（设计文档未列出的 API）
- 评估: 通过 / 有条件通过 / 不通过（存在未对接 API 且未获用户确认时）
```

#### 硬性规则

- 如果存在未对接的 API，禁止开发者声明"任务完成"
- 发现未对接 API 时，必须在对话中明确报告差异详情
- 用户确认延期处理的未对接 API 可标记为"有条件通过"
- 禁止在未执行一致性检查的情况下完成验证报告
- 禁止忽略 API 集成矩阵中的任何条目
- 禁止在未对接 API 的情况下将验证结论标记为"通过"


### 5. 规格收敛检查（v1.3.0 新增，ADR-008）

> 在验证流程中增加规格一致性检查，确保 spec 的编号需求与验收场景全部在实现中被覆盖；
> 这是 `executing-plans` 收敛判据的第 3 条，未收敛不得声称完成。
>
> **与 RULE-004 的边界**（同 `rules/spec-driven.md` §9）：RULE-004 的验证合约
> （`rules/hotl-contracts.md` 的 `verify_steps`）回答**"怎么验"**，本步回答**"验的是不是 spec 要的"**。
> 两者互补，不是两套独立验证——`verify_steps` 的实现落在 tasks 的验证动作里，spec 的 `Acceptance`
> 决定这些动作是否覆盖了全部需求。

#### 检查流程

```
读取 docs/tasks/<id>/spec.md 的 FR 与验收场景
     │
     ▼
逐个 FR 对照实现与测试：有没有对应测试？断言是否匹配场景期望？
     │
     ▼
跑规格门禁（零依赖）：
node <规则库根>/hooks/scripts/spec-clarity-gate.mjs --root <仓根>
     │
     ├─ PASS → 收敛，可进入 code-review
     └─ FAIL → 修代码；若发现规格本身有误，升 spec_version 改规格后重跑
```

#### 规格收敛检查报告模板

```markdown
## 规格收敛检查

### FR 覆盖

| FR | 摘要 | 对应测试 | 状态 |
|----|------|---------|------|
| FR-001 | 系统 MUST … | tests/test_x.py::test_… | ✅ 已覆盖 |
| FR-002 | 系统 SHALL … | （无） | ❌ 未覆盖 |

### 规格门禁

- 命令: `node <规则库根>/hooks/scripts/spec-clarity-gate.mjs --root <仓根>`
- 结果: ✅ PASS（2 份 spec、5 条 FR，无遗留澄清、无漂移）
- [附实际输出]

### 结论

- 收敛: 是 / 否（未收敛必须留在 executing-plans，不得进 code-review）
```

#### 硬性规则

- **未收敛不得声称完成**——spec 的 FR 没有对应测试、或门禁 FAIL，一律停在 executing-plans
- 规格本身写错是**合法发现**：改规格要升 `spec_version` 并记 `spec:<slug>@v<N>`，不许悄悄改
- L0/L1 任务无落盘 spec，本步退化为"对话内轻量规格的口头复核"，不跑门禁也不判 FAIL
- 禁止把"验证实现"这类没有对应测试的 task 标为 done 后直接进本步骤

### 6. 生成验证报告

```markdown
## 验证报告

### 测试套件
- 命令: `pytest --tb=short -q`
- 结果: ✅ 42 passed, 0 failed, 0 errors
- [附实际输出]

### Lint 检查
- 命令: `ruff check .`
- 结果: ✅ All checks passed
- [附实际输出]

### 构建验证
- 命令: `pnpm build`
- 结果: ✅ Build successful (2.3s)
- [附实际输出]

### 结论: ✅ 所有验证通过，可以进入 code-review
```

## 硬性规则

- ✅ **必须贴出实际命令输出**作为证据
- ✅ 步骤 1–5 全部通过（测试套件 / Lint / 构建 / 手动验证 / 规格收敛）才能声称"完成"
- ✅ 验证报告必须包含**命令和实际输出**
- ✅ 任何一项检查失败时，**暂停并修复**
- ❌ **不接受"应该没问题"** — 必须有实际证据
- ❌ **不接受"我之前测过了"** — 必须重新运行
- ❌ 禁止跳过任何检查项
- ❌ 禁止在测试失败时声称"完成"

## 反模式

- ❌ "测试应该没问题" — 假设不是验证
- ❌ "我本地跑过了" — 不贴出输出就没有证据
- ❌ 只跑部分测试就说"全部通过" — 必须跑完整套件
- ❌ 跳过 lint 检查"反正不影响功能" — 技术债累积
- ❌ 构建失败还说"代码写好了" — 无法部署的代码等于没写
