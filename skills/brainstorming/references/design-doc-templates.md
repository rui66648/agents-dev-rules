# 设计文档模板参考（brainstorming 步骤 5 / 6 配套）

> 本文档按需加载。包含设计文档章节结构、三合约模板、需求探索 Prompt 模板与实现泄漏规则。

## 1. 文档 frontmatter（必须）

```yaml
---
design_type: feature      # feature | phase | initiative
created_at: YYYY-MM-DD
---
```

## 2. 章节结构

### feature/phase 级别（7 个必需章节）

1. `## Intent Contract`
2. `## Verification Contract`
3. `## Governance Contract`
4. `## Scope`（in / out，表格形式）
5. `## Decisions`（# / 决策 / 选择 / 被否定的替代方案，表格形式）
6. `## Surface`（API / 存储 / 组件 / 涉及文件，每段简述）
7. `## Risks & Open Questions`

### initiative 级别（9 个章节，新增 Market Context + User Personas）

1. `## Market Context` ← 必须（模板见 [market-research.md](market-research.md) 第 6 节）
2. `## User Personas` ← 必须（模板见 [market-research.md](market-research.md) 第 6 节）
3. `## Intent Contract`
4. `## Verification Contract`
5. `## Governance Contract`
6. `## Scope`
7. `## Decisions`
8. `## Surface`
9. `## Risks & Open Questions`

## 3. 三合约模板

```
### Intent Contract
intent: [一句话目标]
constraints: [什么不能改变/破坏]
success_criteria: [怎么算完成]
risk_level: low | medium | high
```

```
### Verification Contract
verify_steps:
  - run tests: [测试命令]
  - check: [检查什么]
  - confirm: [成功信号]
```

```
### Governance Contract
approval_gates: [需要人工审查的步骤]
rollback: [出问题怎么回滚]
ownership: [谁负责]
```

> `risk_level: high` 自动适用于安全、认证、隐私、计费相关需求，必须人工门禁。
> `initiative` 级别且涉及市场/竞品的，默认 `risk_level: high`。

## 4. 自检清单（设计文档写完后内部过一遍）

通用项：

- [ ] 约束条件是否缺失？
- [ ] 验收标准是否模糊？
- [ ] 验证步骤能否真正验证 intent？
- [ ] 风险等级是否合适？
- [ ] 是否有 scope creep？
- [ ] 是否违反"实现泄漏"规则（见第 6 节）？

研究项（仅当执行了外部研究）：

- [ ] 市场数据是否有时效标注（截至 YYYY-MM）？
- [ ] 竞品分析是否包含最新定价和功能？
- [ ] 用户痛点是否有来源依据（非 AI 臆测）？
- [ ] 差异化机会是否有数据支撑？
- [ ] 搜索结果是否覆盖了主要竞品（Top 5）？
- [ ] 所有数据是否标注了来源 URL？

## 5. 需求探索 Prompt 模板

### MVP 功能梳理模板

当用户提出模糊需求时，使用此模板引导结构化梳理：

```
我想做一个 [XXX] 项目，目标用户是 [XXX]，
核心要解决的问题是 [XXX]。

请帮我：
1. 梳理核心功能列表（MVP 版本，不要贪多）
2. 列出用户故事（User Story）
3. 标注优先级（P0 必须有 / P1 重要 / P2 可后做）
4. 指出我可能遗漏的需求点
5. 给出一个合理的技术栈建议（考虑我一个人开发）
```

### 用户故事生成模板

当需要细化功能需求时：

```
基于以下 MVP 功能列表：[列出功能]

请为每个功能生成用户故事：
- 作为 [角色]，我想要 [功能]，以便 [价值]
- 标注验收标准
- 标注依赖关系
```

### 技术选型辅助模板

当项目需要技术选型时（应结合 `tech-stack.md`）：

```
我要做 [XXX] 项目，功能包括：[列出功能]
约束条件：[一人开发 / 低成本 / 快速上线]

请给出 2-3 个技术栈方案对比：
- 每个方案的优势和劣势
- 适合场景
- 学习成本
- 推荐理由
```

## 6. 实现泄漏规则（设计文档中禁止出现）

| 泄漏类型 | 示例 | 为什么不该出现在设计里 |
|---------|------|---------------------|
| 行号引用 | `cli.py:16` | 代码一动就失效 |
| 长代码块（>10 行） | 30 行 Python 片段 | 设计说 shape，实现说 exact bytes |
| 密集 flag 行（≥6 个 `--`） | `docker run --network=none --cap-drop=ALL ...` | 参数断言放在 workflow 步骤和测试里 |

> 当设计文档必须引用其中之一作为示例时，用 Markdown 引用块（`> Example: ...`）或标注 `Example` 的章节包裹，并在自检时说明理由。
