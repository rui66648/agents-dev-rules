---
name: verify
version: v1.1.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-11-07
description: 斜杠命令：verify - "验证一下"、"检查完成"、"确认通过"、"测试结果"；L2/L3 追加规格收敛检查（FR 覆盖 + spec 门禁）
---
# /verify - 完成前验证

**触发词**: "验证一下"、"检查完成"、"确认通过"、"测试结果"

---

## 命令语法

```
/verify [scope] [--type=unit|integration|spec|manual|all]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | string | 否 | 当前变更 | 验证范围，如 `auth-module`、`user-api` |
| `--type` | enum | 否 | `all` | `unit`（单元测试）、`integration`（集成测试）、**`spec`（规格收敛）**、`manual`（手动验证）、`all`（全部） |

## 触发场景

- 每个逻辑单元完成后，声称"完成"之前（RULE-004 强制要求）
- 代码审查前，需要确认所有验证步骤通过
- 分支收尾前，需要确认无遗漏
- 部署前，需要确认功能完整性
- **executing-plans 收敛判据第 3 条**：跑规格门禁确认无遗留澄清 / 无漂移 / FR 全覆盖

## 前置条件

1. 代码实现已完成（executing-plans 步骤完成）
2. 测试代码已编写（test-driven 步骤完成）
3. 所有已知编译错误已修复
4. **L2/L3**：spec 无遗留 `[NEEDS CLARIFICATION]`（有遗留先问）

## 执行流程

1. **加载验证合约** — 从设计文档读 Verification Contract；从 `docs/tasks/<id>/spec.md` 读 FR 与验收场景
2. **执行验证** — 按 `verify_steps` 逐项执行命令或操作
3. **规格收敛**（L2/L3）— 逐 FR 对照测试；跑
   `node <规则库根>/hooks/scripts/spec-clarity-gate.mjs --root <仓根>`
4. **结果比对** — 将实际输出与 `confirm` 成功信号比对
5. **状态判定** — 通过/不通过；**未收敛不得进 code-review**
6. **报告输出** — 生成验证报告（含命令实际输出 + 规格收敛结论）

## 产出物

- 验证报告（markdown 格式，含命令实际输出）
- **规格收敛报告**（L2/L3）：FR 覆盖表 + 门禁 PASS/FAIL
- 通过/不通过结论
- 失败项清单与修复建议

## 错误处理

| 常见错误 | 处理方式 |
|----------|----------|
| 验证步骤失败 | 定位失败原因，修复后重新验证 |
| 设计文档缺少验证合约 | 提示补充 Verification Contract |
| 测试环境未就绪 | 提示启动测试环境（数据库、Mock 服务等） |
| spec 门禁 FAIL（漂移/遗留澄清/FR 未覆盖） | 留在 executing-plans 修；规格本身有误则升 `spec_version` 改规格后重跑 |

## 示例

```
/verify auth-module --type=all
```

**预期输出**：
- 单元测试：12 passed, 0 failed
- 集成测试：5 passed, 0 failed
- 规格收敛：FR-001…005 全部有对应测试；门禁 PASS（1 份 spec、5 条 FR）
- 手动验证：3/3 步骤通过
- 结论：验证通过，可进入 code-review

---

**执行流程**: 遵循 [verification 技能](skills/verification/SKILL.md`) 的完整流程
**负责代理**: `test-engineer`
**规则**: `rules/spec-driven.md`（RULE-055 §3/§4）