---
name: cicd-rules
version: v4.4.4
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-11
description: CI/CD 规则 — 门禁现状真源 + pre-commit/Docker Compose/CD 配置模板（RULE-007）
applies_to:
  agents: ['architect', 'backend-developer']
  phases: ['deploy', 'implementation']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# CI/CD 规则 — 个人开发者精简版
> **本文件落实**: RULE-007（CI/CD 遵循 cicd-rules.md）

> **版本**: v4.4.3 | **更新**: 2026-11-05
> **变更说明**: v4.4.3 把 `trailing-whitespace` / `end-of-file-fixer` 移出默认 stage（`stages: [manual]`）：默认 `run --all-files` 零写入，只在显式 `--hook-stage manual` 时修复（此前全量运行会一次性改写 709 处空白，只能靠 `git diff -w` 反推回滚）。v4.4.1 把 check-yaml 的 6 处失败修至 Passed（3 个 `cordis.patch.yml` 的 `!js` 自定义 tag 用 `exclude` 排除而非全局 `--unsafe`；`regulation-index.yml` 加 `--allow-multiple-documents`；`docs/openapi.yaml` 去掉 Markdown 头与围栏、改为纯 YAML），§门禁现状 该行由「未全绿」改为实测「上游 4 项 2 绿 2 红」（trailing-whitespace / end-of-file-fixer 因存量纯空白仍红，批量改写已回滚）。v4.4.0 回填 portal 的 pre-commit 实测结果（4.7.0 已装；trailing-whitespace / end-of-file-fixer 首跑自动修复后复跑 Passed；check-yaml 6 处真实失败；check-added-large-files Passed），并把该行从「未启用」改为「已安装但 check-yaml 未清零」。v4.3.0 在 §门禁现状 补记三仓（ai/qms/eval）已挂载共享规则门禁，并新增 `--no-verify` 逃生口径（允许情形 / 批准人 / 留痕）。v4.2.0 新增 §门禁现状作为「规则 ↔ 实现」唯一真源（此前多份规则各自声称 pre-commit 已阻断，实际四仓均未安装钩子）；修正 `ui/new-ui/src/` 旧路径与 `scripts/deploy.sh` 误导表述，明确部署脚本为项目自建、本规则库不含实现。

---

## 核心规则

| 编号 | 规则 | Enforcement 路径 |
|------|------|------------------|
| RULE-007 | CI/CD 遵循本规则 | 手动执行 + 项目自建钩子（见 §门禁现状） |

---

## 门禁现状（唯一真源）

> 本表是「规则声称的门禁」与「真实存在的实现」之间的唯一对账口径。其他规则文件只引用本节，不各自声明"已阻断"。

| 门禁 | 实现位置 | 当前状态（2026-11-12 复核） |
|------|----------|------------------------------|
| 共享规则门禁（结构洁净 + 规则一致性） | 各仓 `.githooks/pre-commit`（`core.hooksPath=.githooks`） | **已启用（三仓）**：`example-workspace/{ai,qms,eval}` 于 2026-11-04 挂载，串行执行 `hooks/scripts/root-cleanliness-check.mjs --root <repo>` → `scripts/rules-consistency-check.py`，任一非 0 即拦截；`node`/`python` 缺失时 fail-closed 而非静默放行。`portal` **挂载就绪但推迟落地**（2026-11-05）：两条门禁对 portal 试跑均 PASS，且已备好 framework local hooks 配置；但因本仓暂存区正被另一会话以 3,327 条 `frozen/` 纯 rename 占用（在途事务），framework 要求 `.pre-commit-config.yaml` 必须 staged 才能执行——staged 会把配置混入他人在途提交， unstaged 会在其下次 commit 时触发「configuration is unstaged」拦截，两者均不可接受，故配置变更已回退、待该事务结束后再挂；因本仓 AGENTS.md 有「允许 main 直接提交」偏差声明，届时也不挂 main 分支保护 |
| 本地 pre-commit（secret / schema / component） | 各仓 `.pre-commit-config.yaml` | **portal 已装、默认只读 2 项全绿**（2026-11-05 实测，pre-commit 4.7.0，`.git/hooks/pre-commit` 已生成，`core.hooksPath` 为空）：默认 `run --all-files` 只跑 `check-yaml`、`check-added-large-files`，均 **Passed** 且**零写入**（`git status --porcelain` 行数运行前后一致）；`trailing-whitespace` / `end-of-file-fixer` 于 2026-11-05 **移出默认 stage（`stages: [manual]`）**——只在显式 `--hook-stage manual` 时修复（此前全量运行会一次性改写 709 处空白，只能靠 `git diff -w` 反推回滚）；本地两项（ai-security-lint / component-validator）仍 `stages: [manual]` 且标注未启用；**2026-11-05 拟追加 2 条自动启用 local hooks（root-cleanliness + rules-consistency，试跑 PASS），但因暂存区被另一会话 3,327 条 staged rename 占用而回退推迟，见上表共享门禁行**。`ai/qms/eval` **未装**（无配置文件、无 `.git/hooks/pre-commit`） |
| Agent 钩子（`hooks/hooks.json`：secret-scan / schema-gate / plugin-gate / post-test） | 本规则库 `hooks/` | **已挂载（四仓，2026-11-05）**：`example-workspace/{ai,qms,eval,portal}` 均落 `.claude/settings.json`（绝对路径引用本库脚本，脚本按 `__file__` 定位、`git diff --cached` 按触发时项目根取暂存区），覆盖 secret-scan（PreToolUse×Bash）与 schema-gate/plugin-gate（PreToolUse×Write/Edit）；`post-test.js`（PostToolUse×Bash，60s）**未挂载**——每条 Bash 后强制跑测试开销过重且与各仓 `verify.ps1`/`npm test` 流程重叠，取舍已记录 |
| 规则库一致性 | `scripts/rules-consistency-check.py` | **可手动执行**，退出码 0/1；仅支持 `--verbose`，无重复检测 |
| 结构洁净 | 各仓 `tools/root-cleanliness-check.mjs` → 本库 canonical | **可手动执行**；四仓均已接入，2026-11-04 实测 ai/qms/eval/portal 退出码 0 |
| 看板注册 | 各仓 `tools/dashboard-check.mjs` → 本库 canonical | **部分接入**：`portal`、`qms`、`eval` 已接入（`portal` 10 槽 0 在用，空跑通过）；`ai` 无启动器 |
| 一键门禁 | `rules/gate.sh` | **可用**：步骤 1–3 通过；已移除废弃的 RULE-029 冒烟步（v4.2.0） |
| 服务端 main 保护（`--no-ff` ≥2 父） | `ai/.githooks/pre-receive` | **未落地（2026-11-12 实测）**：脚本已随仓提交，但 `pre-receive` 属服务端钩子，需安装到接收 push 的裸仓/远端；`.git/hooks/pre-receive` 实测不存在，`core.hooksPath=.githooks` 只让客户端钩子生效。脚本注释记录「`main` 最近 40 个提交里 23 个单父直接提交」→ 历史已被绕过。**不得写成「由钩子阻断」**；本地补偿为 `tools/kg-main-audit.mjs` 与 `tools/branch-governance-check.ps1` 的只读巡检。GitHub 托管仓不支持自定义 pre-receive，若不自建接收端，应改用分支保护规则 + PR 合并策略 |
| 分支 / Worktree 治理巡检 | `ai/tools/gc-branches.ps1`（全量 dry-run，已进 main @ `511b1d1`）、`ai/tools/branch-governance-check.ps1`（四仓只读巡检） | **可手动执行、无自动调度（2026-11-12 复核）**：`gc-branches.ps1` 默认 dry-run、`-Apply` 才执行 T1/T2，只用 `git branch -d`、永不删远端；全仓无 CI/cron 引用，`.github/workflows` 0 命中。CI 按本表不承担规则门禁，故巡检保持本地手动执行，挂 `ai/AGENTS.md:24` 收工节拍；**不要**把本地 worktree 巡检挂到 CI（CI 上 `worktree list` 只见单检出，结果无意义） |
| 部署脚本 | 项目自建 | **本库不含** `scripts/deploy.sh`、`scripts/update-deployed.py`，需项目按 §部署流程 自行实现 |
| 云端测试 CI（instabox-medium） | 各仓 `.github/workflows/*.yml`（`runs-on: instabox-medium`） | **起步（2026-11-07）**：`example-workspace-qms` 分支 `ci/instabox-runner-1107` 三条 job 改跑 instabox-medium（typecheck/test，免费档 4c8G）；GitHub App 连接与首次云端执行**待验证**。部署仍走各仓 `deploy/deploy.ps1`，CI 不承担部署与规则门禁 |

**口径**：上表状态为「无自动保护」时，规则不得写成"由 pre-commit 阻断"，必须写"手动执行 X"。新增门禁时同步更新本表，并在 `AGENTS.md` 速查表标注实现位置。

**示例代码块占位符约定**：本文所有 workflow / 配置示例中，凡指向**项目侧自建**脚本的路径，
一律写成 `<your-xxx>.py` / `<your-xxx>.sh` 尖括号占位形式，**不写真实文件名**。
原因：`rules-consistency-check.py` 会把规则正文里指向不存在文件的路径判为悬空（FAIL）——
写真实文件名要么触发误报，要么逼着给检测器开白名单（那就是自我豁免）。占位符既让示例保持
"照抄前先自己实现"的提醒，也让检测器无需为示例破例。

### `--no-verify` 逃生口径

`git commit --no-verify`（`-n`）会跳过全部本地钩子——包括 main 分支保护与上表两条共享检查——因此按例外流程管理，不得作为常规手段。

| 维度 | 口径 |
|------|------|
| 允许情形 | ① 线上故障热修，需先落最小回滚/修复，24h 内补跑门禁并单独提交补正；② 钩子自身故障（共享实现或 node/python 工具链损坏）导致正常提交被误拦，须同时在 issue 或提交说明记录现象与复现步骤；③ 纯文档/非代码变更且结构门禁误伤（必须临时落在仓根）。 |
| 不允许 | 常规功能开发、重构、依赖升级；为掩盖规则库一致性 FAIL 或结构违规而绕过；批量提交时统一加 `-n`。 |
| 批准人 | 单人项目 = 仓库所有者本人（口头即可）；多人协作 = 该仓 owner 在提交说明中明确批准（`Approved-by: <owner>`）。无第二人在场时不得自行批准。 |
| 留痕 | 提交说明首行前缀 `[no-verify]`，正文写「原因 / 批准人 / 补验证计划」；禁止用 `--amend` 或 force-push 抹掉该记录。 |
| 补救 | 下一提交前手动执行 `node <RULES_ROOT>/hooks/scripts/root-cleanliness-check.mjs --root <repo>` 与 `python <RULES_ROOT>/scripts/rules-consistency-check.py`，两者归零后方可继续。 |

---

## 个人开发者 CI/CD 架构

### 方案一：本地开发（推荐）

```yaml
# Makefile（简化构建）
.PHONY: dev up down test lint

dev:
    docker compose up -d

up:
    docker compose up

down:
    docker compose down

test:
    pytest tests/ -v --cov=src --cov-report=term-missing

lint:
    ruff check src/
    eslint src/

format:
    black src/
    prettier --write src/
```

```bash
# 一键部署脚本（项目自建：本规则库不含 scripts/deploy.sh，
# 需在项目内实现并保证幂等、可回滚）
./scripts/deploy.sh
```

### 方案二：GitHub Actions（可选）

如需云端 CI，使用简化流水线：

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      
      - name: Run linters
        run: |
          ruff check src/
          pylint src/
      
      - name: Run tests
        run: pytest tests/ -v --cov=src --cov-fail-under=60
      
      - name: Security scan
        run: bandit -r src/ -ll
```

### 方案三：CD 自动部署（推荐）

> **为什么推荐**：手动 `ssh + docker compose pull` 容易漏拉新镜像、漏执行迁移、忘记打 tag，是「本地好了、线上还是旧的」的直接根因。tag 触发的自动部署让「push tag → 构建 → 部署 → 健康检查 → 更新 .deployed.json」全链路自动化。
>
> **示例中的自建脚本**：下面的 workflow 是**示例**，其中 `scripts/update-deployed.py`
> 与「部署流程」一节里的 `scripts/deploy.sh` 均为**项目侧自建**——本规则库**不含**这两个文件
> （见 §门禁现状表「部署脚本」行）。照抄前先在项目内实现它们，或把该步骤替换为
> `wrangler deploy` 等平台等价动作。

```yaml
# .github/workflows/cd-production.yml（tag 触发自动部署）
name: CD Production

on:
  push:
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build & push image
        run: |
          docker build -t registry.example.com/app:${{ github.ref_name }} .
          docker push registry.example.com/app:${{ github.ref_name }}

      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /path/to/project
            docker compose pull
            docker compose up -d
            docker compose exec app alembic upgrade head

      - name: Health check
        run: |
          sleep 10
          curl -fsS https://your-server.com/health || exit 1

      - name: Update .deployed.json
        # 项目侧自建脚本（本规则库不含），或换成 wrangler deploy 等平台等价动作
        run: |
          python scripts/<your-deploy-marker>.py --version ${{ github.ref_name }}
```

> **部署流程对应**：`git tag vX.Y.Z` → 推送 tag → 自动构建/部署/健康检查 → 更新 `.deployed.json`（RULE-020 推荐项）。若项目部署到 Cloudflare Pages/Workers，将 `deploy` 步骤替换为 `wrangler deploy` 即可（见 `rules/deploy-records.md`）。

---

## Pre-commit Hooks（建议配置，当前未启用）

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        args: [--fix, --ext .tsx,.ts,src/]

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black  # 注意：ruff-format 已可替代 black，新项目建议只用 ruff

  - repo: local
    hooks:
      - id: alembic-check
        name: Check Alembic migrations
        entry: bash -c 'if [ -n "$(alembic check)" ]; then echo "Migration needed"; exit 1; fi'
        language: python
        pass_filenames: false
        always_run: true
```

---

## 取消的企业级功能

| 原功能 | 简化后 |
|--------|--------|
| 完整 GitHub Actions 流水线 | **CD 自动部署推荐**（tag 触发），CI 以本地 Makefile + pre-commit 为主 |
| CI 门禁（所有测试必须通过） | **降级为 pre-commit hook** |
| 部署后自动更新 .deployed.json | **CD 流水线自动更新**（推荐），或 git tag + 手动更新 |
| Span 消耗监控 | **无需**（个人项目无配额限制） |
| Agent SLO 监控 | **无需**（单实例部署） |
| Feature Flag 灰度发布 | **使用环境变量开关替代** |

---

## 部署流程（简化版）

```bash
# 1. 本地测试
make test lint

# 2. 提交代码（feature 分支 + PR，禁止直推 main —— RULE-012）
git checkout -b feat/user-profile
git add .
git commit -m "feat: add user profile endpoint"
git push origin feat/user-profile
# 在平台发起 PR 合并，main 由 CI / 分支保护规则更新

# 3. 部署到线上（推荐：tag 触发 CD 自动部署；无 CD 时手动执行）
git tag v1.2.0
git push origin v1.2.0
# 有 CD 流水线 → 推送 tag 自动构建/部署/健康检查
# 无 CD 流水线 → 手动执行：
#   ssh server "cd /path/to/project && docker compose pull && docker compose up -d"

# 4. 更新部署记录
#   CD 自动更新 .deployed.json，或手动按 deploy-records.md 更新
```

---

## 安全扫描（必须）

```bash
# 后端安全扫描
bandit -r src/ -ll
pip-audit

# 前端安全扫描
npm audit --production
```

---

## Enforcement

- **必须**: pre-commit hooks（ruff + eslint + black）
- **可选**: GitHub Actions（如需云端 CI）
- **降级**: CI 门禁 → pre-commit 门禁
- **取消**: Span 监控、SLO 监控、灰度发布
