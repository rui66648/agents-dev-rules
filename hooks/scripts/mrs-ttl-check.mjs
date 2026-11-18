#!/usr/bin/env node
/**
 * mrs-ttl-check.mjs — MRS scratch 条目 TTL 到期检查（零依赖）
 * ============================================================
 * 用法：
 *   node mrs-ttl-check.mjs [--mrs <file>] [--json]
 *
 * 遍历 managed-root-set.json，对 kind=scratch 且有 ttl 的条目：
 *   - ttl < 今天 → 报 "到期未归档"（应走 archive-scratch.ps1）
 *   - ttl 距今天 ≤ 7 天 → 报 "即将到期" WARN
 *   - 缺 ttl 的 scratch → 报 "缺 TTL"（fail-closed，设计稿 §2.1 约束）
 *
 * 退出码：恒 0（观察期）；--strict 时到期/缺 TTL 退出 1。
 */
import { readFileSync, existsSync } from 'node:fs';
import { resolve, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_MRS = resolve(SCRIPT_DIR, '..', 'configs', 'managed-root-set.json');

const arg = (name) => {
  const i = process.argv.indexOf(name);
  return i > -1 ? process.argv[i + 1] : undefined;
};
const flag = (name) => process.argv.includes(name);

function localToday() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

const mrsFile = resolve(isAbsolute(arg('--mrs') || DEFAULT_MRS) ? (arg('--mrs') || DEFAULT_MRS) : DEFAULT_MRS);
if (!existsSync(mrsFile)) {
  console.error(`[mrs-ttl] MRS 不存在：${mrsFile}`);
  process.exit(2);
}
const mrs = JSON.parse(readFileSync(mrsFile, 'utf8'));
const today = localToday();
const findings = [];
const dayDiff = (a, b) => Math.round((new Date(a) - new Date(b)) / 86400000);

for (const r of mrs.roots || []) {
  if (r.kind !== 'scratch') continue;
  const entry = { path: r.path, kind: r.kind, ttl: r.ttl || null };
  if (!r.ttl) {
    findings.push({ ...entry, level: 'FAIL', msg: 'scratch 条目缺 TTL（fail-closed：必须显式写）' });
  } else if (!/^\d{4}-\d{2}-\d{2}$/.test(r.ttl)) {
    findings.push({ ...entry, level: 'FAIL', msg: `TTL 格式非法：${r.ttl}` });
  } else {
    const diff = dayDiff(r.ttl, today);
    if (diff < 0) findings.push({ ...entry, level: 'FAIL', msg: `TTL 已过期 ${-diff} 天（${r.ttl}）— 应归档` });
    else if (diff <= 7) findings.push({ ...entry, level: 'WARN', msg: `TTL 即将到期（剩 ${diff} 天，${r.ttl}）` });
  }
}

const fails = findings.filter((f) => f.level === 'FAIL');
if (flag('--json')) {
  console.log(JSON.stringify({ today, mrs: mrsFile, findings, fail: fails.length }, null, 2));
} else {
  console.log(`[mrs-ttl] 今天 ${today}，scratch 条目 ${findings.length} 条告警`);
  for (const f of findings) console.log(`  [${f.level}] ${f.path} — ${f.msg}`);
  if (!findings.length) console.log('[mrs-ttl] 无到期/缺 TTL 条目');
}
process.exit(flag('--strict') && fails.length ? 1 : 0);
