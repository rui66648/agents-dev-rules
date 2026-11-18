#!/usr/bin/env node
/**
 * RULE-053 / RULE-052 目录结构门禁（零依赖，规范唯一实现）
 * ============================================================
 * 用法：
 *   node root-cleanliness-check.mjs [--root <目录>] [--allowlist <文件>] [--exemptions <文件>]
 *                                  [--json] [--apply] [--trigger <scheduled|manual|hook>]
 *   node root-cleanliness-check.mjs --emit-allowlist
 *   node root-cleanliness-check.mjs --selftest        # 正/负双向自证，证明门禁不是假绿
 *
 * 落盘纪律：默认 **只读**（DRY-RUN），输出违规清单 + 将要执行的动作摘要，绝不写文件；
 *           只有显式 `--apply` 才会把根级散文件移入 archive/root-cleanup-<YYYYMMDD>/。
 *           （一个能自动改文件的检查器等于拥有否决权，见 2026-11-05 的口径调整。）
 *
 * 豁免真源：hooks/configs/root-exemptions.yaml（fail-closed：缺 reason/review_by、日期非法、
 *           已过期 → 该条目直接判违规，且不进入放行集合；配置缺失 → 不放行任何根级文件）。
 * 运行记录：每次实际运行追加一条 logs/gate-runs/<YYYYMM>.jsonl（schema 见 scripts/gate_runs.py）。
 *
 * 三层判定（口径见 rules/directory-structure.md）：
 *   L1 仓根文件：白名单外或命中命名红线 → FAIL
 *   L2 一级目录：必须「可核算」——被 .gitignore 忽略 / 是独立子仓 / 在 root-structure.json 登记
 *                另外三类直接 FAIL：空目录壳、路径事故目录（含 % 或 : 的拼平路径）、`_*` 等红线名
 *   L3 清单自身：root-structure.json 里已不存在的条目 → FAIL（防止清单与磁盘脱节）
 *
 * 历史缺陷（本版本修正）：v1 只把目录名拿去匹配 DENY_RE，目录永不过白名单 ⇒ `%SystemDrive%`、
 * `NVIDIA Corporation`、拼平路径目录、空目录全部漏判，脏根照样 PASS。
 */
import { execFileSync, spawnSync } from 'node:child_process';
import { readdirSync, statSync, readFileSync, existsSync, mkdirSync, writeFileSync, rmSync, renameSync } from 'node:fs';
import { join, resolve, isAbsolute as path_is_absolute, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { recordGateRun, utcNow } from './lib/gate-run-log.mjs';

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_EXEMPTIONS = resolve(SCRIPT_DIR, '..', 'configs', 'root-exemptions.yaml');

// 豁免配置的 YAML 子集解析：仅支持本文件使用的 schema（entries: 下每项为 path/pattern + 标量字段）。
// 不引入第三方依赖；如未来需要多行/锚点语义，应改用 JSON 或显式解析库。
function parseScalar(raw) {
  const s = raw.trim();
  if ((s.startsWith("'") && s.endsWith("'")) || (s.startsWith('"') && s.endsWith('"'))) {
    const body = s.slice(1, -1);
    return s[0] === "'" ? body.replace(/''/g, "'") : JSON.parse(s);
  }
  return s;
}

function parseExemptions(text) {
  const entries = [];
  let cur = null;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.replace(/\t/g, '  ');
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const item = line.match(/^\s*-\s+(.*)$/);
    if (item) {
      cur = {};
      entries.push(cur);
      const first = item[1].match(/^(path|pattern|reason|owner|review_by)\s*:\s*(.*)$/);
      if (first) cur[first[1]] = parseScalar(first[2]);
      continue;
    }
    const kv = line.match(/^\s+(path|pattern|reason|owner|review_by)\s*:\s*(.*)$/);
    if (kv && cur) cur[kv[1]] = parseScalar(kv[2]);
  }
  return entries;
}

function localToday() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** fail-closed：不完整/过期/格式非法的条目一律变成违规，且绝不进入放行集合。 */
function loadExemptions(file) {
  const problems = [];
  const paths = new Set();
  const patterns = [];
  if (!existsSync(file)) {
    problems.push({
      name: file,
      kind: 'exemptions-missing',
      dest: '豁免配置缺失：不放行任何根级文件（fail closed），请创建 hooks/configs/root-exemptions.yaml',
    });
    return { paths, patterns, problems, source: file, missing: true };
  }
  let entries = [];
  try {
    entries = parseExemptions(readFileSync(file, 'utf8'));
  } catch (e) {
    problems.push({ name: file, kind: 'exemptions-broken', dest: `豁免配置读取失败：${e.message}（不放行任何文件）` });
    return { paths, patterns, problems, source: file, broken: true };
  }
  const today = localToday();
  entries.forEach((entry, index) => {
    const label = entry.path || entry.pattern || `entries[${index}]`;
    if (!String(entry.reason || '').trim() || !String(entry.review_by || '').trim()) {
      problems.push({ name: label, kind: 'exemption-incomplete', dest: '豁免条目缺少 reason/review_by，按违规处理' });
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(entry.review_by)) {
      problems.push({ name: label, kind: 'exemption-invalid-date', dest: `review_by 格式非法（${entry.review_by}），按违规处理` });
      return;
    }
    if (entry.review_by < today) {
      problems.push({ name: label, kind: 'exemption-expired', dest: `豁免已过期（review_by=${entry.review_by}），请复核或续期` });
      return;
    }
    if (entry.path) {
      paths.add(entry.path);
    } else if (entry.pattern) {
      try {
        patterns.push(new RegExp(entry.pattern));
      } catch {
        problems.push({ name: label, kind: 'exemption-invalid-pattern', dest: `pattern 无法编译：${entry.pattern}` });
      }
    } else {
      problems.push({ name: label, kind: 'exemption-incomplete', dest: '豁免条目必须含 path 或 pattern' });
    }
  });
  return { paths, patterns, problems, source: file };
}
const DENY_RE = [
  /^_/, /^\.tmp/i, /\.tmp\.json$/i, /^check[-_]/, /^analyze_/, /^batch_.+\.py$/, /^debug[-_]/,
  /\.log$/i, /\.db$/i, /\.(cer|pem|crt|key)$/i, /^kbp_/, /^[^/\\]*\.png$/i, /\.bak$/i, /^nul$/i,
];
const DIR_ALWAYS_OK = new Set(['.git']);
const ACCIDENT_RE = /[%:]/;
const CLASSES = new Set(['engineering', 'artifact', 'data', 'external']);

const arg = (name) => {
  const i = process.argv.indexOf(name);
  return i > -1 ? process.argv[i + 1] : undefined;
};
const flag = (name) => process.argv.includes(name);

const isAllowedFile = (n, exempt) => exempt.paths.has(n) || exempt.patterns.some((r) => r.test(n));
const deniedBy = (n) => DENY_RE.find((r) => r.test(n));

function git(root, args) {
  try {
    return execFileSync('git', ['-C', root, ...args], { encoding: 'utf8' });
  } catch {
    return '';
  }
}

function isGitIgnored(root, name) {
  return spawnSync('git', ['-C', root, 'check-ignore', '-q', name], { encoding: 'utf8' }).status === 0;
}

function hasFilesDeep(dir) {
  let stack = [dir];
  while (stack.length) {
    const cur = stack.pop();
    let entries = [];
    try {
      entries = readdirSync(cur, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const e of entries) {
      if (e.isFile()) return true;
      if (e.isDirectory()) stack.push(join(cur, e.name));
    }
  }
  return false;
}

function loadAllowlist(root, file) {
  const abs = path_is_absolute(file) ? file : join(root, file);
  if (!existsSync(abs)) return { file, dirs: {}, missing: true };
  try {
    const j = JSON.parse(readFileSync(abs, 'utf8'));
    return { file, dirs: j.dirs || {}, missing: false };
  } catch (e) {
    return { file, dirs: {}, missing: false, broken: String(e.message) };
  }
}

export function check(root, exemptionsFile) {
  const allow = loadAllowlist(root, arg('--allowlist') || join('tools', 'root-structure.json'));
  const exempt = loadExemptions(exemptionsFile || arg('--exemptions') || DEFAULT_EXEMPTIONS);
  const v = [...exempt.problems];

  for (const name of readdirSync(root)) {
    let isDir = false;
    try {
      isDir = statSync(join(root, name)).isDirectory();
    } catch {
      continue;
    }

    if (name === '.git') continue; // 主仓目录或 worktree 指针文件，均不参与判定
    if (isDir) {
      if (DIR_ALWAYS_OK.has(name)) continue;
      if (deniedBy(name)) {
        v.push({ name, kind: 'dir-deny-pattern', dest: 'archive/<用途>-<YYYY-MM-DD>/（或 tools/ 若长期使用）' });
        continue;
      }
      if (ACCIDENT_RE.test(name)) {
        v.push({ name, kind: 'path-accident-dir', dest: '直接移除（路径拼接事故产物，无内容即无归档价值）' });
        continue;
      }
      // 已核算的三种形态（子仓 / .gitignore 忽略）先看，再看空壳：
      // 被忽略的工具态目录（如 .wrangler、dist）当下是否为空由工具自己决定，不是仓库的违规
      if (existsSync(join(root, name, '.git'))) continue; // 独立子仓：已核算
      if (isGitIgnored(root, name)) continue; // .gitignore 明确忽略：已核算
      if (!hasFilesDeep(join(root, name))) {
        v.push({ name, kind: 'empty-dir', dest: '直接移除，或在 root-structure.json 写明用途' });
        continue;
      }
      const entry = allow.dirs[name];
      if (!entry) {
        v.push({ name, kind: 'unaccounted-dir', dest: `在 ${allow.file} 登记 class（engineering/artifact/data/external）+ reason，或写进 .gitignore` });
      } else if (!CLASSES.has(entry.class)) {
        v.push({ name, kind: 'bad-class', dest: `class 必须是 ${[...CLASSES].join('/')}，当前为 ${entry.class}` });
      } else if (!String(entry.reason || '').trim()) {
        v.push({ name, kind: 'no-reason', dest: 'root-structure.json 条目必须写 reason' });
      }
      continue;
    }

    if (isAllowedFile(name, exempt)) continue;
    v.push({
      name,
      kind: deniedBy(name) ? 'deny-pattern' : 'not-allowlisted',
      dest: deniedBy(name) ? 'archive/<用途>-<YYYY-MM-DD>/（或 tools/ 若长期使用）' : name.endsWith('.md') ? 'docs/reports/<主题>-<YYYY-MM-DD>.md' : 'outputs/ 或 tools/',
    });
  }

  // L3：清单条目必须仍然对应磁盘上的目录（防清单与磁盘脱节）
  // 分档：工程目录缺失 = 检出残缺，FAIL；产物/数据/外部目录本就可能未生成
  //（scratch worktree、干净检出的 outputs/ .wrangler 等），降为 WARN，否则每个干净 worktree 都假红
  const present = new Set(readdirSync(root).filter((n) => {
    try {
      return statSync(join(root, n)).isDirectory();
    } catch {
      return false;
    }
  }));
  const warn = [];
  for (const name of Object.keys(allow.dirs)) {
    if (present.has(name)) continue;
    const item = { name, kind: 'stale-allowlist-entry', dest: `class=${allow.dirs[name].class}：工程目录缺失请核对检出是否完整；产物/数据目录未生成属正常，条目保留即可` };
    if (allow.dirs[name].class === 'engineering') v.push(item);
    else warn.push(item);
  }
  if (allow.missing) v.push({ name: allow.file, kind: 'allowlist-missing', dest: '运行 --emit-allowlist 生成草稿后逐项核实 class/reason' });
  if (allow.broken) v.push({ name: allow.file, kind: 'allowlist-broken', dest: allow.broken });

  // L1 补充：根级未跟踪新文件（白名单外）
  for (const line of git(root, ['status', '--porcelain', '--untracked-files=normal']).split('\n')) {
    if (!line.startsWith('?? ')) continue;
    const p = line.slice(3).trim().replace(/^"|"$/g, '');
    if (p.includes('/') || p.includes('\\')) continue;
    if (isAllowedFile(p, exempt) || v.some((x) => x.name === p)) continue;
    v.push({ name: p, kind: 'new-untracked', dest: p.endsWith('.md') ? 'docs/reports/<主题>-<YYYY-MM-DD>.md' : 'outputs/ 或 tools/' });
  }

  return { root, violations: v, warnings: warn, allowlist: allow.file, allowlistMissing: Boolean(allow.missing), exemptions: exempt.source };
}

function emitAllowlist(root) {
  const names = readdirSync(root).filter((n) => {
    try {
      return statSync(join(root, n)).isDirectory();
    } catch {
      return false;
    }
  });
  const dirs = {};
  for (const n of names) {
    if (DIR_ALWAYS_OK.has(n)) continue;
    if (ACCIDENT_RE.test(n) || !hasFilesDeep(join(root, n))) continue; // 事故目录/空壳不登记
    let klass = 'unclassified';
    let reason = '待核实：本脚本仅给出草稿，必须人工确认用途后保留';
    if (existsSync(join(root, n, '.git'))) {
      klass = 'external';
      reason = '独立 git 子仓';
    } else if (isGitIgnored(root, n)) {
      continue; // 已被 .gitignore 忽略，无需登记
    } else if (/^(docs|tools|scripts|src|tests|deploy|migrations|supabase|shared|packages?)$/.test(n)) {
      klass = 'engineering';
    } else if (/^(archive|outputs|screenshots|mockups|research|test-results|vendor-refs|extensions)$/.test(n)) {
      klass = 'artifact';
    } else if (/^(data|chroma_data|blobs|KnowledgeGraph|pharmakg|hetionet|d1_full_backup|eval|requirements|lineage|telemetry)$/.test(n)) {
      klass = 'data';
    }
    dirs[n] = { class: klass === 'unclassified' ? 'engineering' : klass, reason };
  }
  const out = join(root, 'tools', 'root-structure.json');
  mkdirSync(join(root, 'tools'), { recursive: true });
  writeFileSync(out, JSON.stringify({ schema: 1, generator: 'hooks/scripts/root-cleanliness-check.mjs --emit-allowlist', dirs }, null, 2), 'utf8');
  return out;
}

// ── --selftest：正向（干净根）与负向（各类违规）都必须如预期 ────────────────
function selftest() {
  const sandbox = join(tmpdir(), `root-hygiene-selftest-${Date.now()}`);
  const results = [];
  const cfgClean = join(tmpdir(), `root-exempt-selftest-clean-${Date.now()}.yaml`);
  const cfgExpired = join(tmpdir(), `root-exempt-selftest-expired-${Date.now()}.yaml`);
  const cfgNoReason = join(tmpdir(), `root-exempt-selftest-noreason-${Date.now()}.yaml`);
  try {
    mkdirSync(join(sandbox, 'tools'), { recursive: true });
    git(sandbox, ['init', '-q', '.']);
    writeFileSync(join(sandbox, 'AGENTS.md'), '# x', 'utf8');
    writeFileSync(join(sandbox, '.gitignore'), 'ignored-data/\nignored-empty/\n', 'utf8');
    mkdirSync(join(sandbox, 'ignored-data'));
    writeFileSync(join(sandbox, 'ignored-data', 'a.bin'), 'x', 'utf8');
    mkdirSync(join(sandbox, 'ignored-empty')); // 被忽略且当前为空（如 .wrangler）：不得判违规
    mkdirSync(join(sandbox, 'docs'));
    writeFileSync(join(sandbox, 'docs', 'a.md'), 'x', 'utf8');
    writeFileSync(join(sandbox, 'tools', 'root-structure.json'), JSON.stringify({ dirs: { docs: { class: 'engineering', reason: '文档' }, tools: { class: 'engineering', reason: '工具' } } }), 'utf8');

    // 干净的临时豁免配置：只放行 selftest 根里真实存在的两个文件
    writeFileSync(cfgClean, [
      'entries:',
      '  - path: AGENTS.md',
      "    reason: '入口文件'",
      '    owner: rules-maintainer',
      '    review_by: 2099-12-31',
      '  - path: .gitignore',
      "    reason: 'Git 忽略规则'",
      '    owner: rules-maintainer',
      '    review_by: 2099-12-31',
      '',
    ].join('\n'), 'utf8');

    const clean = check(sandbox, cfgClean);
    results.push({ case: '干净根应 PASS', ok: clean.violations.length === 0, detail: clean.violations.map((x) => `${x.name}:${x.kind}`).join(', ') });

    mkdirSync(join(sandbox, '%SystemDrive%'));                       // 路径事故 + 空
    mkdirSync(join(sandbox, 'ProgramData%target%'));                 // 路径事故（非空）
    writeFileSync(join(sandbox, 'ProgramData%target%', 'x.txt'), 'x', 'utf8');
    mkdirSync(join(sandbox, 'mystery'));                              // 未登记一级目录
    writeFileSync(join(sandbox, 'mystery', 'y.txt'), 'y', 'utf8');
    mkdirSync(join(sandbox, 'emptyshell'));                           // 空目录
    writeFileSync(join(sandbox, 'scratch_report.md'), 'z', 'utf8');   // 根级产物
    const dirty = check(sandbox, cfgClean);
    const kinds = new Set(dirty.violations.map((x) => `${x.name}:${x.kind}`));
    const expect = [
      '%SystemDrive%:path-accident-dir',
      'ProgramData%target%:path-accident-dir',
      'mystery:unaccounted-dir',
      'emptyshell:empty-dir',
      'scratch_report.md:not-allowlisted',
    ];
    results.push({ case: '五类违规必须全部被抓出', ok: expect.every((e) => kinds.has(e)), detail: expect.filter((e) => !kinds.has(e)).join(' | ') || '全中' });

    const stale = join(sandbox, 'tools', 'root-structure.json');
    writeFileSync(stale, JSON.stringify({ dirs: { docs: { class: 'engineering', reason: '文档' }, tools: { class: 'engineering', reason: '工具' }, ghost: { class: 'data', reason: '已不存在' }, vanished: { class: 'engineering', reason: '工程目录却不在磁盘上' } } }), 'utf8');
    const after = check(sandbox, cfgClean);
    results.push({ case: '僵尸清单条目：工程类缺失 = FAIL', ok: after.violations.some((x) => x.kind === 'stale-allowlist-entry' && x.name === 'vanished'), detail: 'vanished 条目' });
    results.push({ case: '产物/数据类目录未生成 = WARN 而不是 FAIL（干净 worktree 不得假红）', ok: after.warnings.some((x) => x.kind === 'stale-allowlist-entry' && x.name === 'ghost') && !after.violations.some((x) => x.name === 'ghost'), detail: 'ghost 条目' });

    // ④ fail-closed 三连：过期 / 缺 reason / 配置缺失，都必须红
    writeFileSync(cfgExpired, [
      'entries:',
      '  - path: AGENTS.md',
      "    reason: '入口文件'",
      '    owner: rules-maintainer',
      '    review_by: 2000-01-01',
      '',
    ].join('\n'), 'utf8');
    const expired = check(sandbox, cfgExpired);
    results.push({
      case: '过期豁免必须报红（fail closed）',
      ok: expired.violations.some((x) => x.kind === 'exemption-expired'),
      detail: expired.violations.find((x) => x.kind === 'exemption-expired')?.dest || '未报红',
    });

    writeFileSync(cfgNoReason, [
      'entries:',
      '  - path: AGENTS.md',
      '    owner: rules-maintainer',
      '    review_by: 2099-12-31',
      '',
    ].join('\n'), 'utf8');
    const noReason = check(sandbox, cfgNoReason);
    results.push({
      case: '缺 reason 必须报红（fail closed）',
      ok: noReason.violations.some((x) => x.kind === 'exemption-incomplete'),
      detail: noReason.violations.find((x) => x.kind === 'exemption-incomplete')?.dest || '未报红',
    });

    const missing = check(sandbox, join(tmpdir(), `root-exempt-selftest-absent-${Date.now()}.yaml`));
    results.push({
      case: '豁免配置缺失必须报红（无永久放行兜底）',
      ok: missing.violations.some((x) => x.kind === 'exemptions-missing'),
      detail: missing.violations.find((x) => x.kind === 'exemptions-missing')?.dest || '未报红',
    });
  } finally {
    rmSync(sandbox, { recursive: true, force: true });
    for (const f of [cfgClean, cfgExpired, cfgNoReason]) rmSync(f, { force: true });
  }

  const failed = results.filter((r) => !r.ok);
  for (const r of results) console.log(`[selftest] ${r.ok ? 'OK  ' : 'FAIL'} ${r.case} — ${r.detail}`);
  console.log(failed.length ? `[selftest] FAIL — 门禁本身有缺陷（${failed.length} 项）` : '[selftest] PASS — 正负双向自证通过');
  process.exit(failed.length ? 1 : 0);
}

const root = resolve(arg('--root') || process.cwd());
if (flag('--selftest')) selftest();
if (flag('--emit-allowlist')) {
  console.log(`[root-hygiene] 草稿清单已写出：${emitAllowlist(root)}（必须人工核实 class 与 reason）`);
  process.exit(0);
}

// ── --mrs：遍历 managed-root-set.json 所有受管根，聚合 violations ──
if (arg('--mrs')) {
  const mrsPath = resolve(arg('--mrs'));
  if (!existsSync(mrsPath)) {
    console.error(`[root-hygiene] MRS 文件不存在：${mrsPath}`);
    process.exit(2);
  }
  const mrs = JSON.parse(readFileSync(mrsPath, 'utf8'));
  const allRoots = mrs.roots || [];
  const aggregated = { roots: [], totalViolations: 0, totalWarnings: 0, scanned: 0, skipped: 0 };

  for (const r of allRoots) {
    if (r.scan === false) {
      aggregated.roots.push({ path: r.path, kind: r.kind, scanned: false, bypass: true, violations: [], warnings: [] });
      aggregated.skipped += 1;
      continue;
    }
    const rp = resolve(r.path);
    if (!existsSync(rp)) {
      aggregated.roots.push({ path: r.path, kind: r.kind, scanned: false, error: '目录不存在', violations: [], warnings: [] });
      aggregated.skipped += 1;
      continue;
    }
    const rep = check(rp);
    aggregated.roots.push({
      path: r.path,
      kind: r.kind,
      scanned: true,
      violations: rep.violations,
      warnings: rep.warnings || [],
      allowlist: rep.allowlist,
    });
    aggregated.totalViolations += rep.violations.length;
    aggregated.totalWarnings += (rep.warnings || []).length;
    aggregated.scanned += 1;
  }

  if (flag('--json')) {
    console.log(JSON.stringify(aggregated, null, 2));
  } else {
    console.log(`[managed-root-hygiene] 扫描 ${aggregated.scanned} 个受管根（跳过 ${aggregated.skipped}），违规 ${aggregated.totalViolations} 项，警告 ${aggregated.totalWarnings} 项`);
    for (const rootReport of aggregated.roots) {
      if (rootReport.bypass) { console.log(`  [BYPASS] ${rootReport.path} (${rootReport.kind}, scan:false)`); continue; }
      if (rootReport.error) { console.log(`  [ERROR]   ${rootReport.path} — ${rootReport.error}`); continue; }
      const tag = rootReport.violations.length ? 'FAIL' : 'PASS';
      console.log(`  [${tag}]     ${rootReport.path} (${rootReport.kind}) — ${rootReport.violations.length} violations, ${rootReport.warnings.length} warnings`);
      for (const x of rootReport.violations) console.log(`    - ${x.name}  [${x.kind}]  → ${x.dest}`);
      for (const x of rootReport.warnings) console.log(`    [WARN] ${x.name}  [${x.kind}]`);
    }
  }
  try {
    recordGateRun({
      gateId: 'managed-root-cleanliness',
      mode: 'dry-run',
      trigger: String(arg('--trigger') || process.env.GATE_TRIGGER || 'manual').toLowerCase(),
      result: aggregated.totalViolations ? 'FAIL' : 'PASS',
      ruleIds: ['RULE-052', 'RULE-053'],
      evidence: { mrs: mrsPath, scanned: aggregated.scanned, skipped: aggregated.skipped, totalViolations: aggregated.totalViolations, totalWarnings: aggregated.totalWarnings },
      startedAt: utcNow(),
      exitCode: aggregated.totalViolations ? 1 : 0,
    });
  } catch {}
  process.exit(aggregated.totalViolations ? 1 : 0);
}

// ── 运行记录（②）：每次实际运行追加一条；写失败降级为 FAIL 并退出非 0 ──
const startedAt = utcNow();
const trigger = String(arg('--trigger') || process.env.GATE_TRIGGER || 'manual').toLowerCase();
if (!['scheduled', 'manual', 'hook'].includes(trigger)) {
  console.error(`[gate-runs] 非法 trigger=${trigger}（允许 scheduled/manual/hook）；未记录，退出 2`);
  process.exit(2);
}
function emitRun({ mode, result, exitCode, evidence }) {
  try {
    recordGateRun({
      gateId: 'root-cleanliness',
      mode,
      trigger,
      result,
      ruleIds: ['RULE-052', 'RULE-053'],
      evidence,
      startedAt,
      exitCode,
    });
  } catch (e) {
    console.error(`[gate-runs] 记录写入失败：${e.message} → 本次运行按 FAIL 处理`);
    process.exit(1);
  }
  process.exit(exitCode);
}
const evidenceOf = (rep, extra = {}) => ({
  checker: 'hooks/scripts/root-cleanliness-check.mjs',
  root,
  exemptions: rep.exemptions,
  violations: rep.violations.length,
  warnings: (rep.warnings || []).length,
  sample: rep.violations.slice(0, 5).map((x) => `${x.name}[${x.kind}]`),
  ...extra,
});

const report = check(root);

// ── 落盘提案：默认只读；--apply 才把根级散文件移入 archive/root-cleanup-<YYYYMMDD>/ ──
// 只处理"文件"类违规；目录类（空壳/未登记/事故目录）一律只提案，交由人判断。
const QUARANTINE_KINDS = new Set(['deny-pattern', 'not-allowlisted', 'new-untracked']);
const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
const destRel = `archive/root-cleanup-${stamp}`;
const actions = report.violations
  .filter((x) => QUARANTINE_KINDS.has(x.kind))
  .map((x) => ({ name: x.name, kind: x.kind }));

if (flag('--apply')) {
  const destDir = join(root, destRel);
  let moved = 0;
  if (actions.length) mkdirSync(destDir, { recursive: true });
  for (const a of actions) {
    renameSync(join(root, a.name), join(destDir, a.name));
    moved += 1;
  }
  const after = check(root);
  const exitCode = after.violations.length ? 1 : 0;
  if (flag('--json')) {
    console.log(JSON.stringify(after, null, 2));
  } else {
    console.log(`[root-hygiene] APPLY — 已移动 ${moved} 项到 ${destRel}/（其余目录类违规仅提案，未处理）`);
    if (after.violations.length) {
      console.log(`[root-hygiene] 落盘后仍有 ${after.violations.length} 项违规（需人工处置）:`);
      for (const x of after.violations) console.log(`  - ${x.name}  [${x.kind}]  → ${x.dest}`);
    } else {
      console.log('[root-hygiene] APPLY 后 PASS — 仓根洁净 + 一级目录全部可核算');
    }
    if (moved) console.log(`[root-hygiene] 回滚：tracked 文件用 git checkout -- <path>；新增文件从 ${destRel}/ 移回原位`);
  }
  emitRun({
    mode: 'apply',
    result: exitCode ? 'FAIL' : 'PASS',
    exitCode,
    evidence: evidenceOf(after, { moved }),
  });
}

if (flag('--json')) {
  console.log(JSON.stringify(report, null, 2));
} else if (report.violations.length === 0) {
  console.log('[root-hygiene] PASS — 仓根洁净 + 一级目录全部可核算（RULE-052/RULE-053）');
} else {
  console.log(`[root-hygiene] DRY-RUN — ${report.violations.length} 项违规（未写盘；加 --apply 才落盘）`);
  for (const x of report.violations) console.log(`  - ${x.name}  [${x.kind}]  → ${x.dest}`);
  if (actions.length) {
    console.log(`[root-hygiene] 可执行动作 ${actions.length} 项（--apply 时执行）：`);
    for (const a of actions) console.log(`  - move ${a.name}  → ${destRel}/${a.name}`);
  }
}
for (const x of report.warnings || []) console.log(`  [WARN] ${x.name}  [${x.kind}]  → ${x.dest}`);
const exitCode = report.violations.length ? 1 : 0;
emitRun({
  mode: 'dry-run',
  result: exitCode ? 'FAIL' : 'PASS',
  exitCode,
  evidence: evidenceOf(report),
});
