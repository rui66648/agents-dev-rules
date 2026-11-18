# Hooks 目录

个人开发者精简版 Hook 脚本。挂载配置见 [hooks.json](hooks.json)。

## 已挂载的 Hook（hooks.json）

| 脚本 | 用途 | 规则 | 触发时机 |
|------|------|------|---------|
| `scripts/pre-commit-secret-scan.js` | 密钥扫描 | RULE-008 | 执行命令前 |
| `scripts/schema-gate.py` | Schema 契约校验门禁 | RULE-030/032 | 写入/编辑前 |
| `scripts/plugin-gate.py` | 插件清单校验门禁 | RULE-043 | 写入/编辑前 |
| `scripts/post-test.js` | 测试后处理 | — | 执行命令后 |

## 辅助脚本（手动 / CI 调用）

| 脚本 | 用途 | 规则 |
|------|------|------|
| `schema-validator.py`（hooks 顶层） | Schema 全量校验，被 schema-gate 复用 | RULE-030 |
| `scripts/plugin-validator.py` | 清单/注册表校验器（`--check-all`、`--check <file>`、`--check-registry`） | RULE-043 |
| `scripts/agent_linter_checker.py` | Agent 生成代码 Linter 检查（以项目已配置的工具为准） | RULE-028 |
| `scripts/plugin-manifest-backfill.py` | 批量补全插件清单字段（type/enabled/mode） | RULE-043 配套 |
| `scripts/health-check.py` | 引用完整性 + 配置一致性检查 | — |
| `contract-diff.py`、`design-token-linter.js`（hooks 顶层） | 契约差异 / 设计令牌检查 | — |

## 项目级可选门禁（不再全局挂载）

| 脚本 | 用途 | 项目级启用方式 |
|------|------|---------------|
| `scripts/model_gateway_lint.py` | 扫描直连模型 SDK/endpoint | 仅当项目在 `tech-stack.md` 明确要求"统一模型网关"时，由该项目加入自身 pre-commit/CI；不再作全局钩子 |

> v4.11.0（ADR-006）：`model-gateway-gate.py` 已从全局 hooks.json 移除（文件仍在 `hooks/scripts/` 下，未挂载）；是否强制走模型网关是项目架构决策，不应由全局黑名单代替判断。

## 已归档脚本（`scripts/archive/`，仅历史参考）

| 脚本 | 原规则 | 归档原因 |
|------|--------|---------|
| `ai-code-reviewer.py` | RULE-044 | 正则启发式审查误报多，质量低于模型语义分析，由 Linter/测试替代 |
| `api-existence-checker.py` | RULE-045 | 写死 API 知识库过时且不完备，误报真实 API，由类型检查/运行验证替代 |
| `agent_snapshot_manager.py` | RULE-029 | 断点续传由运行时会话能力原生承担 |

## 约定

- **门禁退出码**：`0` = 放行；`2` = 阻断。
- **门禁输入**：命令行参数文件列表，或 stdin 的 hook JSON（`tool_input.file_path`）。
- 无关改动一律放行，避免拖慢正常写入；全量兜底交给 CI（`.github/workflows/ai-security-lint.yml` 等）。
