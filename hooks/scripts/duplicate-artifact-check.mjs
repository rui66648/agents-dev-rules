#!/usr/bin/env node
/**
 * RULE-053 §3.5 生成任务查重门禁（观察期 / WARN only，零依赖）
 * ==========================================================
 * 用法：
 *   node duplicate-artifact-check.mjs --root <目录> --check [--json] [--min-cluster N]
 *   node duplicate-artifact-check.mjs --selftest
 *
 * 观察期口径（v4.17.0）：只读、绝不写文件、退出码恒 0（参数错误 / 自证失败除外）。
 * 输出的是「候选」，不是判定：命中后按 rules/directory-structure.md §3.5 的四步由人判定
 * 就地修改 / 指针化 / 合法例外 / 确实可新建。挂硬拦截前必须先清零误报。
 *
 * 三类信号：
 *   EXACT   —— SHA256 完全相同（同一份内容被复制成多个文件）
 *   TOPIC   —— 文件名归一化后主题键相同（去日期 / 版本 / 体裁词 / 副本后缀），且落在多个目录
 *   CLUSTER —— 同一父目录下 >=3 份同体裁文档（报告 / 分析 / 评估 / 盘点 / 矩阵…），
 *              提示「同主题层层新建」；召回优先，人工复核
 *
 * 合法例外（§3.5）：冻结仓、archive/、_worktrees/、脚本派生 staged/、一次性实测快照，
 * 以及 .git / node_modules / 构建产物等工具态目录，均在遍历阶段排除。
 */
import {
  readdirSync, readFileSync, statSync, existsSync, mkdtempSync,
  mkdirSync, writeFileSync, rmSync,
} from 'node:fs';
import { createHash } from 'node:crypto';
import { join, resolve, relative, basename, extname, dirname, sep } from 'node:path';
import { tmpdir } from 'node:os';

const EXCLUDE_DIRS = new Set([
  '.git', '.hg', '.svn', 'node_modules', 'dist', 'build', 'coverage', '.venv', '__pycache__',
  'archive', '_worktrees', '.worktrees', 'staged', 'blobs', 'vendor-refs', 'call_logs',
  'audit-logs', '.trae', '.zcode', '.wrangler', '.cache',
]);
const EXCLUDE_FILE = /(?:^|[._-])(?:pre|post)-fix-repro|\.log$/i;
const SCAN_EXT = new Set(['.md', '.markdown', '.html', '.htm']);
const GENRE_WORDS = [
  '报告', '分析', '评估', '盘点', '差距', '矩阵', '对齐', '方案', '汇总', '说明', '总结', '复核',
  'report', 'analysis', 'review', 'summary',
];
const NOISE_WORDS = [
  ...GENRE_WORDS, '文档', '执行', '最终', '新版', '修订', '副本', '初稿', '草稿',
  'final', 'new', 'copy', 'draft', 'v2', 'updated', 'revised', 'latest',
];
const MAX_BYTES = 2 * 1024 * 1024; // 内嵌快照型大 HTML 不参与主题比对

// 包级结构性入口：一包一份是结构要求，只跳 TOPIC 判定、仍参与 EXACT（RULE-053 §3.5 合法例外）
const STRUCTURAL_BASENAME = /^(?:readme|changelog|index|agents|claude|contributing|license|notice|security|codeowners|template|manifest)(?:[-._].*)?$/i;

const HELP = `RULE-053 §3.5 duplicate-artifact-check (OBSERVE / WARN only)
  --root <dir>        扫描根目录，默认 cwd
  --check             只读检查（观察期默认行为，与不传等价）
  --json              输出 JSON
  --min-cluster <n>   CLUSTER 阈值，默认 3
  --selftest          临时目录构造正/负例自证，不触碰工作区
  -h, --help          显示本帮助
  包级 README/CHANGELOG/index/AGENTS 等结构性入口只跳 TOPIC；内容完全相同仍按 EXACT 报出`;

function parseArgs(argv) {
  const a = { root: process.cwd(), check: false, json: false, selftest: false, minCluster: 3, help: false };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v === '--root' && argv[i + 1]) a.root = resolve(argv[++i]);
    else if (v === '--check') a.check = true;
    else if (v === '--json') a.json = true;
    else if (v === '--selftest') a.selftest = true;
    else if (v === '--min-cluster' && argv[i + 1]) a.minCluster = Number(argv[++i]) || 3;
    else if (v === '-h' || v === '--help') a.help = true;
  }
  return a;
}

function walk(root, out) {
  const stack = [root];
  while (stack.length) {
    const dir = stack.pop();
    let entries;
    try { entries = readdirSync(dir, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (e.isDirectory()) {
        if (!EXCLUDE_DIRS.has(e.name) && !e.name.startsWith('.')) stack.push(join(dir, e.name));
        continue;
      }
      if (!e.isFile()) continue;
      const p = join(dir, e.name);
      if (!SCAN_EXT.has(extname(e.name).toLowerCase()) || EXCLUDE_FILE.test(e.name)) continue;
      try {
        const st = statSync(p);
        if (st.size > MAX_BYTES) continue;
        out.push({ rel: relative(root, p).split(sep).join('/'), buf: readFileSync(p) });
      } catch { /* 不可读文件跳过：不制造假绿，也不让门禁崩掉 */ }
    }
  }
}

function topicKey(rel) {
  let s = basename(rel).replace(/\.(?:md|markdown|html|htm)$/i, '').toLowerCase();
  s = s.replace(/\d{4}[-_]?\d{2}[-_]?\d{2}|\d{8}/g, ' ');
  s = s.replace(/v\d+(?:\.\d+)*/g, ' ');
  for (const w of NOISE_WORDS) s = s.split(w.toLowerCase()).join(' ');
  s = s.replace(/[^a-z0-9\u4e00-\u9fff]+/g, '');
  return s;
}

function genreOf(rel) {
  const n = basename(rel).toLowerCase();
  return GENRE_WORDS.find((w) => n.includes(w.toLowerCase())) || null;
}

function analyze(root, minCluster) {
  const files = [];
  walk(root, files);
  const byHash = new Map();
  const byTopic = new Map();
  const byGenreDir = new Map();
  for (const f of files) {
    const h = createHash('sha256').update(f.buf).digest('hex');
    if (!byHash.has(h)) byHash.set(h, []);
    byHash.get(h).push(f.rel);

    const k = topicKey(f.rel);
    const stem = basename(f.rel).replace(/\.(?:md|markdown|html|htm)$/i, '');
    if (k && k.length >= 4 && !STRUCTURAL_BASENAME.test(stem)) {
      if (!byTopic.has(k)) byTopic.set(k, []);
      byTopic.get(k).push(f.rel);
    }

    const g = genreOf(f.rel);
    if (g) {
      const ck = `${dirname(f.rel)}::${g}`;
      if (!byGenreDir.has(ck)) byGenreDir.set(ck, []);
      byGenreDir.get(ck).push(f.rel);
    }
  }

  const findings = [];
  for (const [h, list] of byHash) {
    if (list.length > 1) findings.push({ kind: 'EXACT', key: h.slice(0, 12), files: list });
  }
  for (const [k, list] of byTopic) {
    if (list.length > 1 && new Set(list.map((p) => dirname(p))).size > 1) {
      findings.push({ kind: 'TOPIC', key: k, files: list });
    }
  }
  for (const [k, list] of byGenreDir) {
    if (list.length >= minCluster) findings.push({ kind: 'CLUSTER', key: k, files: list });
  }
  return { root, scanned: files.length, findings };
}

function selftest() {
  const t = mkdtempSync(join(tmpdir(), 'dupcheck-'));
  const passed = [];
  try {
    const put = (rel, text) => {
      const p = join(t, rel);
      mkdirSync(dirname(p), { recursive: true });
      writeFileSync(p, text, 'utf8');
    };
    put('docs/reports/example-workspace-文档盘点-2026-11-09.md', 'SAME BODY');
    put('outputs/example-workspace-文档盘点.md', 'SAME BODY');
    put('docs/designs/架构设计.md', 'OTHER BODY');
    put('archive/old/example-workspace-文档盘点.md', 'SAME BODY'); // 合法例外，应被排除

    // 包级结构性入口：内容不同不报 TOPIC；内容完全相同仍必须报 EXACT
    put('pkg-a/README.md', 'A README BODY');
    put('pkg-b/README.md', 'B README BODY');
    put('pkg-c/README.md', 'A README BODY');

    const r = analyze(t, 3);
    const exact = r.findings.filter((f) => f.kind === 'EXACT');
    const topic = r.findings.filter((f) => f.kind === 'TOPIC');
    const dumped = JSON.stringify(r.findings);
    const assert = (cond, msg) => {
      if (!cond) throw new Error(msg);
      passed.push(msg);
    };
    assert(r.scanned === 6, '仅扫描到 6 份非例外文件');
    assert(exact.length === 2, '检出 2 组精确重复（含结构性 README 真重复）');
    assert(topic.length >= 1, '去日期后仍检出同主题归一化候选');
    assert(!JSON.stringify(topic).includes('README.md'), '包级结构性 README 不参与 TOPIC 判定');
    assert(exact.some((f) => f.files.some((p) => p.includes('README.md'))), '结构性 README 内容相同仍按 EXACT 报出');
    assert(!dumped.includes('架构设计'), '不同主题未被误报');
    assert(!dumped.includes('archive/'), 'archive 合法例外未被计入');
    console.log('[selftest] PASS');
    for (const m of passed) console.log('  + ' + m);
    return 0;
  } catch (e) {
    console.error('[selftest] FAIL: ' + e.message);
    return 1;
  } finally {
    rmSync(t, { recursive: true, force: true });
  }
}

function main() {
  const a = parseArgs(process.argv.slice(2));
  if (a.help) { console.log(HELP); return 0; }
  if (a.selftest) return selftest();
  if (!existsSync(a.root) || !statSync(a.root).isDirectory()) {
    console.error(`[dupcheck] root 不存在或不是目录: ${a.root}`);
    return 2;
  }
  const r = analyze(a.root, a.minCluster);
  if (a.json) {
    console.log(JSON.stringify({ ...r, mode: 'OBSERVE_WARN_ONLY' }, null, 2));
    return 0;
  }
  console.log(`[dupcheck] root=${r.root}`);
  console.log(`[dupcheck] scanned=${r.scanned} findings=${r.findings.length} mode=OBSERVE(WARN only, exit 0)`);
  for (const f of r.findings) {
    console.log(`  [${f.kind}] ${f.key}`);
    for (const p of f.files) console.log(`      - ${p}`);
  }
  console.log('[dupcheck] 候选需人工按 RULE-053 §3.5 四步判定；观察期不阻断写入。');
  return 0;
}

process.exitCode = main();
