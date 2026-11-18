#!/usr/bin/env bash
#
# rules/gate.sh - 本地一键规则门禁
#
# 在提交 / 合并前运行，确定性强制以下铁律：
#   1. 规则库一致性审计（scripts/rules-consistency-check.py）
#      —— 含 7 项：速查表位置/编号唯一/索引双向/版本三方/悬空路径/License 交叉/选型 ADR
#   2. Schema-As-Code 契约校验（hooks/schema-validator.py）
#   3. Schema 门禁（hooks/scripts/schema-gate.py）
#   4. Agent 生成代码 Linter（hooks/scripts/agent_linter_checker.py --ci）
#   5. 规格驱动门禁（hooks/scripts/spec-clarity-gate.mjs，RULE-055/056）
#
# **不在本脚本内的铁律门禁**（可达性说明，别以为跑了 gate.sh 就全过了）：
#   - RULE-052/053 目录结构：node hooks/scripts/root-cleanliness-check.mjs --root .
#   - RULE-054 项目图形资产：node hooks/scripts/dashboard-registry-check.mjs --root .
#   两者由各仓 tools/ 启动器单独触发；未并入本聚合脚本的原因见
#   hooks/configs/gate-inventory.yaml 的 integration/reason 字段。
#（2026-11-07：新增 spec 门禁后补此说明，避免"新门禁进了聚合脚本、老门禁没有"造成可达性错觉。）
#
# 注：原第 5 步「Agent 模块冒烟测试（RULE-026/027/029）」已删除——RULE-029 于 v4.11.0 废弃，
# 对应模块已移至 hooks/scripts/archive/，该步会让门禁永久 FAIL；本注释行由 v4.14.2 清理移除。
#
# 用法：
#   bash rules/gate.sh [--skip-linter] [--skip-spec]
#
# Windows 注意：PATH 上的 `bash` 可能解析到未安装的 WSL stub（System32\bash.exe），
# 需使用 Git Bash 显式路径运行：
#   "C:\Program Files\Git\bin\bash.exe" rules/gate.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Python 启动器：优先 uv（若安装），否则回退系统 python（v4.10.1 修复：uv 未安装时门禁全挂）
if command -v uv >/dev/null 2>&1; then
  PY="uv run python"
else
  PY="python3"
  command -v python3 >/dev/null 2>&1 || PY="python"
fi

SKIP_LINTER=0
SKIP_SPEC=0
for arg in "$@"; do
  case "$arg" in
    --skip-linter) SKIP_LINTER=1 ;;
    --skip-spec) SKIP_SPEC=1 ;;
  esac
done

FAILED=0

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m  ✓ %s\033[0m\n' "$*"; }
fail() { printf '\033[1;31m  ✗ %s\033[0m\n' "$*"; FAILED=1; }

# 1. 规则库一致性审计（7 项，含 RULE-017/019 的选型 ADR 存在性）
step "规则库一致性审计（位置/编号/索引/版本/悬空路径/License/选型 ADR）"
if $PY scripts/rules-consistency-check.py; then ok "rules-consistency"; else fail "rules-consistency"; fi

# 2. Schema-As-Code 契约校验
step "Schema-As-Code 契约校验（RULE-030~033）"
if $PY hooks/schema-validator.py --all --fail-on-violation; then
  ok "schema-validator"
else
  fail "schema-validator"
fi

# 3. Schema 门禁
step "Schema 门禁（RULE-032）"
if $PY hooks/scripts/schema-gate.py; then ok "schema-gate"; else fail "schema-gate"; fi

# 4. Agent 生成代码 Linter（RULE-028）
if [ "$SKIP_LINTER" -eq 1 ]; then
  step "Agent Linter（RULE-028）— 已跳过"
else
  step "Agent 生成代码 Linter（RULE-028）"
  if $PY hooks/scripts/agent_linter_checker.py --ci --project-root .; then
    ok "agent-linter"
  else
    fail "agent-linter"
  fi
fi

# 5. 规格驱动门禁（RULE-055/056：澄清清零、无漂移、FR 全被 tasks 覆盖）
if [ "$SKIP_SPEC" -eq 1 ]; then
  step "规格驱动门禁（RULE-055/056）— 已跳过"
else
  step "规格驱动门禁（RULE-055/056）"
  if node hooks/scripts/spec-clarity-gate.mjs --root .; then
    ok "spec-clarity-gate"
  else
    fail "spec-clarity-gate"
  fi
fi

printf '\n'
if [ "$FAILED" -eq 1 ]; then
  printf '\033[1;31m规则门禁未通过，请修复后重试。\033[0m\n'
  exit 1
fi
printf '\033[1;32m规则门禁全部通过。\033[0m\n'
exit 0