# Rules applies_to 元数据

> 本文件列出所有规则文件的 applies_to 元数据，供 AGENTS.md 入口路由和规则影响分析使用。
> 每个 rules/*.md 文件应在 frontmatter 中声明 applies_to 字段。

---

## 规则元数据索引

> 版本 / RULE 编号 / 级别 的**唯一权威**是 `plugins/registry.yaml`；本表由生成器写入，勿手改。
> 交叉引用不再在本表重复维护——以各规则正文与 `AGENTS.md` 入口路由为准（避免又一处需人肉对齐的分叉）。

<!-- generated:rule-index begin -->
<!-- 本区块由 scripts/rule-index-gen.py 生成：版本/RULE/级别取自 plugins/registry.yaml，
     Agent/阶段/项目类型/技术栈取自各 rules/*.md 的 frontmatter。勿手改，改源后重跑生成器。 -->
| 规则文件 | 版本 | RULE | 级别 | 适用 Agent | 适用阶段 | 适用项目类型 | 适用技术栈 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `rules/adlc-lifecycle.md` | v4.2.0 | RULE-041 | 建议 | architect, backend-developer, test-engineer | design, implementation, deploy | 全部 | 全部 |
| `rules/agent-constraints.md` | v2.1.0 | RULE-028 | 铁律 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/agent-context.md` | v2.0.0 | — | 建议 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/anti-patterns.md` | v1.2.0 | — | 铁律 | code-reviewer, 全部 Agent | 全程 | 全部 | 全部 |
| `rules/architecture.md` | v1.1.0 | RULE-005 | 铁律 | architect, backend-developer, database-expert | design, implementation | backend, fullstack, mobile | python, kotlin, typescript |
| `rules/backup-recovery.md` | v1.0.1 | RULE-050 | 建议 | database-expert, backend-developer, architect | deploy, operations | 全部 | 全部 |
| `rules/branch-strategy.md` | v1.2.0 | — | 建议 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/cicd-rules.md` | v4.4.4 | RULE-007 | 铁律 | architect, backend-developer | deploy, implementation | 全部 | 全部 |
| `rules/cloudbox-rules.md` | v1.0.0 | RULE-059 | 建议 | 全部 Agent | implementation, testing, deploy | 全部 | 全部 |
| `rules/coding-standards.md` | v1.1.0 | — | 建议 | 全部 Agent | implementation | 全部 | 全部 |
| `rules/collaboration.md` | v1.7.0 | RULE-001, RULE-002, RULE-014 | 铁律 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/component-selection-rules.md` | v1.2.1 | RULE-034, RULE-035, RULE-036 | 铁律 | frontend-developer, ui-designer, 全部 Agent | design, implementation, review | web, fullstack | typescript, react |
| `rules/skill-discovery.md` | v1.1.0 | RULE-BROWSER | 铁律 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/cross-project-conflicts.md` | v1.1.0 | — | 建议 | architect, security-auditor | 全程 | 全部 | 全部 |
| `rules/deploy-records.md` | v1.1.0 | — | 建议 | backend-developer, architect | deploy | 全部 | 全部 |
| `rules/directory-structure.md` | v1.6.0 | RULE-053 | 铁律 | 全部 Agent | design, build, verify, operations | 全部 | 全部 |
| `rules/engineering-principles.md` | v1.2.0 | RULE-015 | 铁律 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/environment-isolation.md` | v1.0.1 | RULE-048 | 铁律 | architect, backend-developer, security-auditor | implementation, deploy | 全部 | 全部 |
| `rules/exceptions.md` | v1.0.0 | — | 建议 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/git-conventions.md` | v1.2.0 | RULE-011, RULE-012 | 铁律 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/hotl-contracts.md` | v1.2.1 | RULE-004 | 铁律 | architect, 全部 Agent | design, implementation | 全部 | 全部 |
| `rules/monitoring-rules.md` | v1.0.1 | RULE-049 | 建议 | backend-developer, security-auditor | deploy, operations | 全部 | 全部 |
| `rules/open-source-first.md` | v3.7.0 | RULE-017, RULE-018, RULE-019, RULE-042, RULE-051 | 铁律 | architect, backend-developer, frontend-developer, database-expert | design, implementation | 全部 | 全部 |
| `rules/performance-rules.md` | v1.0.1 | — | 建议 | architect, backend-developer, frontend-developer | design, implementation | 全部 | 全部 |
| `rules/priority-system.md` | v1.0.0 | — | 建议 | architect | 全程 | 全部 | 全部 |
| `rules/project-dashboards.md` | v1.2.0 | RULE-054 | 铁律 | 全部 Agent | design, build, verify, operations | 全部 | 全部 |
| `rules/spec-driven.md` | v1.0.0 | RULE-055 | 铁律 | architect, code-reviewer, 全部 Agent | design, implementation, review | 全部 | 全部 |
| `rules/spec-kit.md` | v1.0.1 | RULE-056 | 建议 | architect, 全部 Agent | design, implementation, review | 全部 | 全部 |
| `rules/dev-learning-loop.md` | v1.1.0 | RULE-057 | 建议 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/system-baseline.md` | v1.0.0 | RULE-058 | 建议 | 全部 Agent | 全程 | 全部 | 全部 |
| `rules/project-status.md` | v1.2.0 | — | 建议 | architect | 全程 | 全部 | 全部 |
| `rules/root-directory-hygiene.md` | v2.1.0 | RULE-052 | 铁律 | 全部 Agent | build, verify, operations | 全部 | 全部 |
| `rules/schema-as-code.md` | v4.0.1 | RULE-030, RULE-032, RULE-033 | 铁律 | architect, backend-developer, frontend-developer, ui-designer | design, implementation, review | 全部 | 全部 |
| `rules/security-rules.md` | v1.1.2 | RULE-008, RULE-009, RULE-010, RULE-016 | 铁律 | security-auditor, backend-developer, frontend-developer | 全程 | 全部 | 全部 |
| `rules/tech-debt.md` | v1.0.1 | — | 建议 | architect, code-reviewer | 全程 | 全部 | 全部 |
| `rules/testing-rules.md` | v1.1.4 | RULE-003, RULE-013 | 铁律 | test-engineer, code-reviewer | 5, 6 | 全部 | 全部 |
| `rules/ui-design-patterns.md` | v1.0.1 | — | 建议 | ui-designer, frontend-developer | design | web, mobile | typescript, kotlin, js |
| `rules/workflow-core.md` | v1.3.1 | — | 铁律 | architect | 全程 | 全部 | 全部 |
| `rules/workflow-design.md` | v1.3.0 | — | 建议 | architect, frontend-developer, ui-designer | design | web, mobile, backend | 全部 |
| `rules/workflow-html.md` | v1.1.0 | RULE-006 | 铁律 | docs-author | implementation | web | html, markdown |
<!-- generated:rule-index end -->

> 注：以下规则文件暂不存在，保留元数据供未来创建使用：
> - `rules/architecture-python.md` (Python 架构规范)
> - `rules/security-python.md` (Python 安全规范)
> - `rules/security-android.md` (Android 安全规范)
> - `rules/testing-python.md` (Python 测试规范)
> - `rules/testing-android.md` (Android 测试规范)

---

## 使用说明

### 新增规则时
1. 在 `plugins/registry.yaml` 的 `rules:` 段登记 `version` / `rule_id` / `level`（唯一真源）
2. 在对应 `rules/*.md` 的 frontmatter 中声明 `applies_to`（Agent / 阶段 / 项目类型 / 技术栈）
3. 运行 `python scripts/rule-index-gen.py` 生成本文件索引区块（**不要手改区块内表格**）
4. 更新 AGENTS.md 入口路由表

### 修改规则时
1. 使用 `/rules-audit <规则文件>` 查看影响范围
2. 只改 `plugins/registry.yaml` 里的版本号，再跑 `python scripts/rule-index-gen.py`（会同步本索引与各规则 frontmatter 的 `version:` 行）
3. 确认涉及的 agent 和 skill 是否需要同步更新

### Agent 加载规则时
1. 根据 agent 的 `applies_to.agents` 过滤规则
2. 根据项目技术栈过滤 `applies_to.tech_stacks`
3. 加载匹配的规则文件
