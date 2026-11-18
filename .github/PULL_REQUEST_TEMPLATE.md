# PR 模板

> 提交前请先阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)。CI 会强制校验规则登记与门禁自证。

## 变更描述

<!-- 这次改了什么？为什么改？ -->

## 类型

- [ ] 规则（`rules/`）
- [ ] 技能（`skills/`）
- [ ] 命令 / 子代理（`commands/`、`agents/`）
- [ ] 门禁脚本（`hooks/`）
- [ ] 模板 / 契约（`templates/`、`schemas/`）
- [ ] 文档
- [ ] 修复

## 关联规则

<!--
若改动规则正文，列出涉及的规则编号（如 RULE-055）。
非规则改动填「不适用」。
-->
规则编号：

## 校验结果

<!-- 全部必须为 ✅ 才能合并 -->

- [ ] `python scripts/rules-consistency-check.py` 通过
- [ ] `python scripts/rule-liveness-check.py` 通过
- [ ] `python hooks/schema-validator.py --all --fail-on-violation` 通过
- [ ] 新增/修改的门禁脚本已实现 `--selftest` 并通过

## 检查项

- [ ] 未提交任何真实密钥、内网地址、个人绝对路径
- [ ] 新增脚本未硬编码绝对路径（用 `__file__` / `__dirname` 自解析）
- [ ] 规则正文与 `AGENTS.md` §2 入口路由、§3 速查表、`rules/applies_to.md` 三处一致
- [ ] 新增规则/技能已在入口登记（否则视为结构性失效）

## AI 生成内容

<!-- 若含 AI 生成内容，填写此项 -->

- 生成工具：
- 人工审查要点：
- 已知局限：
