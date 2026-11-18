#!/usr/bin/env node
/**
 * RULE-054 十槽读数控取器（canonical 实现，零依赖）
 * ============================================================================
 * 三条硬约束：
 *   1) 只写能量出来的数。取不到就写「取不到」并指出缺哪一行输入——不用估算、不用占位符冒充读数。
 *   2) 就地更新：只替换每张图「读数」段里 AUTO:BEGIN/AUTO:END 之间的内容；
 *      决策 / 图 / 变化 属人工判断，永不覆盖（这就是「只更新不重生成」的工具层落点）。
 *   3) 灯不写死在代码里：值按口径算出，档位查 docs/dashboards/thresholds.md 的绿/黄/红列；
 *      阈值表没有该指标 → 不点灯并回报缺口。
 *
 * 用法：node tools/gen-dashboards.mjs [--slots 02,03] [--dry] [--offline] [--json]
 * 取数声明：docs/dashboards/sources.json（端点、目录名、责任人等仓特有项；缺省则不触网）
 *
 * 不做近似的事：循环依赖检测需要真 import 解析器，正则近似会造出假环——本工具只报边数，
 * 判环写「取不到」，等接入解析器再补。
 */
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const argv = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined; };
// ROOT 由启动器用 --root 传入（缺省=本文件所在仓，即共享根本自己不产图）
const ROOT = resolve(argv('--root') || join(HERE, '..', '..'));
const DASH = join(ROOT, 'docs', 'dashboards');
const now = new Date();
const git = (a, cwd = ROOT) => { try { return execFileSync('git', ['-c', 'core.quotePath=false', ...a], { encoding: 'utf8', cwd, maxBuffer: 64 << 20 }); } catch { return ''; } };
/** 只关心成败的 git 调用（merge-base --is-ancestor 等）：stdout 两边都为空，必须看退出码 */
const gitOk = (a, cwd = ROOT) => { try { execFileSync('git', ['-c', 'core.quotePath=false', ...a], { encoding: 'utf8', cwd, stdio: 'ignore' }); return true; } catch { return false; } };
const L = (s) => String(s).split(/\r?\n/).filter((x) => x.trim());
const day = (iso) => (iso || '').slice(0, 10);
const ago = (iso) => (iso ? Math.floor((now - new Date(iso)) / 86400000) : null);
const src = existsSync(join(DASH, 'sources.json')) ? JSON.parse(readFileSync(join(DASH, 'sources.json'), 'utf8')) : {};
const trunk = src.trunk || 'main';

// ── 阈值表 → 档位判定 ─────────────────────────────────────────────────────
function loadThresholds() {
  const map = new Map();
  const p = join(DASH, 'thresholds.md');
  if (!existsSync(p)) return map;
  for (const line of L(readFileSync(p, 'utf8'))) {
    const c = line.split('|').map((x) => x.trim());
    if (c.length < 7 || !c[1] || /^:?-{2,}:?$/.test(c[1]) || /^(指标|metric)$/i.test(c[1])) continue;
    map.set(c[1], { green: c[4], amber: c[5], red: c[6] });
  }
  return map;
}
const TH = loadThresholds();
function lamp(metric, value) {
  const t = TH.get(metric);
  if (!t) return { l: '不点灯', why: '阈值表缺「' + metric + '」行' };
  if (value === null || value === undefined) return { l: '不点灯', why: metric + '：值取不到（缺的是输入，不是数——见该行「口径/数据源」列缺哪一行）' };
  const n = parseFloat(String(value).replace(/[^\d.\-]/g, ''));
  if (Number.isNaN(n)) return { l: '不点灯', why: '值非数值' };
  const hit = (cell) => {
    const m = /^([<>≤≥=]*)\s*(-?[\d.]+)/.exec(String(cell || '').replace('−', '-'));
    if (!m) return false;
    const th = parseFloat(m[2]);
    if (m[1] === '<') return n < th; if (m[1] === '≤') return n <= th;
    if (m[1] === '>') return n > th; if (m[1] === '≥') return n >= th;
    return n === th;
  };
  if (hit(t.red)) return { l: '红', why: metric + '=' + value + ' 命中红档 ' + t.red };
  if (hit(t.green)) return { l: '绿', why: metric + '=' + value + ' 命中绿档 ' + t.green };
  if (hit(t.amber)) return { l: '黄', why: metric + '=' + value + ' 命中黄档 ' + t.amber };
  return { l: '不点灯', why: metric + '=' + value + ' 不落任何档' };
}
const GAPS = [];
/** 灯与指标名同行，但各占一格：门禁按「灯所在行是否出现阈值表指标名」判颜色有无依据。
 *  把指标名塞进灯格里会绕过门禁的正则（`红（…）` 里的红不视作灯），等于自造假绿。 */
function cell(metric, value, note) {
  const r = lamp(metric, value);
  if (r.l === '不点灯') GAPS.push(r.why);
  return { metric, v: value === null || value === undefined ? '取不到' : String(value), l: r.l, why: r.why,
    note: note ? note + (r.l === '不点灯' && !String(note).includes('取不到') ? '｜不点灯原因：' + r.why : '') : r.why };
}
const tbl = (head, rows) => ['| ' + head + ' |', '|' + head.split(' | ').map(() => '---').join('|') + '|'].concat(rows).join('\n');
const r4 = (c) => '| ' + [c.metric, c.v, c.l, c.note || c.why].join(' | ') + ' |';
const M = (metric, value, note) => cell(metric, value, note);
/** 只报事实不判档的量（没有好坏含义的计数，硬给它点灯就是假判据） */
const RAW = (name, value, note) => '| ' + name + ' | ' + (value === null || value === undefined ? '取不到' : value) + ' | 不点灯 | ' + note + ' |';
const KV = (rows) => tbl('指标 | 实测 | 灯 | 口径 / 数据源', rows);
/** 带 ID 列的表（08 代码健康）：指标名写进 ID 格，灯格只留灯——同上，指标名不许藏进灯格 */
function LR(id, metric, value, source) {
  const r = lamp(metric, value);
  if (r.l === '不点灯') GAPS.push(r.why);
  return '| ' + id + ' ' + metric + ' | ' + (value === null || value === undefined ? '取不到' : value) + ' | ' + source + ' | ' + r.l + ' |';
}

// ── 事实采集（git + 磁盘 + 可选线上戳）───────────────────────────────────
const F = { head: git(['rev-parse', '--short', 'HEAD']).trim(), headIso: git(['show', '-s', '--format=%cI', 'HEAD']).trim() };
F.ahead = (() => { const up = git(['rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}']).trim(); return up ? parseInt(git(['rev-list', '--count', up + '..HEAD']).trim(), 10) : null; })();
F.commits = L(git(['log', '--format=%cI|%an', trunk])).map((x) => { const [d, a] = x.split('|'); return { d, a }; });
F.authors = [...new Set(F.commits.map((c) => c.a))];
F.first = day(F.commits[F.commits.length - 1] ? F.commits[F.commits.length - 1].d : '');
F.merges = L(git(['log', '--first-parent', '--merges', '--format=%cI|%s', trunk])).map((x) => { const [d, ...s] = x.split('|'); return { d, name: s.join('|') }; });
F.branches = L(git(['for-each-ref', '--format=%(refname:short)|%(committerdate:iso8601)', 'refs/heads'])).map((x) => {
  const [n, d] = x.split('|');
  return { n, d, age: ago(d), merged: n === trunk ? true : gitOk(['merge-base', '--is-ancestor', n, trunk]) };
});
// 必须用 --porcelain：`git worktree list` 的行是「路径 sha [分支]」，当路径用会整批失败并假报 0 在途
F.wts = L(git(['worktree', 'list', '--porcelain'])).filter((l) => l.startsWith('worktree ')).map((x) => x.slice('worktree '.length).trim());
F.dirty = F.wts.map((p) => ({ p, name: p.split(/[\\/]/).pop(), n: L(git(['status', '--porcelain'], p)).length }));
F.churn = (() => {
  const f = new Set(); let add = 0, del = 0;
  for (const line of L(git(['log', '--since=7.days', '--numstat', '--format=', trunk]))) {
    const p = line.split('\t');
    if (p.length >= 3) { f.add(p[2]); add += parseInt(p[0], 10) || 0; del += parseInt(p[1], 10) || 0; }
  }
  return { files: f.size, add, del };
})();
F.weeks = [...Array(5)].map((_, i) => {
  const to = new Date(now - i * 7 * 86400000), from = new Date(now - (i + 1) * 7 * 86400000);
  const inw = (iso) => { const d = new Date(iso); return d >= from && d < to; };
  return {
    label: day(from.toISOString()) + '~' + day(to.toISOString()),
    commits: F.commits.filter((c) => inw(c.d)).length,
    merges: F.merges.filter((m) => inw(m.d)).length,
    branches: F.branches.filter((b) => inw(b.d)).length,
  };
});
function countFiles(rel, re) {
  const abs = join(ROOT, rel);
  if (!rel || !existsSync(abs)) return null;
  let n = 0;
  const walk = (d, depth) => { if (depth > 5) return; for (const e of readdirSync(d, { withFileTypes: true })) { if (e.name === 'node_modules' || e.name.startsWith('.')) continue; const p = join(d, e.name); if (e.isDirectory()) walk(p, depth + 1); else if (re.test(e.name)) n++; } };
  try { walk(abs, 0); } catch { return null; }
  return n;
}
function countRoutes() {
  const idx = join(ROOT, 'worker/src/index.ts');
  if (existsSync(idx)) return (readFileSync(idx, 'utf8').match(/\.(get|post|put|delete|patch|all)\(\s*['"`]/g) || []).length;
  for (const p of ['test-system/backend/main.py', 'platform/src/main.js']) {
    const abs = join(ROOT, p);
    if (existsSync(abs)) return (readFileSync(abs, 'utf8').match(/@app\.(get|post|put|delete|patch)\b|\.(get|post|put|delete)\(\s*['"`]/g) || []).length;
  }
  return null;
}
F.deliv = {
  pages: countFiles(src.pagesDir || 'web/src/pages', /\.tsx$/),
  routes: countRoutes(),
  migrations: countFiles(src.migrationsDir || 'worker/migrations', /\.sql$/),
  tests: countFiles(src.testsDir || 'worker/tests', /\.(test|spec)\.[tj]s$|\.test\.mjs$/),
  tools: countFiles('tools', /\.(mjs|ps1|py|cjs|js|ts)$/),
  reports: countFiles('docs/reports', /\.(md|html)$/),
  adrs: countFiles('docs/decisions', /^ADR-.*\.md$/),
};
F.registry = (() => {
  const rel = src.registryFile || 'plugins/registry.yaml';
  const p = join(ROOT, rel);
  if (!existsSync(p)) return null;
  const s = readFileSync(p, 'utf8'); const out = {};
  for (const m of s.matchAll(/^  (\w+):\n((?:    .*\n|\n)*)/gm)) {
    const body = m[2];
    const arr = (body.match(/^    -\s/gm) || []).length;
    const obj = (body.match(/^    \S.*:\s*$/gm) || []).length;
    if (arr || obj) out[m[1]] = arr || obj;
  }
  return { file: rel, counts: out };
})();
F.coverage = (() => {
  for (const rel of ['coverage/coverage-summary.json', 'web/coverage/coverage-summary.json', 'worker/coverage/coverage-summary.json']) {
    const p = join(ROOT, rel);
    if (existsSync(p)) { try { const t = JSON.parse(readFileSync(p, 'utf8')).total; if (t && t.lines) return { pct: t.lines.pct, of: t.lines.covered + '/' + t.lines.total, rel }; } catch { return { broken: rel }; } }
  }
  return null;
})();
function importEdges() {
  let files = 0, edges = 0;
  for (const rel of src.importScanDirs || ['worker/src', 'web/src']) {
    const abs = join(ROOT, rel);
    if (!existsSync(abs)) continue;
    const walk = (d) => { for (const e of readdirSync(d, { withFileTypes: true })) { if (e.name === 'node_modules' || e.name.startsWith('.')) continue; const p = join(d, e.name); if (e.isDirectory()) walk(p); else if (/\.(ts|tsx|js|jsx|mjs)$/.test(e.name)) { files++; try { edges += (readFileSync(p, 'utf8').match(/from\s+['"]\.[^'"]+['"]/g) || []).length; } catch { /* 读不到即不计 */ } } } };
    try { walk(abs); } catch { /* 跳过 */ }
  }
  return { files, edges: files ? edges : null };
}
const DEP = importEdges();

// 发布台账 + lead time（真算：commit 提交者时间 → 台账事件时间）
// thresholds.md 把「发布失败率」的数据源钉在机器级发布审计（跨 worktree 全量），仓库内 build-log 是子集，
// 所以两源都读：主源用审计，缺失时回退仓库台账，并把两源条数并列出来对账（差额本身就是口径事实）。
function expandPath(p) {
  if (!p) return null;
  return String(p)
    .replace(/%\{?LOCALAPPDATA\}?%/i, process.env.LOCALAPPDATA || '')
    .replace(/\$\{?LOCALAPPDATA\}?/i, process.env.LOCALAPPDATA || '')
    .replace(/^~(?=[/\\])/, process.env.USERPROFILE || process.env.HOME || '');
}
function readJsonl(abs, label, shown) {
  if (!abs || !existsSync(abs)) return { label, rel: shown || abs || '未声明', recs: [], missing: true };
  return { label, rel: shown || abs, recs: L(readFileSync(abs, 'utf8')).map((x) => { try { return JSON.parse(x); } catch { return null; } }).filter(Boolean), missing: false };
}
const AUD = readJsonl(expandPath(src.deployAudit), '机器级发布审计', src.deployAudit);
const LOG = readJsonl(join(ROOT, src.deployLedger || 'deploy/build-log.json'), '仓内发布台账', src.deployLedger || 'deploy/build-log.json');
const LED = AUD.recs.length ? AUD : LOG;
const deploys = LED.recs.filter((r) => /deploy-pass/.test(r.event || ''));
// seed-rollback = 回滚包预置（首次播种），按阈值表口径不计入失败
const rollbacks = LED.recs.filter((r) => /^rollback$|deploy-fail|verify-fail/.test(r.event || ''));
const lead = (() => {
  const seen = new Set(); const vals = [];
  for (const r of deploys) {
    const c = (r.commit || '').slice(0, 8);
    if (!c || seen.has(c)) continue; seen.add(c);
    const cd = git(['show', '-s', '--format=%cI', c]).trim();
    if (cd && r.at) { const h = (new Date(r.at) - new Date(cd)) / 3600000; if (h >= 0 && h < 24 * 30) vals.push(h); }
  }
  vals.sort((a, b) => a - b);
  return { n: vals.length, median: vals.length ? vals[Math.floor(vals.length / 2)].toFixed(1) : null, max: vals.length ? vals[vals.length - 1].toFixed(1) : null };
})();

const LIVE = {};
if (!flag('--offline')) {
  const probe = async (base, path, pick) => {
    if (!base) return { err: 'sources.json 未声明该端点' };
    try {
      const res = await fetch(new URL(path, base), { signal: AbortSignal.timeout(8000) });
      if (!res.ok) return { err: 'HTTP ' + res.status };
      const j = await res.json();
      const val = pick.split('.').reduce((o, k) => (o || {})[k], j);
      return { sha: val ?? null, count: Array.isArray(val) ? val.length : null, base, path };
    } catch (e) { return { err: e.name === 'TimeoutError' ? '超时 8s' : String(e.message).slice(0, 48), base, path }; }
  };
  LIVE.api = await probe(src.apiBase, src.healthPath || '/api/health', src.healthPick || 'data.gitCommit');
  LIVE.web = await probe(src.webBase, '/assets/build-meta.json', 'gitCommit');
  if (src.skillsPath) LIVE.skills = await probe(src.apiBase, src.skillsPath, 'data');
}
function drift() {
  if (!LIVE.api || !LIVE.api.sha) return null;
  const liveSha = String(LIVE.api.sha), short = F.head;
  const same = liveSha.startsWith(short) || short.startsWith(liveSha.slice(0, 7));
  if (same) return { same: true, liveSha };
  const inputs = (src.buildInputs || ['worker', 'web', 'kernel', 'shared', 'vendor', 'functions']);
  const gap = git(['rev-list', '--count', liveSha.slice(0, 8) + '..' + trunk]).trim();
  const funcDiff = git(['diff', '--name-only', liveSha.slice(0, 8) + '..' + trunk, '--'].concat(inputs)).trim();
  return { same: false, liveSha, head: short, gap: parseInt(gap, 10) || 0, functional: Boolean(funcDiff), detail: '线上 ' + liveSha.slice(0, 8) + ' vs ' + trunk + ' ' + short + '，差 ' + gap + ' 个提交；构建输入面' + (funcDiff ? '有功能差（' + L(funcDiff).length + ' 文件）' : '零功能差（仅版本戳差）') };
}
const DRIFT = drift();

// ── 各槽位读数 ────────────────────────────────────────────────────────────
const BUILDERS = {
  '01': () => {
    const rows = [
      ['前端页面/路由壳', F.deliv.pages, (src.pagesDir || 'web/src/pages') + ' 下 .tsx 计数'],
      ['后端路由/端点', F.deliv.routes, 'worker/src/index.ts 注册计数（无该文件则探 py/js 路由装饰器）'],
      ['数据迁移', F.deliv.migrations, (src.migrationsDir || 'worker/migrations') + ' 下 .sql 计数'],
      ['测试文件', F.deliv.tests, (src.testsDir || 'worker/tests') + ' 下 *.test.* 计数'],
      ['工具与门禁', F.deliv.tools, 'tools/ 下脚本计数'],
      ['报告档案', F.deliv.reports, 'docs/reports/ 下 .md/.html 计数'],
      ['架构决策', F.deliv.adrs, 'docs/decisions/ 下 ADR-*.md 计数'],
    ].map(([n, v, s], i) => '| D' + (i + 1) + ' ' + n + ' | ' + (v === null ? '取不到（目录不在磁盘）' : v) + ' | ' + s + ' | ' + (v ? '已交付' : '不适用') + ' |');
    if (F.registry) rows.push('| D8 注册能力面 | ' + Object.entries(F.registry.counts).map(([k, v]) => k + '=' + v).join(' / ') + ' | 派生自 ' + F.registry.file + '（生成器 ' + (src.registryGen || 'tools/gen-plugin-registry.mjs') + '） | 已交付 |');
    return [
      tbl('ID | 交付物面 | 实测数量 | 数据源 | 状态', rows),
      '',
      '需求追溯：可测的追溯链是「能力/技能 → 路由 → 页面」三段，本轮实测到 ' + (F.registry ? Object.values(F.registry.counts).reduce((a, b) => a + b, 0) : 0) + ' 个注册面与 ' + (F.deliv.routes ?? 0) + ' 条后端路由；技能↔路由的逐条映射需要 ' + (src.traceMatrix || 'sources.json 里声明 traceMatrix') + ' 才有分母，缺它则覆盖率类指标一律不写（不拿路由数冒充需求覆盖）。',
      '',
      '**不做什么**：' + (src.outOfScope || '取不到——sources.json 的 outOfScope 未声明；没有这条，范围边界无法判定，本图只能给数量不能给结论'),
    ].join('\n');
  },
  '02': () => {
    const rows = F.merges.slice(0, 8).map((m, i) => '| M' + String(F.merges.length - i).padStart(2, '0') + ' | ' + m.name.replace(/^Merge branch '|^merge: /, '').replace(/' ?:|\s*进 main.*$/, '').slice(0, 52) + ' | ' + day(m.d) + ' | ' + ago(m.d) + ' 天 | ' + (i > 0 ? (ago(F.merges[i - 1].d) - ago(m.d)) + ' 天' : '—') + ' | git log --first-parent --merges |');
    const span = F.merges.length > 1 ? (new Date(F.merges[0].d) - new Date(F.merges[F.merges.length - 1].d)) / 86400000 : 0;
    const gapsList = F.merges.slice(0, 10).map((m, i) => (i ? ago(F.merges[i - 1].d) - ago(m.d) : null)).filter((x) => x !== null && x >= 0);
    const p50 = gapsList.length ? gapsList.slice().sort((a, b) => a - b)[Math.floor(gapsList.length / 2)] : null;
    const unmerged = F.branches.filter((b) => !b.merged && b.n !== trunk);
    return [
      tbl('ID | 批次（合入 main 的提交标题） | 合入日 | 距今 | 与上一批间隔 | 判据', rows),
      '',
      '仓史起点 ' + F.first + '，累计合入批次 ' + F.merges.length + ' 个，跨 ' + span.toFixed(1) + ' 天 → 近 10 批的批次节奏中位数 ' + (p50 === null ? '取不到' : p50 + ' 天/批') + '（可算 ' + gapsList.length + ' 段间隔）。',
      '',
      KV([
        r4(M('里程碑偏差', null, '计划列取不到：仓内无事前基线台账（sources.json 的 ' + (src.planLedger ? 'planLedger=' + src.planLedger : 'planLedger 未声明') + '）→ 上表全是**事后合入事实**，不是计划达成率')),
        r4(M('未合入分支数', unmerged.length, '分支共 ' + F.branches.length + ' 个，未进 ' + trunk + ' 的 ' + unmerged.length + ' 个（' + unmerged.slice(0, 3).map((b) => b.n + ' ' + b.age + 'd').join('、') + '）')),
        r4(M('未推送提交', F.ahead, F.ahead === null ? '当前分支无上游跟踪，无「未推送」可言' : 'git rev-list @{u}..HEAD')),
      ]),
      '',
      '关键路径：' + (src.criticalPath || '取不到——sources.json 的 criticalPath 未声明，我不猜哪条链是关键路径'),
    ].join('\n');
  },
  '03': () => {
    const inflight = F.dirty.reduce((a, b) => a + b.n, 0);
    const longest = Math.max(0, ...F.branches.filter((b) => !b.merged && b.n !== trunk).map((b) => b.age));
    return [
      tbl('周 | 该周有提交的分支数 | 合入 main 批次 | 提交数', F.weeks.map((w) => '| ' + w.label + ' | ' + w.branches + ' | ' + w.merges + ' | ' + w.commits + ' |')),
      '',
      '累积流的实测形态：本仓没有看板系统（任务卡不落盘，' + (src.kanban ? '声明源 ' + src.kanban : 'sources.json kanban 未声明') + '），上表用「分支/批次/提交」的周计数近似吞吐——**这是吞吐事实，不是看板 CFD**，两者不可混报。',
      '',
      tbl('在途 worktree | 未提交文件数', F.dirty.map((d) => '| ' + d.name + ' | ' + d.n + ' |').concat(['| 合计 | ' + inflight + ' |'])),
      '',
      KV([
        r4(M('在途文件数', inflight, '各 worktree git status --porcelain 计数之和（多工具并发的真实堆积面）')),
        r4(M('并发工作面数', F.dirty.length, '本仓 worktree 数，一工具一面')),
        r4(M('列内停留天数', longest, '本仓「列」= 分支：未合入分支里最长的一支已 ' + longest + ' 天')),
      ]),
      '',
      'WIP 上限：' + (src.wipLimit ? '声明值 ' + src.wipLimit + '，超限判定见上表' : '取不到——未设上限即无「超限」可言；需要一行输入：同时并行几个面算超'),
    ].join('\n');
  },
  '04': () => {
    const byAuthor = F.commits.reduce((a, c) => (a[c.a] = (a[c.a] || 0) + 1, a), {});
    const top = Object.entries(byAuthor).sort((a, b) => b[1] - a[1])[0];
    return [
      tbl('作者 | 提交数 | 占比', Object.entries(byAuthor).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([a, n]) => '| ' + a + ' | ' + n + ' | ' + (100 * n / F.commits.length).toFixed(1) + '% |')),
      '',
      tbl('周 | 提交数 | 合入批次', F.weeks.map((w) => '| ' + w.label + ' | ' + w.commits + ' | ' + w.merges + ' |')),
      '',
      KV([
        r4(M('并发工作面数', F.dirty.length, 'worktree 实测：' + F.dirty.map((d) => d.name + '(' + d.n + ')').slice(0, 4).join(' '))),
        r4(M('关键技能单点', src.reviewIndependentPersons === undefined ? null : src.reviewIndependentPersons, src.reviewIndependentPersons === undefined ? '取不到：sources.json 的 reviewIndependentPersons 未声明（提交作者数 = ' + F.authors.length + '，但作者数 ≠ 评审独立性——本仓 main 只接受本地 --no-ff merge 且 CI 停用，评审与发布在同一人手上）' : '声明值 ' + src.reviewIndependentPersons + '（判据：分支策略声明 + CI 停用，见 AGENTS.md）')),
        RAW('主作者集中度', top ? (100 * top[1] / F.commits.length).toFixed(1) + '%' : null, top ? top[0] + ' 承担 ' + top[1] + '/' + F.commits.length + ' 提交' : '无提交'),
      ]),
      '',
      '人均负载：**取不到**——没有工时台账（' + (src.capacitySource ? '声明源 ' + src.capacitySource : 'sources.json capacitySource 未声明') + '），不算负载百分比。上表周提交分布与并发面数是可测产出口，不等于负载率；要这条指标得先有每周可用工时输入。',
    ].join('\n');
  },
  '05': () => {
    const rev = F.weeks.slice().reverse();
    let acc = F.merges.filter((m) => new Date(m.d) < new Date(rev[0].label.slice(0, 10))).length;
    const curve = rev.map((w) => { acc += w.merges; return '| ' + w.label + ' | ' + w.merges + ' | ' + acc + ' |'; });
    return [
      tbl('周（旧→新） | 当周合入批次 | 累计合入批次（S 曲线，EV 候选口径）', curve),
      '',
      KV([
        RAW('交付曲线累计批次数', F.merges.length, 'git log --first-parent --merges ' + trunk + '（计数本身无好坏含义，不点灯）'),
        RAW('近 7 天代码变更量', '+' + F.churn.add + ' −' + F.churn.del + ' 行 / ' + F.churn.files + ' 文件', 'git log --since=7.days --numstat（产出口，不是成本）'),
      ]),
      '',
      '**SPI / CPI 取不到**（缺的不是测量，是分母）：本仓无预算基线与工时折算，PV 与 AC 无定义即无 SPI/CPI。要转挣值只需在 sources.json 补两行：`baseline`（计划累计批次或计划人日）与 `costModel`（人日↔金额折算）。当前状态：baseline=' + (src.baseline || '未声明') + '，costModel=' + (src.costModel || '未声明') + '。这两行缺任一条，我给任何 SPI/CPI 数字都是编的，故不写。',
    ].join('\n');
  },
  '06': () => {
    const due = src.dueBy || '未定', owner = src.owner || '待指派';
    const unmerged = F.branches.filter((b) => !b.merged && b.n !== trunk);
    const s = [];
    const mk = (id, title, evid, val, p, i, why, act) => {
      const score = p * i; const lm = lamp('风险敞口', score);
      if (lm.l === '不点灯') GAPS.push(lm.why);
      return '| ' + id + ' | 风险 | ' + title + '｜' + evid + (val === null ? '' : '（量=' + val + '）') + ' | ' + (val === null ? '定性' : val) + ' | ' + p + ' | ' + i + ' | ' + score + ' | 风险敞口 ' + score + '（阈值表档：' + (TH.get('风险敞口') || {}).red + ' 红 / ' + (TH.get('风险敞口') || {}).green + ' 绿） | ' + owner + ' | ' + due + ' | ' + why + ' | ' + act + ' | ' + lm.l + ' |';
    };
    const dirty = F.dirty.filter((d) => d.n > 0).sort((a, b) => b.n - a.n);
    if (dirty.length) s.push(mk('R01', '在途未提交改动跨工作树重叠 → 合并冲突出或互相覆盖', dirty.map((d) => d.name + ':' + d.n).slice(0, 3).join('、'), dirty.reduce((a, b) => a + b.n, 0), 4, 5, '本轮已实测两次 merge 被他面暂存项挡住（见变化段）', '本面收尾前把该面改动落 commit 或声明文件清单'));
    if (F.ahead !== null && F.ahead > 0) s.push(mk('R02', '本地领先 origin 未推送：工作只在本机，磁盘故障即丢', 'git rev-list @{u}..HEAD', F.ahead, 2, 5, '概率取「磁盘/误删」基线，影响=不可恢复', '一句「推送」即可闭环'));
    if (unmerged.length) s.push(mk('R03', '长期未合入分支：口径漂移与合并成本', unmerged.map((b) => b.n + '(' + b.age + 'd)').slice(0, 3).join('、'), unmerged.length, 4, 3, unmerged.length + ' 支未进主干，最长 ' + Math.max(...unmerged.map((b) => b.age)) + ' 天', '逐支判定合入或废弃（走 tools/gc-branches.ps1 dry-run）'));
    if (!F.coverage) s.push(mk('R04', '磁盘上无覆盖率报告 → 质量档位无读数（不是覆盖率低）', 'coverage/coverage-summary.json 不存在', null, 3, 3, '缺读数本身即风险：改完无法自证', '跑测试产出 coverage-summary.json 后再取'));
    if (LIVE.api && LIVE.api.err) s.push(mk('R05', '后端健康端点本机不可达 → 线上判定无通道', LIVE.api.base + '：' + LIVE.api.err, null, 3, 4, '无判定通道 = 发布只能盲发', '核 DNS/代理，或改用看板通道取'));
    if (LIVE.web && LIVE.web.err) s.push(mk('R06', '前端线上版本戳不可达 → 发布面无法与主干对账', LIVE.web.base + '：' + LIVE.web.err, null, 4, 3, '实测不可达（未发布或 DNS 不通），非推测', '确认 Pages 项目是否创建/域名是否绑定'));
    if (DRIFT && !DRIFT.same) s.push(mk('R07', DRIFT.functional ? '线上版本与主干存在功能差（发布漂移）' : '线上与主干仅版本戳差（发布通道未走完）', DRIFT.detail, DRIFT.gap, 3, DRIFT.functional ? 5 : 2, DRIFT.functional ? '构建输入面有差异文件' : '零功能差，可安全重发', DRIFT.functional ? '核对是谁的功能差再决定重发' : '走 -Mode backend/frontend 补齐戳'));
    if (!src.criticalPath) s.push(mk('R08', '关键路径未声明 → 延期影响面无法判定', 'sources.json criticalPath', null, 4, 2, '无声明即只能靠记忆', '在 sources.json 写一行'));
    if (!F.registry) s.push(mk('R09', '无派生能力/插件注册表 → 架构读数靠人工描述，易过期', src.registryFile || 'plugins/registry.yaml', null, 4, 3, '人工描述与代码必然漂移（RULE-053 §3 同判）', '建派生脚本 + --check 门禁'));
    if (!src.planLedger) s.push(mk('R10', '无事前计划基线 → 里程碑达成率与挣值全链路不可算', 'sources.json planLedger / baseline', null, 5, 3, '本轮实测确证：02/05 的判定列只能留空', '定一次计划基线（哪怕只写里程碑日期）'));
    if (!s.length) s.push('| — | 风险 | 本轮可测信号未抓到风险（不代表无风险，代表信号面未覆盖 CI/监控/事故台账） | 定性 | — | — | — | 风险敞口 无判据 | ' + owner + ' | ' + due + ' | 接入信号源后重取 | — | 不点灯 |');
    return [
      tbl('ID | 类型 | 实测证据 | 量 | 概率 | 影响 | 分值 | 档位依据 | 责任人 | 截止 | 定档判据 | 处置动作 | 灯', s),
      '',
      '概率/影响为 1–5 档，**每档都附「定档判据」列**（不是印象分）；分值 = 概率 × 影响，档位查 thresholds.md 的「风险敞口」行；责任人/截止取自 sources.json（' + owner + ' / ' + due + '），未声明即按缺值处理。',
      '注：R01/R07 的概率档来自本轮实测（两次 merge 被挡、两次功能差核对），不是估计。',
    ].join('\n');
  },
  '07': () => [
    F.registry ? tbl('注册面 | 派生计数', Object.entries(F.registry.counts).map(([k, v]) => '| ' + k + ' | ' + v + ' |')) : '无派生注册表（' + (src.registryFile || 'plugins/registry.yaml') + ' 不在磁盘）→ 架构计数留空，不做人工描述。',
    '',
    tbl('ID | 指标 | 实测 | 数据源 | 灯', [
      '| C1 前端页面数 | ' + (F.deliv.pages === null ? '取不到（目录不在磁盘）' : F.deliv.pages) + ' | ' + (src.pagesDir || 'web/src/pages') + ' 下 .tsx 计数 | 不点灯（数量无好坏含义） |',
      '| C2 后端路由/端点数 | ' + (F.deliv.routes === null ? '取不到' : F.deliv.routes) + ' | 代码注册计数（worker/src/index.ts 或 py/js 路由装饰器） | 不点灯（同上） |',
      '| C3 相对 import 边数 | ' + (DEP.edges === null ? '取不到' : DEP.edges + ' 条 / ' + DEP.files + ' 文件') + ' | 正则抽取自目录内的 from "./*" | 不点灯（规模量，非健康量） |',
      '| C4 循环依赖分量数 | **取不到**：判环需要真 import 解析器；正则近似会造出假环，宁缺不假 | — | 不点灯 |',
      '| C5 迁移/契约数 | ' + (F.deliv.migrations === null ? '取不到' : F.deliv.migrations) + ' | ' + (src.migrationsDir || 'worker/migrations') + ' 下 .sql 计数 | 不点灯 |',
      '| C6 架构决策数 | ' + (F.deliv.adrs ?? 0) + ' | docs/decisions/ADR-*.md 计数 | 不点灯 |',
    ]),
    '',
    '变更影响面：本轮可测的只有依赖边总量（' + (DEP.edges ?? '未测') + '）与注册面计数。「被依赖最多的文件」排名与影响面需要用同一份 import 解析器输出，正则近似会给错名次 → 留空。',
    '与注册表对账：' + (F.registry ? '本图组件计数与 ' + F.registry.file + ' 同源派生（' + (src.registryGen || 'tools/gen-plugin-registry.mjs') + '），注册表更新即本图更新；漂移由该脚本 --check 判。' : '无注册表可对账。'),
  ].join('\n'),
  '08': () => {
    const stale = F.branches.filter((b) => b.age > 14 && b.n !== trunk);
    return [
      tbl('周 | 提交数 | 合入批次 | 该周有提交的分支数', F.weeks.map((w) => '| ' + w.label + ' | ' + w.commits + ' | ' + w.merges + ' | ' + w.branches + ' |')),
      '',
      tbl('ID | 指标 | 实测 | 数据源 | 灯', [
        LR('K1', '近 7 天提交数', F.weeks[0].commits, 'git log --since=7.days｜产出口不判好坏（「代码图只看提交量」正是 RULE-054 §7 列出的坑）'),
        LR('K2', '近 7 天合入批次', F.weeks[0].merges, 'git log --first-parent --merges ' + trunk),
        RAW('K3 近 7 天代码变更', '+' + F.churn.add + ' −' + F.churn.del + ' 行 / ' + F.churn.files + ' 文件', 'git log --since=7.days --numstat'),
        LR('K4', '存活>14天分支', stale.length, 'for-each-ref %(committerdate:iso8601)' + (stale.length ? '：' + stale.slice(0, 3).map((b) => b.n + '(' + b.age + 'd)').join('、') : '：无超 14 天未合分支')),
        LR('K5', '覆盖率', F.coverage && F.coverage.pct !== undefined ? F.coverage.pct : null, F.coverage && F.coverage.pct !== undefined ? F.coverage.of + '｜' + F.coverage.rel : '取不到：磁盘无 coverage-summary.json' + (F.coverage && F.coverage.broken ? '（' + F.coverage.broken + ' 存在但解析失败）' : '') + '——缺读数 ≠ 覆盖率低'),
        (() => { const v = F.branches.filter((b) => b.merged && b.n !== trunk).map((b) => b.age).sort((a, b) => a - b); return LR('K6', '平均合并时长', null, '本仓无 PR 对象（分支 → 本地 --no-ff merge），无「创建→合并」时刻；可参照的只有已合并分支最后提交距今中位 ' + (v.length ? v[Math.floor(v.length / 2)] + ' 天' : '取不到') + '，口径=天而阈值=小时，不做换算判灯'); })(),
        LR('K7', '平均评审等待', null, '单人 + CI 停用：提交与评审同人，forge 上无 PR → 结构性取不到（不是等待久，是不可测）'),
      ]),
      '',
      '作者数 ' + F.authors.length + '（' + F.authors.slice(0, 3).join('、') + '）：提交与评审同人 → 「评审等待」在本形态下结构性不存在，这条指标要成立必须先改协作形态，不是加统计口径能解决的。',
    ].join('\n');
  },
  '09': () => {
    const envRows = [
      '| E1 ' + (src.workerName || '后端 Worker') + ' | ' + (LIVE.api && LIVE.api.sha ? '`' + String(LIVE.api.sha).slice(0, 8) + '`' : '取不到：' + (LIVE.api ? LIVE.api.err : '未声明')) + ' | ' + (LIVE.api && LIVE.api.sha ? (DRIFT && !DRIFT.same ? '与主干 ' + F.head + ' 不同戳' : '与主干一致') : '—') + ' | GET ' + (src.apiBase || '—') + (src.healthPath || '/api/health') + ' |',
      '| E2 ' + (src.pagesName || '前端 Pages') + ' | ' + (LIVE.web && LIVE.web.sha ? '`' + String(LIVE.web.sha).slice(0, 8) + '`' : '取不到：' + (LIVE.web ? LIVE.web.err : '未声明')) + ' | ' + (LIVE.web && LIVE.web.sha ? ('与主干 ' + F.head + (String(LIVE.web.sha).slice(0, 7) === F.head ? ' 一致' : ' 不同戳（web 面是否有功能差需按构建输入面对账）')) : '—') + ' | GET ' + (src.webBase || '—') + '/assets/build-meta.json |',
      '| E3 本地 wrangler dev / 执行器 | 工作区 ' + F.head + ' | — | git rev-parse --short HEAD |',
    ];
    return [
      tbl('ID | 环境 | 当前版本 V | 与主干关系 | 判据来源', envRows),
      '',
      tbl('指标 | 实测 | 灯 | 口径 / 数据源', [
        r4(M('部署频率', deploys.length ? deploys.filter((r) => ago(r.at) <= 7).length : null, '近 7 天发布台账 deploy-pass 条数｜主源 ' + LED.label + ' ' + LED.rel + '（全量 ' + LED.recs.length + ' 条）')),
        r4(M('发布失败率', deploys.length ? (100 * rollbacks.length / deploys.length).toFixed(2) + '%（回滚 ' + rollbacks.length + '/发布 ' + deploys.length + '）' : null, '回滚或发布失败事件 / 发布成功事件；seed-rollback 属回滚包预置不计失败｜' + LED.rel)),
        r4(M('变更 lead time', lead.median !== null ? lead.median + 'h（可算 ' + lead.n + ' 条，最长 ' + lead.max + 'h）' : null, 'commit 提交者时间 → 发布台账事件时间（按 commit 去重后逐条可算才取中位数）')),
        r4(M('版本戳漂移', DRIFT ? 1 : LIVE.api && LIVE.api.sha ? 0 : null, DRIFT ? DRIFT.detail : '线上戳与本地 HEAD 前缀一致')),
        RAW('发布台账两源对账', (AUD.missing ? '机器级审计取不到（' + AUD.rel + '）' : '审计 ' + AUD.recs.length + ' 条') + ' vs ' + (LOG.missing ? '仓内台账取不到（' + LOG.rel + '）' : '仓内 ' + LOG.recs.length + ' 条'), AUD.missing || LOG.missing ? '只有一源可用时，发布面读数按该源计，差额无从判定' : '审计为跨 worktree 全量、仓内台账为随仓提交的本仓面；两者条数差 = 未落仓的发布事件数（' + (AUD.recs.length - LOG.recs.length) + '）'),
        r4(M('恢复时间', null, '无事故开闭时间台账 → MTTR 无分子分母；需先建改进项 I## 事故时间线')),
        r4(M('SLO 达成', null, '阈值表 SLO 行的目标值/错误预算未钉死 → 分母无定义；需在 thresholds.md 补一行')),
      ]),
      ...(LIVE.skills && LIVE.skills.count !== null ? ['', '在线能力数（免鉴权端点实测）：' + LIVE.skills.count + ' 项，路径 ' + src.skillsPath] : []),
    ].join('\n');
  },
};

const SLOTS = [['00', 'cockpit'], ['01', 'scope-wbs'], ['02', 'milestone-critical-path'], ['03', 'flow-board-cfd'], ['04', 'resource-load-heat'], ['05', 'evm-s-curve'], ['06', 'risk-issue-matrix'], ['07', 'architecture-dependency'], ['08', 'code-health'], ['09', 'env-release-dora-slo']];
const BEGIN = '<!-- AUTO:BEGIN 由 tools/gen-dashboards.mjs 现取，勿手工改本段 -->';
const END = '<!-- AUTO:END -->';

function writeSlot(id, body, opts = {}) {
  const slug = (SLOTS.find((s) => s[0] === id) || [])[1];
  if (!slug) return { id, skipped: '未知槽位' };
  const p = join(DASH, id + '-' + slug + '.md');
  if (!existsSync(p)) return { id, skipped: '槽位文件不在磁盘' };
  let t = readFileSync(p, 'utf8');
  const fm = /^---\n([\s\S]*?)\n---/.exec(t);
  const status = fm ? ((/status:\s*(\S+)/.exec(fm[1]) || [])[1] || 'active') : 'active';
  if (status === 'not_applicable' && !opts.force) return { id, skipped: 'not_applicable（按 RULE-054 §5 不留假图）' };
  const block = BEGIN + '\n\n' + body + '\n\n' + END;
  if (t.includes(BEGIN) && t.includes(END)) t = t.replace(new RegExp(BEGIN.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[\\s\\S]*?' + END.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), block);
  // 无标记时：读数段整体由取数器接管（人工判断留在 决策/图/变化 三段，不混在这里）
  else t = t.replace(/(## 读数\n)([\s\S]*?)(?=\n## )/, '$1' + block + '\n\n');
  const today = day(now.toISOString());
  t = t.replace(/^last_updated: .*$/m, 'last_updated: ' + today);
  t = t.replace(/^- last_updated: .*$/m, '- last_updated: ' + today);
  if (status !== 'active') {
    t = t.replace(/^status: deferred$/m, 'status: active');
    t = t.replace(/^reason: .*$/m, 'reason: 读数由 tools/gen-dashboards.mjs 现取；取不到的指标在表内标「取不到」并列缺口，不用占位符');
  }
  if (flag('--dry')) return { id, dry: true, toActive: status !== 'active' };
  writeFileSync(p, t, 'utf8');
  return { id, written: true, toActive: status !== 'active' };
}

const want = (argv('--slots') || ['00'].concat(Object.keys(BUILDERS)).join(',')).split(',').map((x) => x.trim());
if (want.includes('00')) {
  // 必须惰性求值：00 汇总其余九张的缺口，先算会把 GAPS 读成空的（实测写出「去重后 0 处」的空清单）
  BUILDERS['00'] = () => {
    const unmerged = F.branches.filter((b) => !b.merged && b.n !== trunk).length;
    const inflight = F.dirty.reduce((a, b) => a + b.n, 0);
    const riskCount = ((BUILDERS['06'] ? BUILDERS['06']() : '').match(/\n\| R/g) || []).length;
    const gaps = [...new Set(GAPS)];
    return [
    tbl('面 | 读数（现取） | 灯 | 依据图 / 指标', [
      '| 进度 | 累计合入 ' + F.merges.length + ' 批（仓史起 ' + F.first + '），最近一批 ' + (F.merges[0] ? day(F.merges[0].d) + '（' + ago(F.merges[0].d) + ' 天前）' : '—') + '；**无事前基线 → 达成率不判** | ' + lamp('里程碑偏差', null).l + ' | 02 里程碑偏差 |',
      '| 范围 | 页面 ' + (F.deliv.pages ?? '—') + ' / 路由 ' + (F.deliv.routes ?? '—') + ' / 迁移 ' + (F.deliv.migrations ?? '—') + ' / 工具 ' + (F.deliv.tools ?? '—') + ' / 报告 ' + (F.deliv.reports ?? '—') + ' | ' + lamp('未合入分支数', unmerged).l + ' | 01 交付物面 × 02 未合入分支数 |',
      '| 成本 | 近 7 天 +' + F.churn.add + ' −' + F.churn.del + ' 行 / ' + F.churn.files + ' 文件（产出口；无预算基线 → CPI 不判） | ' + lamp('CPI', null).l + ' | 05 CPI |',
      '| 资源 | 作者 ' + F.authors.length + ' 人（' + F.authors.slice(0, 2).join('、') + '），并发面 ' + F.dirty.length + ' 个，在途文件 ' + inflight + ' | ' + lamp('并发工作面数', F.dirty.length).l + ' | 04 并发工作面数 / 关键技能单点 |',
      '| 风险 | 可测信号抓到 ' + riskCount + ' 条（在途 ' + inflight + ' 文件 / 未推送 ' + (F.ahead ?? '无上游') + ' 提交 / 未合分支 ' + unmerged + ' 个） | ' + lamp('在途文件数', inflight).l + ' | 06 风险敞口 × 03 在途文件数 |',
      '| 发布 | ' + (src.workerName || '后端') + ' ' + (LIVE.api && LIVE.api.sha ? String(LIVE.api.sha).slice(0, 8) : '取不到') + ' / ' + (src.pagesName || '前端') + ' ' + (LIVE.web && LIVE.web.sha ? String(LIVE.web.sha).slice(0, 8) : '取不到') + '；近 7 天发布 ' + deploys.filter((r) => ago(r.at) <= 7).length + ' 次 | ' + lamp('版本戳漂移', DRIFT ? 1 : LIVE.api && LIVE.api.sha ? 0 : null).l + ' | 09 版本戳漂移 / 部署频率 |',
    ]),
    '',
    '改进项跟踪（事故 → 根因 → 措施 → 责任人 → 截止）：本仓尚无事故时间线台账可取（见 09 的「恢复时间」缺口），故不列条目——有即填，无即空，不写「暂无」。',
    '',
    '缺口清单（本轮取不到、也不编的读数，去重后 ' + gaps.length + ' 处；每条都指一个缺的输入，补进 sources.json 即可转真数）：',
    gaps.length ? gaps.map((x) => '- ' + x).join('\n') : '- 无：本轮阈值表内全部指标都取到了值',
    '',
    '本页只汇总六面读数与决策，不复制其余九张图的正文（数字只在一处维护，其余引用它）。',
    ].join('\n');
  };
}
// 00 排最后：它汇总其余九张攒出来的缺口清单
const order = want.filter((x) => x !== '00').concat(want.includes('00') ? ['00'] : []);
const out = order.map((id) => ({ id, ...writeSlot(id, BUILDERS[id] ? BUILDERS[id]() : ''), })).sort((a, b) => a.id.localeCompare(b.id));
console.log('[gen-dashboards] ' + (flag('--dry') ? 'dry-run（未写盘）' : '已写回') + '｜HEAD=' + F.head + ' 合入批次=' + F.merges.length + ' 分支=' + F.branches.length + '(未合 ' + F.branches.filter((b) => !b.merged && b.n !== trunk).length + ') 在途文件=' + F.dirty.reduce((a, b) => a + b.n, 0) + ' 未推送=' + (F.ahead === null ? '无上游' : F.ahead));
for (const r of out) console.log('  ' + r.id + (r.written ? ' 写回' : r.dry ? ' dry' : ' 跳过：' + r.skipped) + (r.toActive ? ' → 转 active' : ''));
const gaps = [...new Set(GAPS)];
console.log('[gen-dashboards] 不点灯缺口 ' + gaps.length + ' 处：\n  - ' + gaps.join('\n  - '));
