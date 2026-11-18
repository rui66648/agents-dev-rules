#!/usr/bin/env node
/**
 * branch-hygiene-check.mjs — 分支/检出卫生观察期门禁（WARN only，退出码恒 0）
 * v1.0.0（2026-11-14，规则库 v4.20.0 配套；起因 = 2026-11-14 违规根因分析六条修法之①②⑥）
 *
 * 判据（全部报告性，不拦截；诚实边界：只判结构信号，不判理解与意图）：
 *   C1 主检出占用 —— 主检出（git-dir == git-common-dir）停在非 main/master 分支
 *                    → WARN 归还提醒（branch-strategy §0.1 主检出权条款）
 *   C2 豁免计量   —— 近 7 天含「--no-verify 原因」的提交数 ≥ 阈值（默认 15/周）
 *                    → WARN 安全阀常态化（root-directory-hygiene §3.1 豁免计量）
 *   C3 Agent 归因 —— HEAD 提交 body 缺 `Agent:` trailer → WARN（git-conventions v1.2.0）
 *   C4 工作面数   —— git worktree list 面数 > 阈值（默认 8，与 thresholds.md「并发工作面数」同源）
 *
 * 用法：
 *   node branch-hygiene-check.mjs --root <repo> [--max-bypass 15] [--max-worktrees 8] [--selftest]
 *
 * 自带 --selftest 正负自证（防止门禁给出假绿/假红）；未挂 rules/gate.sh 硬拦截，
 * 不写 gate-runs 记录 —— 登记 gate-inventory.yaml（not-integrated，观察期）。
 */
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

const args = process.argv.slice(2);
const argv = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined; };
const num = (v, d) => { const n = Number(v); return Number.isFinite(n) && n >= 0 ? n : d; };

const MAX_BYPASS = num(argv('--max-bypass'), 15);
const MAX_WORKTREES = num(argv('--max-worktrees'), 8);

function git(root, gitArgs) {
  try { return execFileSync('git', ['-C', root, ...gitArgs], { encoding: 'utf8' }); } catch { return ''; }
}

/** 纯判定函数（供 --selftest 与 main 共用）：输入事实，输出 findings */
export function evaluate(f) {
  const out = [];
  if (f.isMainCheckout && f.branch && !['main', 'master'].includes(f.branch)) {
    out.push({ id: 'C1', level: 'WARN', msg: `主检出停留在 '${f.branch}'（branch-strategy §0.1 主检出权）：任务收尾请归还 main，或把工作移交专用 worktree` });
  }
  if (f.bypassCount >= f.maxBypass) {
    out.push({ id: 'C2', level: 'WARN', msg: `近 7 天 --no-verify 豁免 ${f.bypassCount} 次 ≥ 阈值 ${f.maxBypass}（root-directory-hygiene §3.1）：安全阀被常态化，当日修根因或登记整改项` });
  }
  if (f.hasHead && !f.hasTrailer) {
    out.push({ id: 'C3', level: 'WARN', msg: 'HEAD 提交缺 `Agent: <工具>-<角色>` trailer（git-conventions v1.2.0 归因条款）' });
  }
  if (f.worktreeCount > f.maxWorktrees) {
    out.push({ id: 'C4', level: 'WARN', msg: `并发工作面 ${f.worktreeCount} > 阈值 ${f.maxWorktrees}（thresholds.md「并发工作面数」同源）：消化存量 worktree` });
  }
  return out;
}

function selftest() {
  const cases = [
    ['C1 正例：主检出+feature 分支 → WARN', { isMainCheckout: true, branch: 'fix/x-1114', bypassCount: 0, maxBypass: 15, hasHead: false, hasTrailer: false, worktreeCount: 1, maxWorktrees: 8 }, (r) => r.some((x) => x.id === 'C1')],
    ['C1 负例：worktree 里开发 → 无 C1', { isMainCheckout: false, branch: 'fix/x-1114', bypassCount: 0, maxBypass: 15, hasHead: false, hasTrailer: false, worktreeCount: 1, maxWorktrees: 8 }, (r) => !r.some((x) => x.id === 'C1')],
    ['C1 负例：主检出在 main → 无 C1', { isMainCheckout: true, branch: 'main', bypassCount: 0, maxBypass: 15, hasHead: false, hasTrailer: false, worktreeCount: 1, maxWorktrees: 8 }, (r) => !r.some((x) => x.id === 'C1')],
    ['C2 正例：豁免达阈值 → WARN', { isMainCheckout: false, branch: 'main', bypassCount: 15, maxBypass: 15, hasHead: false, hasTrailer: false, worktreeCount: 1, maxWorktrees: 8 }, (r) => r.some((x) => x.id === 'C2')],
    ['C3 正例：缺 trailer → WARN', { isMainCheckout: false, branch: 'main', bypassCount: 0, maxBypass: 15, hasHead: true, hasTrailer: false, worktreeCount: 1, maxWorktrees: 8 }, (r) => r.some((x) => x.id === 'C3')],
    ['C3 负例：有 trailer → 无 C3', { isMainCheckout: false, branch: 'main', bypassCount: 0, maxBypass: 15, hasHead: true, hasTrailer: true, worktreeCount: 1, maxWorktrees: 8 }, (r) => !r.some((x) => x.id === 'C3')],
    ['C4 正例：工作面超阈值 → WARN', { isMainCheckout: false, branch: 'main', bypassCount: 0, maxBypass: 15, hasHead: false, hasTrailer: false, worktreeCount: 9, maxWorktrees: 8 }, (r) => r.some((x) => x.id === 'C4')],
    ['全净 → 0 findings', { isMainCheckout: true, branch: 'main', bypassCount: 0, maxBypass: 15, hasHead: true, hasTrailer: true, worktreeCount: 3, maxWorktrees: 8 }, (r) => r.length === 0],
  ];
  let fail = 0;
  for (const [name, input, assertFn] of cases) {
    const ok = assertFn(evaluate(input));
    console.log(`  [${ok ? 'OK' : 'FAIL'}] ${name}`);
    if (!ok) fail++;
  }
  console.log(`[selftest] ${cases.length - fail}/${cases.length} PASS`);
  process.exit(fail === 0 ? 0 : 1);
}

if (args.includes('--selftest')) { selftest(); }

const root = resolve(argv('--root') || process.cwd());
const gitDir = git(root, ['rev-parse', '--path-format=absolute', '--git-dir']).trim();
const commonDir = git(root, ['rev-parse', '--path-format=absolute', '--git-common-dir']).trim();
const branch = git(root, ['branch', '--show-current']).trim();
const isMainCheckout = gitDir !== '' && commonDir !== '' && gitDir === commonDir;

const bypassLog = git(root, ['log', '--since=7 days ago', '-i', '--grep=no-verify 原因', '--format=%h']);
const bypassCount = bypassLog ? bypassLog.split('\n').filter((x) => x.trim()).length : 0;

const headBody = git(root, ['log', '-1', '--format=%B']);
const hasHead = headBody.trim() !== '';
const hasTrailer = /^\s*Agent:\s*\S+/m.test(headBody);

const wtList = git(root, ['worktree', 'list', '--porcelain']);
const worktreeCount = wtList ? wtList.split('\n').filter((l) => l.startsWith('worktree ')).length : 0;

const findings = evaluate({ isMainCheckout, branch, bypassCount, maxBypass: MAX_BYPASS, hasHead, hasTrailer, worktreeCount, maxWorktrees: MAX_WORKTREES });

console.log(`[branch-hygiene] root=${root}`);
console.log(`  main-checkout=${isMainCheckout} branch=${branch || '(detached)'} bypass7d=${bypassCount} trailer=${hasTrailer} worktrees=${worktreeCount}`);
if (findings.length === 0) { console.log('  [OK  ] 无结构卫生信号（不代表行为合规——本门禁只判信号，不判理解）'); }
for (const f of findings) console.log(`  [${f.level}] ${f.id} ${f.msg}`);
console.log('[branch-hygiene] 观察期 WARN-only：退出码恒 0，不拦截（诚实边界：判信号不判行为质量）。');
process.exit(0);
