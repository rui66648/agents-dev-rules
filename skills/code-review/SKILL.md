---
name: code-review
version: v1.2.0
type: skill
enabled: true
mode: [standard, creator]
description: "完成功能/任务后、合并分支前使用。组织上下文并请求结构化代码审查，输出问题清单与修复建议；维度 0 规格符合性以 spec.md 的 FR/验收场景逐条比对。触发词: 代码审查、review、看看代码、检查代码。"
updated: 2026-11-07
depends_on: [ai-safety-check]
composes: [verification]
interface:
  inputs: [context, changes]
  outputs: [review_report, issues]
---

# Code Review

## 负责代理

`code-reviewer` — 代码审查由代码审查员代理负责，确保审查覆盖设计一致性、代码质量、测试覆盖、安全隐患和编码规范五个维度。

## 何时使用

- 完成一个功能或任务的所有开发工作后
- 准备合并分支到主分支之前
- 用户明确要求"代码审查"、"review 一下"、"提交前看一下"时
- 在 `verification` 技能确认所有测试通过后

**触发关键词**: "代码审查"、"review"、"帮我看看"、"提交前检查"

## 执行流程

### 1. 组织审查上下文

收集以下信息用于代码审查:

```markdown
## 变更摘要
- 功能描述 (1-2 句)
- 涉及的模块/文件
- 变更原因

## 影响范围
- 修改的文件列表
- 新增的文件列表
- 删除的文件列表
- 数据库 Schema 变更 (如有)

## 测试状态
- 测试通过率
- 测试覆盖的模块
- 手动验证结果

## Diff 展示
- 关键代码变更 (git diff 摘要)
```

### 2. 多维度审查

从以下维度逐项检查:

#### 维度 0: 规格符合性 (Spec Compliance)

> 审查首先要回答"是否实现了用户真正要的东西"，其次才是代码质量。避免"代码漂亮但做错了需求"。

- **读取 spec**（`docs/tasks/<id>/spec.md`），按其编号需求逐条比对——不要凭 diff 印象判断
- 是否有 FR 要求实现但未实现（漏做）
- 是否有实现但 spec 未要求的范围蔓延（多做，且不在 `scope.out` 的豁免里）
- 每个验收场景是否有对应测试且通过
- 需求优先级是否被正确遵循（P0 功能不得被 P2 功能替代优先）
- **规格—代码同步**（RULE-055 §4）：本次改了行为，spec 的对应 FR / 验收场景是否同批更新？
  commit 是否记了 `spec:<slug>@v<N>`？——**代码改了规格没改 = Critical 级 spec-drift**

**规格符合性检查表**：
| 检查点 | 说明 |
|--------|------|
| FR 遗漏 | spec 的 FR-NNN 是否有未实现的功能点 |
| 范围蔓延 | 实现是否超出 `scope.in` 边界 |
| 验收场景 | 每条的验证动作是否真的跑过并通过 |
| 优先级 | P1 是否被完整实现，未被 P2 挤占 |
| 规格同步 | 行为变更是否同批更新 spec 并升 `spec_version` |

#### 维度 1: 设计一致性
- 实现是否符合已批准的设计方案
- 是否遵循 Clean Architecture 分层 (Router -> Service -> Repository -> Model)
- 是否引入了未批准的架构变更

#### 维度 2: 代码质量
- 命名是否清晰、一致 (snake_case / camelCase)
- 函数是否职责单一、长度合理
- 是否有重复代码可提取
- Type Hints / TypeScript 类型是否完整
- 是否有硬编码的魔法值

#### 维度 3: 测试覆盖
- 新功能是否有对应的测试用例
- 边界条件是否覆盖
- Mock 使用是否合理 (不过度 mock)
- 测试命名是否清晰

#### 维度 4: 安全隐患
- 是否有 SQL 注入风险
- 是否有 XSS 风险 (前端)
- 是否硬编码了密钥/URL
- 用户输入是否经过 Pydantic 校验
- 权限控制是否到位

#### 维度 5: AI 生成代码专项安全检查

> AI 生成代码引入安全漏洞的概率比手写代码高 23%，必须专项检查。

**高频 AI 安全漏洞清单**：

| 漏洞类型 | 检查点 | AI 常见错误 |
|----------|--------|-------------|
| 硬编码密钥 | API Key、密码、JWT Secret | AI 倾向于在示例中写死密钥 |
| SQL 注入 | 字符串拼接 SQL | AI 使用 `f-string` 拼接查询 |
| 路径遍历 | 文件操作路径 | AI 未对用户输入路径做规范化 |
| 不安全的反序列化 | `JSON.parse` / `pickle` | AI 直接解析用户输入未校验 |
| 依赖漏洞 | 过期包版本 | AI 可能推荐有 CVE 的版本 |
| SSRF | 服务端请求伪造 | AI 未限制内网地址访问 |
| 敏感信息泄露 | 日志/错误信息 | AI 在日志中打印完整对象 |

**AI 代码安全审查 Prompt 模板**：

```
对以下 AI 生成的代码做安全审查，重点检查：
1. 所有用户输入是否经过校验和转义
2. 是否存在硬编码的密钥或敏感信息
3. 文件路径、SQL 查询是否有注入风险
4. 依赖包版本是否有已知 CVE
5. 日志输出是否包含敏感信息
6. 错误处理是否泄露内部实现细节

[粘贴代码]
```

#### 维度 6: 编码规范
- Python: PEP 8、Ruff 格式化
- TypeScript: strict 模式、ESLint 通过
- 命名规范: API 路由 kebab-case、数据库 snake_case
- Docstring / JSDoc 是否完整

### 3. 生成审查报告

按严重程度分类审查发现:

- **Critical**: 必须修复后才能合并
- **Major**: 强烈建议修复
- **Minor**: 可以后续优化
- **Suggestion**: 改进建议

#### 3.1 机器可读 JSON 输出（供 CI / verifier 消费）

除对话中的可读报告外，审查必须同时输出机器可读 JSON，写入 `docs/reviews/code-review-<YYYYMMDD>.json`，供 CI / verifier 脚本解析：

```json
{
  "schema_version": "1.0",
  "reviewed_at": "2026-08-11T00:00:00Z",
  "scope": {
    "files_modified": ["src/app.py"],
    "files_added": [],
    "files_deleted": []
  },
  "findings": [
    {
      "severity": "critical | major | minor | suggestion",
      "file": "src/app.py",
      "line": 42,
      "dimension": "spec | security | design | quality | testing | code_style",
      "message": "硬编码 API Key",
      "suggestion": "改用环境变量读取"
    }
  ],
  "verdict": "approve | fix_critical | discuss",
  "summary": "共 N 项发现，其中 Critical X、Major Y"
}
```

**JSON 输出规则**：

1. `findings` 为空数组且 `verdict` 为 `approve` 时，可确认审查通过
2. `severity` 取值仅限 `critical|major|minor|suggestion` 四档
3. `verdict` 取值仅限 `approve|fix_critical|discuss` 三档
4. 任一 `critical` 发现存在时，`verdict` 必须为 `fix_critical`，不得为 `approve`
5. 该 JSON 供 CI 的 review-gate 与 `verifier` 代理消费，作为合并前置条件

### 4. 用户决策

- 展示审查报告，等待用户决定:
  - 修复所有 Critical 项后重新审查
  - 确认无误，准备合并
  - 需要讨论具体发现

## 硬性规则

- ✅ **Critical 问题必须修复**，不得跳过
- ✅ 审查必须覆盖**所有 7 个维度**（含维度 0 规格符合性）
- ✅ 必须提供**变更摘要和影响范围**
- ✅ 审查报告按**严重程度分级**
- ❌ **审查未通过不得合并**
- ❌ 禁止只看一个文件就下结论
- ❌ 禁止忽略安全隐患标记为 Minor
- ❌ 禁止在未运行测试的情况下进行审查

## 反模式

- ❌ "LGTM" 没有任何具体分析 — 无效审查
- ❌ 只关注代码风格不关注逻辑 — 本末倒置
- ❌ 审查者自己修改代码 — 审查应指出问题，由作者修复
- ❌ 忽略数据库 Schema 变更 — 这类变更影响最大
- ❌ 对所有 Minor 问题都阻塞合并 — 区分优先级