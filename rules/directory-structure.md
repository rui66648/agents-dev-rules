---
name: directory-structure
version: v1.6.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-14
description: 目录结构唯一真源 — 三层判定 + docs 内部结构（含 RULE-057 的 docs/learning/） + 与磁盘对账纪律 + §3.5 生成任务查重（Look Before You Write） + Cordis 多仓形态口径 + 跨仓工作区（RULE-053）
applies_to:
  agents: ['all']
  phases: ['design', 'build', 'verify', 'operations']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# RULE-053 目录结构（唯一真源）

> **本文件落实**: RULE-053。RULE-052（`rules/root-directory-hygiene.md`）是本文件第 1 层（仓根）的既有表述，其白名单/落点表/命名红线已并入本文件，原文保留为引用与先例记录。
>
> **收编范围**：此前目录结构的规定散在三处——共享根 `AGENTS.md` §4/§5 的骨架模板、`rules/root-directory-hygiene.md` §2–§4 的白名单与落点表、各项目 `tech-stack.md` §3 的结构树。三处自本版本起只保留**引用**，判定口径以本文件为准；改本文件 = 所有项目生效。

## 0. 为什么会散（保留为设计依据）

| 位置 | 原本写什么 | 缺陷 |
|---|---|---|
| 共享根 `AGENTS.md` §4/§5 | 仓根骨架（`cordis.yaml`/`plugins/`/`presets/`/`schemas/`/`hooks/`）+ `docs/`、`schemas/`、日志目录模板 | 假定「单仓 + 仓根即插件基座」，与多仓/代码级插件化的现实不符，导致大面积「规则要求但项目没有」的假缺陷 |
| `rules/root-directory-hygiene.md`（RULE-052） | 仓根白名单 + 产物落点 + 命名红线 + 门禁 | 只判「仓根文件」，一级目录与 `docs/` 内部无判据；且**从未登记**进规则表 / `plugins/registry.yaml` / `applies_to.md` |
| 各项目 `tech-stack.md` §3 | 该仓结构树 | 每仓各写一份，无人负责与磁盘对账，落后于实际目录 |

## 1. 三层判定（唯一口径）

### L1 仓根：只承载入口与配置

- **白名单**：`AGENTS.md` `CLAUDE.md` `README.md` `tech-stack.md` `PROJECT_RULES.md` `PROJECT_NORMS.md` `CUTOVER.md` `PROGRESS.md` `DEPENDENCIES.md` `LICENSE` `NOTICE` `.gitignore` `.gitattributes` `.env*` `.pre-commit-config.yaml` `package.json` `pnpm-lock.yaml` `package-lock.json` `tsconfig*.json` `*.config.{js,ts,mjs,json,yaml}` `verify.ps1` `.kernel-manifest.json` `agent-cmd.json` `docker-compose*.yml`
- **命名红线（禁止落根）**：`_*`、`.tmp*`、`*.tmp.json`、`*.log`、`*.db`、根级 `*.png`、`check_*.ps1|js|mjs|cjs`、`analyze_*`、`batch_*.py`、`debug-*`、`kbp_*`、`*.cer`/`*.pem`/`*.crt`/`*.key`、`*.bak`、`nul`

### L2 一级目录：必须「可核算」，三选一，否则 FAIL

1. **工程目录**——属于 源码 / 部署 / 文档 / 工具 / 数据 / 测试 / 运维 七类之一，**且**出现在该仓 `tech-stack.md` §3 结构树里；
2. **归档与产物目录**——`archive/<用途>-<YYYY-MM-DD>/`、`outputs/`、`test-results/`、`data/`、`migrations/`、`docs/reports/`；
3. **忽略或外部目录**——被 `.gitignore` 明确忽略（`node_modules`、`.wrangler`、`.venv-*`、`dist`、`vendor-refs`、`blobs` 等），或是独立 git 仓（拆分仓、vendored 参考实现）。

> 不属于任何一类即判 FAIL。典型形态：路径事故产物目录（`%SystemDrive%`、`NVIDIA Corporation`、把 `C:\Users\…\electron-builder\…` 拼平成单个目录名）、`undefined`、以及**空目录**（脚本把路径变量拼错留下的壳）。空目录与无内容事故目录可直接移除；有内容的违规物按 §4 归档。

> **判定次序（门禁与本文一致，2026-11-01 收口）**：目录名含 `%`/`:` 的事故形态无条件判 FAIL；其余先看第 3 类（独立子仓 / `.gitignore` 忽略），**已按第 3 类核算的目录即使当前为空也不判违规**（`.wrangler`、`dist` 这类工具态目录空与非空由工具自己决定，不是仓库的违规）。第 1、2 类目录必须登记在 `tools/root-structure.json`（`class` + `reason`），门禁按该清单判「可核算」，清单与磁盘双向对账：漏登记判 FAIL，清单里有而磁盘已不存在的僵尸条目同样判 FAIL。
>
> **僵尸条目的分档（同日修正）**：清单条目对应的目录在磁盘上不存在时，`class: engineering` 判 FAIL（工程目录缺失 = 检出残缺）；`artifact` / `data` / `external` 降为 **WARN**——产物、数据、外部目录本就可能尚未生成（干净的 scratch worktree 里 `outputs/` 不存在是正常态），一律判 FAIL 会让每个并行 worktree 假红，反而逼人把清单改窄。

### L3 产物落点表（唯一一份，取代此前两份重复表）

| 产物类型 | 落点 |
|---|---|
| 分析 / 评审 / 验收报告 | `docs/reports/<主题>-<YYYY-MM-DD>.md`（或 `.html`，同目录）；**同主题只一份，生成前查重见 §3.5** |
| **活图（驾驶舱与十槽图形资产）** | `docs/dashboards/<槽位号>-<slug>.md`（**RULE-054**；与带日期的 `docs/reports/` 分家，**只就地更新、不许另存副本**，判定见 `hooks/scripts/dashboard-registry-check.mjs`） |
| 阶段完成 / 变更说明 | `docs/CHANGELOG.md` 追加 |
| 架构决策 | `docs/decisions/ADR-NNN-<slug>.md` + `docs/decisions/README.md` 索引 |
| 设计文档 | `docs/designs/<YYYY-MM-DD>-<slug>-design.md` |
| **特性规格**（RULE-055，ADR-008） | `docs/tasks/<id>/{spec,plan,tasks}.md`（模板 `templates/spec/`；**门禁按此路径硬编码查找（`spec-clarity-gate.mjs` 的 `docs/tasks`），改落点必须同批改代码**） |
| **学习笔记 / 知识资产**（RULE-057） | `docs/learning/<YYYY-MM-DD>-<slug>.md`（半页模板 `templates/learning/note-template.md`；**一主题一份、只就地更新**，生成前查重见 §3.5，结构判定见 `hooks/scripts/learning-loop-check.mjs`） |
| 研究 / 调研 | `docs/research/<YYYY-MM-DD>-<title>.md` |
| 指南 / 手册 | `docs/guides/` |
| 探针 / 调试脚本 | `tools/`（长期，必须入库）或 `scripts/`（按主题建子目录） |
| 日志 / 截图 / 中间产物 | `outputs/` 或 `archive/<用途>-<YYYY-MM-DD>/` |
| 测试产物 | `tests/fixtures/` 或 `test-results/` |
| 数据库导出 / 临时库 | `data/` 或 `migrations/`（禁止 `*.db` 落根） |
| AI 计划 / 轨迹 | 工具目录（`.trae/documents/`、`.zcode/plans/`） |
| 依赖总览 | `DEPENDENCIES.md`（由 `scripts/update-deps.ps1` 生成，不手写） |
| 工具自动生成的调用日志 | `call_logs/`（或并入 `outputs/`）；审计日志 `audit-logs/` 可选，个人项目可省略 |
| 机器可读契约 | `schemas/{api.jsonschema,db-schema.sql,plugin-interface.jsonschema}`；未采用 Schema-As-Code 的仓按 §5 用代码契约（`kernel/contracts` 等）替代 |
| 派生清单（插件、目录、台账） | 与被描述对象**同仓同目录族**，且必须由脚本生成（见 §3） |

> **提交载体（2026-11-14 增补，v1.6.0；起因：73 篇报告落盘 3 天未进版本库）**：本表所有落进 `docs/`、`tools/`、`tests/`、`schemas/` 的产物，**落盘即视为待交付物，必须随其任务收尾的 commit 进库**（收工节拍第 ③ 步，见各仓 AGENTS.md「收工节拍（四步）」与 `rules/branch-strategy.md` §0.1）。**「文件在磁盘上」不满足本表——可查得 ≠ 会进库**；一次性探针类例外走 `archive/` 或 `outputs/`（不入库路径）。

## 2. `docs/` 内部结构

```text
docs/
├── README.md            # 文档索引（必需）
├── CHANGELOG.md         # 变更说明唯一落点
├── reports/             # 全部报告（含带日期的 .md/.html）
├── decisions/           # ADR + README.md 索引
├── designs/             # 设计文档
├── research/            # 研究文档
├── guides/              # 指南手册
├── dashboards/          # 活图：00 驾驶舱 + 01–09 核心图 + thresholds.md + 派生 registry.json（RULE-054）
├── tasks/               # 特性规格：<id>/{spec,plan,tasks}.md（RULE-055，L2/L3 才有）
├── learning/            # 学习笔记 / 知识资产：<YYYY-MM-DD>-<slug>.md（RULE-057，L1+）
└── <领域目录>/            # architecture、compliance-wiki 等；命名随项目，但必须在 tech-stack.md §3 出现
```

`docs/` 根级只允许入口类文件（`README.md`、`CHANGELOG.md`、`openapi.yaml` 等机器契约）。散文式报告、临时分析、截图一律下沉到对应子目录。

## 3. 结构必须与磁盘对账（不许手写第二份真源）

1. 每仓 `tech-stack.md` §3 是该仓结构树在项目内的**唯一**描述，内容必须能由磁盘核对得出，且改动目录结构时同批更新。
2. 清单类产物（插件清单、目录清单、依赖台账）**必须由脚本从代码/磁盘派生**，并提供 `--check` 漂移门禁；手写清单只允许作为「人读的索引」，不得充当判据。
   - 先例：本规则库的 `plugins/registry.yaml` ← `hooks/scripts/plugin-validator.py --check-registry`（`--check` 非零即不一致）。四仓当前均未实现插件清单派生，本条为形态约定，不代表四仓现状已满足。
3. 门禁脚本：`tools/root-cleanliness-check.mjs` 同时执行 L1 + L2；**FAIL 即任务未完成**，不得声称完成。
4. 收尾节拍：任何批量移动/改名必须在同批生成 `MANIFEST`（from → to 逐条）并在归档目录写 `README.md`。

## 3.5 生成任务查重（Look Before You Write）

> **适用范围**：所有「产出新文件」的生成任务——报告、评估、盘点、差距分析、执行报告、方案、设计文档、HTML 文档中心、README、台账。**写代码与写文档同样适用**。本条只管「同一主题是否已有承载文件」，落点仍按 §1 L3 判；判定口径只此一处，工作流 / 技能 / Agent 里的表述都是本节的落地入口，不得另立标准。

**四步（顺序不可跳）**：

1. **检索**：动手前在目标仓 / 工作区内按主题检索已有产物——文件名关键词、正文标题、`docs/README.md` 索引、根 `README.md` 入口表。范围至少覆盖该主题的「真源目录 + 派生目录 + 索引」。
2. **判定**：命中同主题文件时按三选一处理，**默认落在第 1 类**：

   | 判定 | 条件 | 动作 |
   |---|---|---|
   | **就地修改** | 已有文件是同主题唯一真源且仍有效 | 改该文件，升版本或追加 `docs/CHANGELOG.md`；**不新建第二份**，不另存 `-v2` / `-final` / 带日期副本 |
   | **指针化** | 内容属另一真源的派生 / 呈现 | 只写一行链接 + 一句说明，不复制正文 |
   | **新建** | 检索为空，或已有件已冻结 / 归档 / 明确标注历史依据 | 才允许新建，并在同批登记进索引；文件元信息里写明「检索过哪些路径、为何判定可新建」 |

3. **写入**：就地修改时同步更新入口与索引，避免仍指向旧文件；确需保留的历史版本按 §4 移入 `archive/<用途>-<YYYY-MM-DD>/` 并写 `README.md`，**不删除、不改写冻结仓档案**。
4. **收尾**：同批确认没有留下两份同主题正文。

**一主题一份（受控文档硬约束）**：带编号的受控文档（如项目自定义 `DOC-*` / `REG-*`）与最小核心文档集，同一主题**只允许一份正文真源**。HTML / PDF / 图表是派生呈现层，必须 `fetch` / 链接真源，不得内嵌第二份正文；已有 HTML 模板命中时在该文件上改，不另起一套视觉体系。

**合法例外**（不算重复，但仍需在索引里说明性质，避免下次被误判）：
- 脚本派生的同内容片段（例如一仓一份的 `staged/<repo>/README.md`，由落地脚本生成）；
- 一次性实测快照（带 `pre-` / `post-` 前后语义的取证日志）；
- 冻结仓、`archive/`、`_worktrees/` / worktree 检出的历史副本（按生命周期管理，不改写、不并入真源）；
- **包级结构性入口**（`README.md` / `CHANGELOG.md` / `index.*` / `AGENTS.md`）：一包一份是结构要求，不是同主题重复。查重门禁只对它们**跳过 TOPIC 判定**，内容完全相同仍按 `EXACT` 报 —— 排除误报不等于放过真重复。

**门禁**：`hooks/scripts/duplicate-artifact-check.mjs --root <repo> --check`（**观察期：只输出候选 WARN，退出码恒 0，不挂硬拦截**，登记见 `hooks/configs/gate-inventory.yaml`）。命中候选后由人按本节四步判定；误报清零前不得改成 FAIL 即阻断。

**观察期退出判据**（四条全满足，才允许把 `duplicate-artifact-check` 从 WARN 升为硬拦截；缺一条即继续观察）：
1. **结构性误报清零**：连续 3 次实跑（其中至少 1 次发生在真实生成任务之后）的候选为 0 或全部是已登记合法例外；
2. **正负双向自证通过**：`--selftest` 覆盖精确重复、同主题、不同主题、合法例外、包级结构性入口五类，且证明结构性文件仍参与 `EXACT`；
3. **命中后确实就地修改的实证**：至少 1 条「检索命中 → 改已有文件而非新建」的记录，登记在 `docs/CHANGELOG.md`；
4. **人工复核留痕**：每条候选的判定结论（就地修改 / 指针化 / 合理保留）写进现行执行记录索引，不静默忽略。

未满足前：`gate-inventory.yaml` 保持 `not-integrated`，不挂 `rules/gate.sh`，不改退出码。

> **先例**：example-workspace 2026-11-09 重复审计——`outputs/` 里三份同构执行报告、两份层层吸收的评估文档、两份包级 README 属本节要收敛的对象；`portal/` 冻结仓与 `_worktrees/` 的 16k+ 精确重复副本属合法例外，不作改写。

## 4. 归档纪律（RULE-052 原文口径）

- 发现违规物：移入 `archive/<用途>-<YYYY-MM-DD>/` 并写 `README.md` 说明来源、为何违规、恢复方式；**禁止直接删除**有内容的违规物（保留可查）。
- 例外：空目录与不含文件的事故目录可直接移除。
- 先例：2026-10-15 三十六条 Railway 时代报告 → `docs/reports/root-legacy-2026-10/`；115 个临时文件 + 24 个临时目录 → `archive/root-quarantine-2026-10/`。

## 5. Cordis / 插件化项目的形态口径

共享根 `AGENTS.md` §4/§5 那套仓根骨架（`cordis.yaml`、`plugins/registry.yaml`、`presets/`、`schemas/`、`hooks/`）是**单仓 Cordis 基座的模板示例，不是判定标准**。已采用代码级插件化（kernel 包 + 宿主 + bundle/patch）的仓，满足以下三条即视为结构合规：

1. **插件声明有单一真源**（代码内 `definePlugin` / 声明表 / 席位契约），且有派生清单 + `--check` 门禁；
2. **配置树有唯一落点**并在 `tech-stack.md` §3 写明——`MODEL_PLUGINS`（Worker `[vars]`）或 `cordis.yml` / `cordis.patch.yml` 之一；
3. **vendored 上游有台账**且能与磁盘对账（`.kernel-manifest.json` 或等价物）。

多仓形态（拆分仓 + 冻结母仓）下：母仓只需在 `tech-stack.md` §3 标注各子仓身份与其被 `.gitignore` 忽略的事实；子仓各自满足上述三条。`presets/`、`hooks/` 在项目内的等价物（宿主 profile、`.githooks/`、共享根 `hooks/scripts/`）按 §1 L2 第 1 类核算即可。

## 6. 与其他规则的关系

- RULE-052（根目录洁净）= 本文件 L1 的既有表述，不再重复维护白名单与落点表。
- RULE-051（Cordis 框架优先）管**选型**，本文件管**落点**；某仓是否必须用 `cordis.yaml` 由 §5 判定，不由 RULE-051 推导出目录要求。
- RULE-043（插件清单合规）管插件 frontmatter 字段；本文件 §3 管「清单必须派生 + 漂移门禁」。
- 冲突时按 `rules/priority-system.md` 裁决。

## 7. 跨仓工作区（worktree / 暂存区 / 顶层命名）

本节管**仓外**的物理落点，是 `<PROJECTS_ROOT>` 这一层；仓内结构仍由 §1–§5 判定。

### 7.1 worktree 唯一入口

- 唯一入口：`example-workspace\_worktrees\<repo>\<purpose>-<date>`；`<repo>` 取 `ai|qms|eval|portal`。**日期段与项目分支命名一致**（本仓分支规范为 `<type>/<task>-<MMDD>`，故日期段用 `MMDD`，如 `fix-storagekeys-1113`）；历史迁移批的全日期名（`-2026MMDD`）视为**合规存量**，不回改（2026-11-12 迁移台账已登记）。**本条修正 v1.5.0 的自相矛盾**：原要求 `yyyyMMdd` 却同时要求 `<purpose>` 与分支名一致，两规范必然打架——11-12~11-14 两仓新建 30 棵 worktree 全部回潮 MMDD 实证（不是代理不听话，是听话与听话不可兼得）。
- 禁止在仓内建 `.worktrees/`，禁止在顶层散建新 worktree；顶层 `_worktrees\` 为搬迁前遗留，只减不增，存量按迁移台账逐条消化。
- 搬迁/移动后先 `git worktree repair`，禁止用 `prune/reset/clean` 处理在用 worktree；释放前确认无进程占用。
- 一个 worktree 对应一个批次/分支，命名里的 `<purpose>` 与分支名一致；收尾（`finishing`）后删除 worktree，不保留"备用"副本。

### 7.2 `<staging-workspace>` 固定落点与 TTL

一级只允许以下五类固定落点，新增类型需先改本节：

| 落点 | 存什么 | 保留策略 |
|------|--------|----------|
| `tmp\` | 一次性临时产物、探针、日志备份 | **7 天 TTL**，过期即清；清理前留文件名清单 |
| `logs\` | 运行日志 | 不进 git，按需轮转 |
| `reports\` | 交付报告 | 长期保留，命名 `YYYYMMDD-<主题>.md` |
| `attic\` | 退役残骸归档 | 长期保留原名，逐条登记 `attic\MANIFEST.md`（来源/时间/体积/性质），禁止直接删除 |
| `datasets\` | 数据集等长期资产 | 长期保留，不设 TTL |

- `<staging-workspace>\tools\` 只放本区工具脚本，不存业务产物；根级散落的 `*.ps1`/`*.mjs`/`*.md` 属于待归位项，按 7.2 表迁移。
- 归档不删除：退役物先进 `attic\` 并在 `MANIFEST.md` 记账；密钥类备份单独目录 + 哈希校验记录。

### 7.3 顶层一级命名

- 顶层 = **项目目录 + 规则目录 + README**：
  - 规则真源：`开发流程规则\`（位置钉死，不可移动）
  - 暂存/工具区：`<staging-workspace>\`（**待决策：是否并入 `example-workspace`**，当前作为显式例外保留）
  - 顶层索引：`README.md`
  - 其余每一项都必须是**已登记的项目目录**；登记处 = `<staging-workspace>\tools\ws-allowlist.json` 的 `top_allowed`，未登记即违规。
- **禁止**在顶层新增 `_` 前缀的目录或散文件（临时产物一律进 `<staging-workspace>\tmp\`）。
- 新增顶层项目目录必须先在 `ws-allowlist.json` 登记用途与形态，再创建；项目一律**平铺**，不再建 `personal\` 之类的容器层。
