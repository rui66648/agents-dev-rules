#!/usr/bin/env node
/**
 * RULE-057 开发中进步闭环门禁（观察期 / WARN only，零依赖）
 * ==========================================================
 * 用法：
 *   node learning-loop-check.mjs --root <目录> [--check] [--json] [--strict]
 *   node learning-loop-check.mjs --selftest
 *
 * 观察期口径（2026-11-10）：只读、绝不写文件、退出码恒 0（参数错误 / 自证失败除外）。
 * 输出的是「缺口清单」，不是判定：命中后按 rules/dev-learning-loop.md §8 由人补全。
 *
 * 判据（刻意收窄，只防「完全没留痕」）：
 *   1. NOTES      —— docs/learning/ 是否存在且非空（L1+ 任务应有笔记）
 *   2. SECTIONS   —— 每份笔记的核心段是否齐全（学习目标 / 四个反问 / 半页笔记）
 *   3. HALF_PAGE  —— 半页笔记七项逐项存在性（RULE-057 §6.1）
 *   4. FOUR_Q     —— 四个反问逐项存在性（RULE-057 §1.2）
 *   5. DEBUG_5    —— 笔记自称含排错（含「根因」）时，五件事六项必须齐（RULE-057 §3.1）
 *
 * **不判**：理解深度、答案质量、是否真的脱稿讲透——这些无法门禁化。
 * 本脚本只能说「没写」，不能说「没学会」；把它当质量判据就是自造假绿。
 *
 * 分级（RULE-057 §9）：L0 不适用（脚本报 NOT_APPLICABLE 提示，不算缺口）。
 */
import {
  readdirSync, readFileSync, statSync, existsSync, mkdtempSync,
  mkdirSync, writeFileSync, rmSync,
} from 'node:fs';
import { join, resolve, relative } from 'node:path';
import { tmpdir } from 'node:os';

const LEARNING_DIR = 'docs/learning';
const NOTE_EXT = /\.md$/i;
const SKIP_FILE = /^(?:readme|index|template|_)|\.template\.md$/i;

const CORE_SECTIONS = [
  { key: '学习目标', pattern: /学习目标|本次要弄懂/ },
  { key: '四个反问', pattern: /四个反问|为什么这样设计/ },
  { key: '半页笔记', pattern: /半页笔记|本次解决的问题/ },
];

const FOUR_Q = [
  '为什么这样设计',
  '替代方案',
  '最容易在哪里出错',
  '十倍',
];

const HALF_PAGE = [
  '本次解决的问题',
  '我原来的理解',
  '实际验证后的结论',
  '最关键的一个原理',
  '踩过的坑及原因',
  '仍然不理解的问题',
  '下次可以复用',
];

const DEBUG_ITEMS = ['现象', '预期', '定位', '根因', '修复', '预防'];
const DEBUG_TRIGGER = /排错五件事|根因/;

const HELP = `RULE-057 learning-loop-check (OBSERVE / WARN only)
  --root <dir>   扫描根目录，默认 cwd
  --check        只读检查（观察期默认行为，与不传等价）
  --json         输出 JSON
  --strict       把缺口计入退出码（默认恒 0；供未来转正评估用，当前不挂 gate.sh）
  --selftest     临时目录构造正/负例自证，不触碰工作区
  -h, --help     显示本帮助
  只判存在性与段齐全率；不判理解质量。`;

function parseArgs(argv) {
  const a = { root: process.cwd(), check: false, json: false, strict: false, selftest: false, help: false };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v === '--root' && argv[i + 1]) a.root = resolve(argv[++i]);
    else if (v === '--check') a.check = true;
    else if (v === '--json') a.json = true;
    else if (v === '--strict') a.strict = true;
    else if (v === '--selftest') a.selftest = true;
    else if (v === '-h' || v === '--help') a.help = true;
  }
  return a;
}

function analyze(root) {
  const dir = join(root, LEARNING_DIR);
  if (!existsSync(dir) || !statSync(dir).isDirectory()) {
    return { root, dirExists: false, scanned: 0, notes: [], findings: [{ kind: 'NOTES', key: LEARNING_DIR, missing: ['目录不存在：L1+ 任务未留学习笔记'] }] };
  }
  const files = readdirSync(dir)
    .filter((f) => NOTE_EXT.test(f) && !SKIP_FILE.test(f))
    .sort();

  const notes = [];
  const findings = [];

  for (const name of files) {
    const rel = `${LEARNING_DIR}/${name}`;
    const text = readFileSync(join(dir, name), 'utf8');
    const missing = [];

    for (const s of CORE_SECTIONS) if (!s.pattern.test(text)) missing.push(`段:${s.key}`);
    for (const q of FOUR_Q) if (!text.includes(q)) missing.push(`反问:${q}`);
    for (const h of HALF_PAGE) if (!text.includes(h)) missing.push(`半页:${h}`);
    if (DEBUG_TRIGGER.test(text)) {
      for (const d of DEBUG_ITEMS) if (!text.includes(d)) missing.push(`排错:${d}`);
    }

    const total = CORE_SECTIONS.length + FOUR_Q.length + HALF_PAGE.length +
      (DEBUG_TRIGGER.test(text) ? DEBUG_ITEMS.length : 0);
    const done = total - missing.length;
    notes.push({ file: rel, total, done, completeness: total ? Math.round((done / total) * 100) : 0, missing });
    if (missing.length > 0) findings.push({ kind: 'SECTIONS', key: rel, missing });
  }

  if (files.length === 0) {
    findings.push({ kind: 'NOTES', key: LEARNING_DIR, missing: ['目录为空：L1+ 任务未留学习笔记'] });
  }

  return { root, dirExists: true, scanned: files.length, notes, findings };
}

function selftest() {
  const t = mkdtempSync(join(tmpdir(), 'learnloop-'));
  const passed = [];
  try {
    const put = (rel, text) => {
      const p = join(t, rel);
      mkdirSync(join(p, '..'), { recursive: true });
      writeFileSync(p, text, 'utf8');
    };
    const complete = [
      '## 学习目标', '本次要弄懂：SSE 断线恢复',
      '## 四个反问', '为什么这样设计', '有什么替代方案', '最容易在哪里出错', '扩大十倍',
      '## 半页笔记', '本次解决的问题', '我原来的理解', '实际验证后的结论', '最关键的一个原理',
      '踩过的坑及原因', '仍然不理解的问题', '下次可以复用',
      '## 排错五件事', '现象', '预期', '定位', '根因：代码', '修复', '预防',
    ].join('\n');

    put(`${LEARNING_DIR}/2026-11-10-complete.md`, complete);
    put(`${LEARNING_DIR}/2026-11-10-partial.md`, '## 学习目标\n本次要弄懂：只有目标\n');
    put(`${LEARNING_DIR}/2026-11-10-debug-missing.md`,
      complete.replace('- **预防**：增加测试\n', '').replace('预防', ''));
    put(`${LEARNING_DIR}/README.md`, '索引文件，应被跳过');
    put(`docs/reports/other.md`, '无关文件，不在 learning/ 下');

    const r = analyze(t);
    const byFile = new Map(r.notes.map((n) => [n.file, n]));
    const assert = (cond, msg) => {
      if (!cond) throw new Error(msg);
      passed.push(msg);
    };

    assert(r.scanned === 3, `只扫描到 3 份笔记（README 与 learning/ 外文件被排除），实际 ${r.scanned}`);
    assert(byFile.get(`${LEARNING_DIR}/2026-11-10-complete.md`).missing.length === 0, '完整笔记无缺口');
    assert(byFile.get(`${LEARNING_DIR}/2026-11-10-complete.md`).completeness === 100, '完整笔记齐全率 100');
    const partial = byFile.get(`${LEARNING_DIR}/2026-11-10-partial.md`);
    assert(partial.missing.length > 0, '残缺笔记被报出缺口');
    assert(partial.missing.some((m) => m.startsWith('半页:')), '残缺笔记缺半页项被点名');
    const dbg = byFile.get(`${LEARNING_DIR}/2026-11-10-debug-missing.md`);
    assert(dbg.missing.some((m) => m === '排错:预防'), '自称含排错但缺「预防」被抓出');
    assert(!JSON.stringify(r).includes('other.md'), 'learning/ 之外的文件未被计入');

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
    console.error(`[learnloop] root 不存在或不是目录: ${a.root}`);
    return 2;
  }
  const r = analyze(a.root);
  const gaps = r.findings.length;

  if (a.json) {
    console.log(JSON.stringify({ ...r, mode: 'OBSERVE_WARN_ONLY', gaps }, null, 2));
    return a.strict && gaps > 0 ? 1 : 0;
  }

  console.log(`[learnloop] root=${r.root}`);
  console.log(`[learnloop] ${LEARNING_DIR} 存在=${r.dirExists} 笔记数=${r.scanned} 缺口=${gaps} mode=OBSERVE(WARN only)`);
  for (const n of r.notes) {
    const flag = n.missing.length === 0 ? 'OK  ' : 'WARN';
    console.log(`  [${flag}] ${n.file} 齐全率=${n.completeness}%`);
    if (n.missing.length) console.log(`        缺：${n.missing.join('、')}`);
  }
  for (const f of r.findings.filter((x) => x.kind === 'NOTES')) {
    console.log(`  [WARN] ${f.key} — ${f.missing.join('；')}`);
  }
  console.log('[learnloop] 观察期不阻断；判据仅「存在性 + 段齐全率」，不代表理解质量（RULE-057 §8 人工判）。');
  return a.strict && gaps > 0 ? 1 : 0;
}

process.exitCode = main();
