#!/usr/bin/env node
/**
 * RULE-054 读数控取器 · 启动器（本仓不留第二份取数实现）
 * 规范唯一实现：共享规则根 hooks/scripts/gen-project-dashboards.mjs
 * 用法：node tools/gen-dashboards.mjs [--slots 02,09] [--dry] [--offline]
 * 取数声明：docs/dashboards/sources.json（端点/目录名/责任人；缺省则不触网）
 * 边界：只替换每张图「读数」段的 AUTO 块；决策/图/变化 属人工判断，不覆盖。
 */
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const impl = [
  process.env.RULES_ROOT && join(process.env.RULES_ROOT, 'hooks', 'scripts', 'gen-project-dashboards.mjs'),
  join(resolve(here, '..', '..'), 'hooks', 'scripts', 'gen-project-dashboards.mjs'),
].filter(Boolean).find((p) => existsSync(p));

if (!impl) { console.error('[gen-dashboards] FAIL — 未找到共享规则根实现（设 RULES_ROOT 指向规则库根目录）'); process.exit(1); }
const r = spawnSync(process.execPath, [impl, '--root', resolve(here, '..'), ...process.argv.slice(2)], { stdio: 'inherit' });
process.exit(r.status ?? 1);
