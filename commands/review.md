---
name: review
version: v1.0.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-08-03
description: 斜杠命令：review - "审查代码"、"code review"、"提交前检查"、"review 一下"
---
# /review - 代码审查

**触发词**: "审查代码"、"code review"、"提交前检查"、"review 一下"

---

## 命令语法

```
/review [target] [--scope=full|diff|file] [--strict=false|true]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `target` | string | 否 | 当前变更 | 审查目标：文件路径、commit 范围（`HEAD~3..HEAD`）、或 PR 链接 |
| `--scope` | enum | 否 | `diff` | 审查范围：`full`（全量）、`diff`（变更差异）、`file`（单文件） |
| `--strict` | bool | 否 | `false` | 严格模式：`true` 时 Blocker 级别问题会阻止合并建议 |

## 触发场景

- 功能开发完成后，提交前进行自我审查
- Pull Request 创建后，请求团队审查
- 代码合并前，最终质量把关
- 发现代码异味或技术债务时，定向审查
- 定期代码健康度检查（全量审查）

## 前置条件

1. 代码已提交到 Git，或已保存到工作区（`--scope=diff` 时）
2. 待审查代码已关联对应的设计文档或需求说明
3. 测试用例已编写（至少核心逻辑有测试覆盖）
4. 代码已通过本地格式化检查（Ruff / Prettier / ESLint）

## 执行流程

1. **加载上下文** — 读取变更描述、关联 Issue/PR、设计文档
2. **确定范围** — 根据 `--scope` 提取待审查的代码范围
3. **分层审查** — 按 Clean Architecture 分层顺序审查：Model -> Repository -> Service -> Router
4. **维度检查** — 依次检查架构合规、编码规范、测试覆盖、安全隐患、性能影响、可维护性
5. **问题分级** — 将发现的问题按 Blocker / Major / Minor / Nit 分级
6. **报告生成** — 输出结构化审查报告，含文件、行号、问题描述、修改建议
7. **决策建议** — 给出 "通过 / 有条件通过 / 不通过" 的审查结论

## 产出物

- **审查报告**：按维度分类的问题汇总，标注严重程度和具体位置
- **问题清单**：可执行的修改项，按 Must Fix / Should Fix / Nice to Have 排序
- **架构合规评估**：分层架构是否被破坏，跨层调用是否被引入
- **技术债务记录**：新引入的技术债务与历史债务变化
- **审查结论**：通过 / 有条件通过 / 不通过

## 错误处理

| 常见错误 | 处理方式 |
|----------|----------|
| 无法获取 diff（未提交代码） | 提示先执行 `git add && git commit` 或使用 `--scope=file` |
| 缺少设计文档 | 标记为风险，要求补充需求上下文后再审查 |
| 测试覆盖率为 0 | 标记为 Blocker，要求补充测试用例 |
| 发现 Blocker 级安全问题 | 立即标记审查不通过，要求修复后重新审查 |
| 审查范围过大（>50 文件） | 建议拆分为多次审查，或缩小 `--scope` |

## 示例

### 示例 1：提交前审查当前变更

```
/review
```

**预期输出**：
- 审查 HEAD 与上次提交之间的 diff
- 输出 3 个 Minor 问题、1 个 Major 问题
- 结论：有条件通过，需修复 Major 问题

### 示例 2：严格审查指定文件

```
/review src/services/user_service.py --scope=file --strict=true
```

**预期输出**：
- 对 `user_service.py` 进行全量逐行审查
- 输出编码规范、类型注解、Docstring 完整性检查结果
- 结论：通过（严格模式下无 Blocker 问题）

---

**执行流程**: 遵循 [code-review 技能](skills/code-review/SKILL.md`) 的完整流程

**产出物**: 审查报告 + 改进建议 + 修改清单
