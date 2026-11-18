#!/usr/bin/env node
/**
 * Creation-Gate 创建点门禁（零依赖，v0.1.0 观察期）
 * ============================================================
 * 用法：
 *   node creation-gate.mjs --target <path> [--mrs <file>] [--json]
 *   node creation-gate.mjs --selftest
 *
 * 在文件/目录创建前判定目标是否位于某个受管根的合法落点。
 * 返回 JSON: { allowed, reason, suggested_destination, owning_root?, bypass? }
 *   allowed: true  → 允许创建
 *   allowed: false → 观察期只 log 不阻断；硬拦截期直接拒绝
 *
 * 三步判定：
 *   1. target 是否位于某个受管根内（最强约束；不在任何受管根 → deny）
 *   2. os-scratch (scan:false) → bypass
 *   3. target 相对 owning root 的第一级是否在 allowlist（root-structure.json）登记
 *      + 文件名是否命中 L1 命名红线
 */

import { readFileSync, existsSync, mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { resolve, relative, isAbsolute, basename, dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_MRS = resolve(SCRIPT_DIR, '..', 'configs', 'managed-root-set.json');

const arg = (name) => {
  const i = process.argv.indexOf(name);
  return i > -1 ? process.argv[i + 1] : undefined;
};
const flag = (name) => process.argv.includes(name);

// L1 命名红线（与 root-cleanliness-check.mjs DENY_RE 保持同步）
const DENY_RE = [
  /^_/, /^\.tmp/i, /\.tmp\.json$/i, /^check[-_]/, /^analyze_/, /^batch_.+\.py$/, /^debug[-_]/,
  /\.log$/i, /\.db$/i, /\.(cer|pem|crt|key)$/i, /^kbp_/, /^[^/\\]*\.png$/i, /\.bak$/i, /^nul$/i,
];

function loadMRS(file) {
  const abs = isAbsolute(file) ? file : resolve(file);
  if (!existsSync(abs)) return { roots: [], missing: true, file: abs };
  try {
    const j = JSON.parse(readFileSync(abs, 'utf8'));
    return { roots: j.roots || [], missing: false, file: abs };
  } catch (e) {
    return { roots: [], missing: false, broken: e.message, file: abs };
  }
}

/**
 * 检查 relPath 第一级是否在 allowlist（root-structure.json）登记
 * @param {string} owningRoot  owning root 绝对路径
 * @param {string} allowlistFile  allowlist 相对/绝对路径
 * @param {string} relPath  target 相对 owning root 的路径
 * @returns {{ ok: boolean, reason?: string }}
 */
function checkAllowlist(owningRoot, allowlistFile, relPath) {
  const absAl = isAbsolute(allowlistFile) ? allowlistFile : resolve(owningRoot, allowlistFile);
  if (!existsSync(absAl)) return { ok: false, reason: `allowlist 不存在：${absAl}` };
  let j;
  try {
    j = JSON.parse(readFileSync(absAl, 'utf8'));
  } catch (e) {
    return { ok: false, reason: `allowlist 解析失败：${e.message}` };
  }
  const dirs = j.dirs || {};
  const firstSeg = relPath.split(/[/\\]/)[0];
  // 一级目录或根级文件
  if (dirs[firstSeg]) return { ok: true };
  return { ok: false, reason: `一级条目 '${firstSeg}' 未在 ${allowlistFile} 登记` };
}

/**
 * 核心判定
 * @param {string} targetPath  目标绝对路径
 * @param {string} [mrsFile]   MRS 文件路径
 * @returns {{ allowed: boolean, reason: string|null, suggested_destination: string|null, owning_root?: string, bypass?: boolean }}
 */
export function judge(targetPath, mrsFile) {
  const mrs = loadMRS(mrsFile || arg('--mrs') || DEFAULT_MRS);
  if (mrs.missing) return { allowed: false, reason: `MRS 文件不存在：${mrs.file}`, suggested_destination: null };
  if (mrs.broken)  return { allowed: false, reason: `MRS 解析失败：${mrs.broken}`,  suggested_destination: null };

  const abs = resolve(targetPath);

  // Step 1: 找 owning root（最长路径前缀匹配）
  let owning = null;
  let bestLen = -1;
  for (const r of mrs.roots) {
    const rp = resolve(r.path);
    const rel = relative(rp, abs);
    if (rel === '' || rel.startsWith('..') || isAbsolute(rel)) continue;
    if (rp.length > bestLen) {
      bestLen = rp.length;
      owning = { ...r, resolvedPath: rp, relPath: rel };
    }
  }

  if (!owning) {
    return {
      allowed: false,
      reason: `target 不在任何受管根内：${abs}`,
      suggested_destination: '见 MRS managed-root-set.json 或 RULE-053 §1 L3 落点表',
    };
  }

  // Step 2: os-scratch bypass
  if (owning.scan === false) {
    return { allowed: true, reason: 'os-scratch bypass (scan:false)', suggested_destination: null, bypass: true, owning_root: owning.resolvedPath };
  }

  // Step 3a: L1 命名红线（只对根级条目，非子目录内文件）
  const isRootLevel = !owning.relPath.includes('/') && !owning.relPath.includes('\\');
  if (isRootLevel) {
    const name = basename(abs);
    const denyHit = DENY_RE.find((r) => r.test(name));
    if (denyHit) {
      return {
        allowed: false,
        reason: `命中 L1 命名红线 (${denyHit.source})`,
        suggested_destination: '按 RULE-053 §1 L3 产物落点表',
        owning_root: owning.resolvedPath,
      };
    }
  }

  // Step 3b: allowlist 检查（scratch 无 allowlist 约束 → 视为合法）
  if (owning.kind === 'scratch') {
    return { allowed: true, reason: null, owning_root: owning.resolvedPath };
  }

  const allowlistFile = owning.allowlist || 'tools/root-structure.json';
  const alResult = checkAllowlist(owning.resolvedPath, allowlistFile, owning.relPath);
  if (!alResult.ok) {
    return {
      allowed: false,
      reason: alResult.reason,
      suggested_destination: '见 RULE-053 §1 L3 产物落点表',
      owning_root: owning.resolvedPath,
    };
  }

  return { allowed: true, reason: null, owning_root: owning.resolvedPath };
}

// ── --selftest ──────────────────────────────────────────────────────────────
function selftest() {
  const results = [];
  const sandbox = mkdtempSync(join(tmpdir(), 'creation-gate-test-'));
  try {
    const fakeWs    = join(sandbox, 'ws');
    const fakeRepo  = join(fakeWs, 'myrepo');
    const fakeScr   = join(sandbox, 'myscratch');
    const outside   = join(sandbox, 'unmanaged');
    const fakeOsTmp = join(sandbox, 'ostmp');

    mkdirSync(join(fakeRepo, 'tools'), { recursive: true });
    mkdirSync(join(fakeWs,   'tools'), { recursive: true });
    mkdirSync(join(fakeScr, 'sub'),    { recursive: true });
    mkdirSync(outside,                  { recursive: true });
    mkdirSync(fakeOsTmp,                { recursive: true });

    writeFileSync(join(fakeRepo, 'tools', 'root-structure.json'), JSON.stringify({
      dirs: {
        docs:    { class: 'engineering', reason: '文档' },
        tools:   { class: 'engineering', reason: '工具' },
        outputs: { class: 'artifact',    reason: '产物' },
      },
    }));
    writeFileSync(join(fakeWs, 'tools', 'root-structure.json'), JSON.stringify({
      dirs: {
        myrepo:  { class: 'external',  reason: '子仓' },
        outputs: { class: 'artifact',  reason: '产物' },
      },
    }));

    const mrsPath = join(sandbox, 'mrs.json');
    writeFileSync(mrsPath, JSON.stringify({
      roots: [
        { path: fakeWs,      kind: 'workspace-root', allowlist: 'tools/root-structure.json' },
        { path: fakeRepo,    kind: 'repo',           allowlist: 'tools/root-structure.json' },
        { path: fakeScr,     kind: 'scratch',        ttl: '2099-12-31' },
        { path: fakeOsTmp,   kind: 'os-scratch',     scan: false },
      ],
    }));

    const cases = [
      // T1: repo 内已登记 docs/ 写文件 → allowed
      { t: join(fakeRepo, 'docs', 'report.md'),
        want: true,  case: 'T1 repo 内已登记 docs/ 写文件' },
      // T2: repo 根写未登记文件 → not allowed
      { t: join(fakeRepo, 'random-report.md'),
        want: false, case: 'T2 repo 根未登记文件' },
      // T3: 受管根外 → not allowed
      { t: join(outside, 'foo.txt'),
        want: false, case: 'T3 受管根外路径' },
      // T4: os-scratch → allowed (bypass)
      { t: join(fakeOsTmp, 'whatever.txt'),
        want: true,  case: 'T4 os-scratch bypass' },
      // T5: scratch 内写 → allowed (无 allowlist 约束)
      { t: join(fakeScr, 'sub', 'data.json'),
        want: true,  case: 'T5 scratch 内写' },
      // T6: 根级 .tmp-* 命名红线 → not allowed
      { t: join(fakeRepo, '.tmp-foo'),
        want: false, case: 'T6 .tmp-* 命名红线' },
      // T7: workspace-root outputs/ → allowed
      { t: join(fakeWs, 'outputs', 'file.txt'),
        want: true,  case: 'T7 workspace-root outputs/' },
      // T8: workspace-root 未登记一级目录 → not allowed
      { t: join(fakeWs, 'unknown-dir', 'x.txt'),
        want: false, case: 'T8 workspace-root 未登记一级目录' },
    ];

    for (const c of cases) {
      const v = judge(c.t, mrsPath);
      const ok = v.allowed === c.want;
      results.push({ ok, case: c.case, detail: v.allowed ? `allowed (${v.bypass ? 'bypass' : v.owning_root})` : `denied: ${v.reason}` });
    }

    const failed = results.filter((r) => !r.ok);
    for (const r of results) console.log(`[creation-gate selftest] ${r.ok ? 'OK  ' : 'FAIL'} ${r.case} — ${r.detail}`);
    console.log(failed.length ? `[creation-gate selftest] FAIL — ${failed.length} 项` : '[creation-gate selftest] PASS — 正负双向自证通过');
    process.exit(failed.length ? 1 : 0);
  } finally {
    rmSync(sandbox, { recursive: true, force: true });
  }
}

if (flag('--selftest')) selftest();

const target = arg('--target');
if (!target) {
  console.error('[creation-gate] 必须传 --target <path>');
  process.exit(2);
}

const verdict = judge(target, arg('--mrs'));
if (flag('--json')) {
  console.log(JSON.stringify(verdict, null, 2));
} else {
  if (verdict.allowed) {
    console.log(`[creation-gate] ALLOW ${target}${verdict.bypass ? ' (bypass)' : ''}`);
  } else {
    console.log(`[creation-gate] DENY  ${target}`);
    console.log(`  reason:     ${verdict.reason}`);
    if (verdict.suggested_destination) console.log(`  suggested:  ${verdict.suggested_destination}`);
  }
}
process.exit(verdict.allowed ? 0 : 1);
