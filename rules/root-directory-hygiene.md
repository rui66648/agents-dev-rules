---
name: root-directory-hygiene
version: v2.1.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-14
description: 根目录洁净（RULE-052）— 仓根只承载入口与配置；白名单、落点表与命名红线已统一至 RULE-053 目录结构唯一真源
applies_to:
  agents: ['all']
  phases: ['build', 'verify', 'operations']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# RULE-052 根目录洁净（Root Directory Hygiene）

> **优先级**：强制 ｜ **适用范围**：所有项目仓库
>
> **v2.0.0 收编声明**：本规则是 `rules/directory-structure.md`（**RULE-053 目录结构唯一真源**）第 1 层（仓根）的既有表述。
> 白名单、产物落点表、命名红线**不再在本文件维护**，一律读 RULE-053 §1/§2；本文件只保留原则、流程与先例。

## 1. 唯一原则
仓库根目录只承载『入口与配置』，不承载『产物』。任何由 AI 或脚本生成的报告、探针、日志、截图、临时数据、一次性脚本，一律不得落在仓库根目录。

## 2. 判定口径（引用，不复制）
- 仓根白名单与命名红线 → RULE-053 **§1 L1**
- 一级目录必须「可核算」（工程目录 / 归档产物 / 忽略或外部） → RULE-053 **§1 L2**
- 各类生成物的正确落点 → RULE-053 **§1 L3 + §2（docs 内部结构）**
- 归档纪律（移入 `archive/<用途>-<YYYY-MM-DD>/` 并写 `README.md`，禁止直接删除有内容物） → RULE-053 **§4**

## 3. 强制流程
1. **生成前先定落点**（RULE-053 §1 L3）；不确定一律用 `docs/reports/`。
2. 任务收尾运行门禁：`node tools/root-cleanliness-check.mjs` —— **FAIL 即任务未完成**，不得声称完成。
   门禁同时判 L1（仓根文件）与 L2（一级目录可核算）；只查文件名不查目录的旧版会给出假绿。
3. 发现违规物：按 RULE-053 §4 归档，同批写 `MANIFEST`（from → to）与归档目录 `README.md`。

### 3.1 门禁红处置协议（2026-11-14 增补，v2.1.0；起因：3 天 38 次绕行实证「红 → 绕过」成为默认路径）

root-cleanliness（及同类结构门禁）判 FAIL 时，**唯一合法动作是处置，不是绕行**：

1. **三选一处置**（在**下一个 commit 之前**完成）：
   - **清理**：违规物是临时产物 / 空壳 / 事故目录 → 直接移除或按 §3 归档（归档不删除）；
   - **归位**：违规物是在途工作（典型：仓根散建的 `_wt-*` worktree）→ 迁入 `example-workspace\_worktrees\<repo>\` 规范位并 `git worktree repair`；
   - **登记**：违规物是长期合法目录 → 在 `tools/root-structure.json` 登记 `class` + `reason`。
2. **禁止用 `--no-verify` 绕过结构类门禁失败**（root-cleanliness / gen-tech-stack 漂移）；`--no-verify` 仅保留给非结构类失败（环境缺失等）且须注明原因。
3. **无主违规物**（找不到归属工作线）由**接手的下一个代理**负责处置——「应由其归属工作线自行归入」不构成跳过理由（2026-11-12~14 同一句话在豁免理由里出现 15 次实证）。
4. **豁免计量**：同日同因豁免 ≥3 次 = 门禁或流程缺陷信号，当日修复或登记整改项（计量见 `hooks/scripts/branch-hygiene-check.mjs` C2）。

## 4. 判定
根目录门禁 FAIL = 任务未完成。确有临时例外必须在交付说明中显式声明：文件、用途、清理时间。

## 5. 先例（本项目落地记录）
- 2026-10-15：36 份 Railway 时代报告 → `docs/reports/root-legacy-2026-10/`
- 2026-10-15：115 个临时文件 + 24 个临时目录 → `archive/root-quarantine-2026-10/`
- 2026-10-15：新增门禁脚本 `tools/root-cleanliness-check.mjs`（零依赖）
- 2026-11-01：三处分散的目录结构规定收编为 RULE-053；门禁补 L2 目录判定（此前 `%SystemDrive%`、`NVIDIA Corporation`、空目录等路径事故产物全部漏判）
