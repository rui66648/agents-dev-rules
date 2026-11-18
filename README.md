# agents-dev-rules

> 面向 AI 编码代理（Claude Code / Cursor / Codex / Trae / Qoder / DeepSeek Harness 等）的**开发流程规则仓库**。
> 把「怎么写代码、怎么评审、怎么提交、怎么收工」固化成可执行、可校验、可继承的规则与门禁。

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/rui66648/agents-dev-rules/actions/workflows/ci.yml/badge.svg)](https://github.com/rui66648/agents-dev-rules/actions/workflows/ci.yml)
[![rules](https://img.shields.io/badge/rules-40%20%E6%9D%A1-informational)](rules/)
[![skills](https://img.shields.io/badge/skills-28%20%E4%B8%AA-informational)](skills/)

---

## 这是什么

一套**与具体技术栈无关**的工程流程规范层。它不写业务代码，而是回答：

- 收到一个需求，从哪一步开始？（入口路由）
- 什么情况下必须先写设计/规格，什么时候可以直接改？（分级门禁）
- 代码写完要过哪些检查？（确定性门禁脚本）
- 一个任务怎么算真正结束？（收工节拍）
- 踩过的坑怎么沉淀成下次的规则？（学习闭环）

## 三个核心组成

| 组成 | 位置 | 作用 |
|------|------|------|
| **规则** | [`rules/`](rules/) — 40 条 | 唯一的规则正文真源。每条带 frontmatter（版本 / 适用范围 / 强制级别） |
| **技能** | [`skills/`](skills/) — 28 个 | 任务级 SOP。规则说「要做什么」，技能说「怎么做」 |
| **门禁** | [`hooks/`](hooks/) | 确定性校验脚本。把规则变成能跑、会失败的检查，而非口头约定 |

配套还有 [`commands/`](commands/)（斜杠命令）、[`agents/`](agents/)（子代理定义）、[`templates/`](templates/)（产物模板）、[`schemas/`](schemas/)（契约）、[`.github/workflows/`](.github/workflows/)（CI）。

## 快速开始

```bash
git clone https://github.com/rui66648/agents-dev-rules.git
cd agents-dev-rules

# 装到你的项目（推荐：Junction 软链，始终取最新版）
pwsh scripts/init-project-rules.ps1 -TargetProject /path/to/your-project
```

装完后，在目标项目的 `AGENTS.md` 写一行指针：

```markdown
> 本项目使用 `<RULES_ROOT>\AGENTS.md`（始终取共享规则最新版）作为通用构建规则入口。
```

代理会按 `AGENTS.md` §2 的**入口路由**按需读取对应规则——不会预载全部 40 条。

## 规则编号速览

| 编号 | 主题 | 落点 |
|------|------|------|
| RULE-001~010 | 基础工程纪律（结构、命名、提交、分支） | `rules/directory-structure.md` 等 |
| RULE-030~033 | Schema-As-Code 契约 | `rules/schema-as-code.md` |
| RULE-034~036 | 前端组件契约（选型 / 元数据 / 组合校验） | `rules/component-selection-rules.md` |
| RULE-041 | 模型网关接入（项目级可选） | `rules/adlc-lifecycle.md` |
| RULE-051 | Cordis 框架优先（Agent 运行时能力域） | `rules/open-source-first.md` |
| RULE-053 | 目录结构与产物落点 | `rules/directory-structure.md` |
| RULE-055 / 056 | 规格驱动开发（SDD）/ Spec-Kit 映射 | `rules/spec-driven.md`、`rules/spec-kit.md` |
| RULE-057 | 开发学习闭环 | `rules/dev-learning-loop.md` |
| RULE-058 | 系统基线 | `rules/system-baseline.md` |

> 完整清单见 [`AGENTS.md`](AGENTS.md) §3。

## 本地校验

所有门禁都能在无依赖环境跑（只需 Python 3.10+ 与 PyYAML）：

```bash
pip install pyyaml

python scripts/rules-consistency-check.py   # 规则索引双向对齐 + 悬空路径
python scripts/rule-liveness-check.py       # 规则是否「结构性失效」（四件套齐备性）
python hooks/schema-validator.py --all --fail-on-violation
python hooks/scripts/health-check.py        # 引用完整性 + 配置一致性
```

门禁脚本均支持 `--selftest`，用负向注入自证——**防止门禁给出假绿**。

## 设计原则

1. **文件即真源**：规则正文只在 `rules/` 一处，其余位置（速查表、索引、生成物）都是派生视图，由脚本对账。
2. **规则可执行**：每条落点规则必须配齐四件套——**触发入口 / 产物落点 / 模板 / 判据**。缺任一件视为结构性失效，由 `rule-liveness-check.py` 拦截。
3. **分级而非一刀切**：按任务体量分 L0~L3，L0/L1 不要求落盘规格，避免把 SDD 变成 Markdown 瀑布。
4. **门禁确定性**：能用脚本判的绝不用人判。`--selftest` 是门禁自身的准入条件。
5. **版本不锁**：引用共享规则的项目统一写「始终取最新版」，避免 N 个项目各维护一份版本锁。

## 目录结构

```
agents-dev-rules/
├── AGENTS.md              # 入口路由 + 规则速查表（规则体系的根）
├── rules/                 # 规则正文真源（40 条）
├── skills/                # 任务级 SOP（28 个）
├── commands/              # 斜杠命令定义
├── agents/                # 子代理定义
├── hooks/
│   ├── scripts/           # 确定性门禁脚本
│   └── configs/           # 门禁配置
├── templates/             # 产物模板（设计 / 规格 / 计划 / pre-commit）
├── schemas/               # JSON Schema 契约
├── components/            # UI 组件元数据库
├── scripts/               # 运维与校验脚本
├── docs/guides/           # 插件清单标准等指南
└── .github/workflows/     # CI
```

## 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。核心要求：

- 改规则正文 → 同步速查表与索引 → 跑 `rules-consistency-check.py` 与 `rule-liveness-check.py` 必须 PASS
- 新增技能 → 在 `skills/` 下建目录 + `SKILL.md`（带 frontmatter），在 `commands/` 或 `agents/` 登记
- 禁止把任何真实密钥、内网地址、个人路径提交进仓库

## 安全

发现安全问题请勿直接开公开 issue，见 [SECURITY.md](SECURITY.md)。

## 致谢

本仓库脱胎于一个多仓 AI 并发开发工作区的实战沉淀——所有规则都来自真实的门禁拦截与事故复盘，而非纸上设计。

## 许可证

[Apache License 2.0](LICENSE)
