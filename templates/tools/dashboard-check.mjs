#!/usr/bin/env node
/**
 * RULE-054 项目图形资产门禁 · 启动器（本仓不留第二份实现）
 * ============================================================
 * 规范唯一实现：共享规则根 `hooks/scripts/dashboard-registry-check.mjs`
 *   —— 十槽固定（00 驾驶舱 + 01–09 核心图），一图一决策
 *   —— 只更新不重生成：同槽位第二份文件即 FAIL
 *   —— 红黄绿必须由 docs/dashboards/thresholds.md 的指标名推导
 *   —— 自带 `--selftest` 正负双向自证，防止门禁给出假绿
 *
 * 位置解析：环境变量 RULES_ROOT > 规则库相对路径。
 * 用法：node tools/dashboard-check.mjs [--json|--check|--emit-registry|--init|--selftest]
 *   首次采纳：node tools/dashboard-check.mjs --init   （任何槽位文件已存在即整体拒绝）
 */
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const candidates = [
  process.env.RULES_ROOT && join(process.env.RULES_ROOT, 'hooks', 'scripts', 'dashboard-registry-check.mjs'),
  join(resolve(here, '..', '..'), 'hooks', 'scripts', 'dashboard-registry-check.mjs'),
].filter(Boolean);
const impl = candidates.find((p) => existsSync(p));

if (!impl) {
  console.error('[dashboards] FAIL — 未找到共享规则根门禁实现（请设 RULES_ROOT 指向规则库根目录）');
  process.exit(1);
}

const r = spawnSync(process.execPath, [impl, '--root', resolve(here, '..'), ...process.argv.slice(2)], { stdio: 'inherit' });
process.exit(r.status ?? 1);
