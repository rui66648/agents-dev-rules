#!/usr/bin/env node
/**
 * RULE-055 规范驱动开发门禁（canonical 实现，零依赖）
 * ============================================================================
 * 判据（RULE-055 §1/§3/§5）：
 *   ① 澄清门禁：spec 内遗留 [NEEDS CLARIFICATION] > 0 或超 3 个标记 → FAIL
 *   ② 结构完整：Intent / Scope / User Stories / Acceptance / Functional Reqs 必填段缺失 → FAIL
 *   ③ 体量纪律：行数 > 200，或含代码块（HOW 泄漏硬判）→ FAIL；
 *      出现文件路径/技术选型词（软泄漏）→ WARN
 *   ④ 规格—代码绑定（漂移）：spec 的 spec_version 落后于代码侧记录的 spec 版本 → FAIL
 *   ⑤ FR 覆盖：tasks 中无任何 FR 被引用 → FAIL（spec 与施工脱节）
 *   ⑥ 无 spec 目录的仓：L0/L1 正常态 → WARN，不 FAIL（不制造假红）
 *
 * 用法：
 *   node spec-clarity-gate.mjs --root <仓根> [--json] [--check] [--trigger manual|hook]
 *   node spec-clarity-gate.mjs --selftest      # 正负双向自证（先证明门禁可信）
 *   node spec-clarity-gate.mjs --spec <文件>   # 只判单份 spec（轻量，pre-commit 用）
 *
 * 落盘纪律：默认只读（DRY-RUN），绝不改文件。
 * 运行记录：每次实际运行追加一条 logs/gate-runs/<YYYYMM>.jsonl（schema 见 scripts/gate_runs.py），
 *           记录写失败 → 本次运行按 FAIL 处理并退出 1（与 root-cleanliness 同一纪律）。
 *
 * 判定表只在本文件维护；各仓不放第二份实现（RULE-053 §3 同口径）。
 */
import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { recordGateRun, utcNow } from './lib/gate-run-log.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));

const MAX_SPEC_LINES = 200;
const MAX_CLARIFICATIONS = 3;
const REQUIRED_SECTIONS = ['Intent', 'Scope', 'User Stories', 'Acceptance', 'Functional Reqs', 'Clarifications'];

/** HOW 软泄漏信号：技术选型词与文件路径。命中 → WARN（不阻断，避免误报） */
const HOW_LEAK_RE = /\b(?:React|Vue|Angular|FastAPI|Django|Flask|Spring|Express|PostgreSQL|MySQL|Redis|MongoDB|SQLite|Docker|Kubernetes|Alembic|Prisma|Tailwind|Vite|Webpack)\b|(?:^|[\s`(])(?:src|app|lib|tests?|components|routes|services|models)\/[\w.-]+\/[\w.-]+/m;
/** 兼容 CRLF：Windows 仓（尤其 PowerShell / pre-commit 写入）的 spec 几乎必然 \r\n */
const SPEC_FRONT_RE = /^---[ \t]*\r?\n([\s\S]*?)\r?\n---/;
const CLARIFY_RE = /\[NEEDS CLARIFICATION:[^\]]*\]/gi;
const FR_RE = /\bFR-\d{3}\b/g;
const FR_DEF_RE = /^\|?\s*(?:\*\*)?FR-(\d{3})(?:\*\*)?\s*\|/im;
const FENCE_RE = /^\s*```/;
/** 只禁编程语言代码块（HOW 泄漏）；`text` / `gherkin` / 空围栏是验收场景的合法格式 */
const LANG_FENCE_RE = /^\s*```[ \t]*(?!text\b|gherkin\b|gwt\b|ears\b|$)([a-z][\w+#.-]*)/im;
/** 段标题：兼容 CRLF、行尾空格。前瞻必须同时接受「下一个 ## 段」「下一个 # 一级标题」
 *  与「文件结束」三种边界——否则 frontmatter 后紧跟一级标题时，非贪婪匹配会在
 *  第一个 `$`（无 m 标志时只匹配文末）处提前收尾，把整段判成空。 */
const SECTION_TITLE = (title) => new RegExp(`^##[ \\t]*${title}[^\\n]*\\r?\\n([\\s\\S]*?)(?=^##[ \\t]|^#[ \\t]|\\s*$)`, 'm');

function argValue(args, name) {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : undefined;
}

function parseFront(text) {
  const m = SPEC_FRONT_RE.exec(text);
  const out = {};
  if (!m) return out;
  for (const line of m[1].split(/\r?\n/)) {
    const kv = /^([a-z_]+):\s*(.*)$/.exec(line.trim());
    if (kv) out[kv[1]] = kv[2].trim().replace(/^["']|["']$/g, '');
  }
  return out;
}

/**
 * 段正文：按行扫描，取「## <title>」行之后到下一个 ## 或 # 标题行（或文末）之间的内容。
 * 不用单个正则 + 非贪婪匹配：那套在「frontmatter 后紧跟一级标题」「`### in` 三级标题」
 * 两种真实形态下都会误判（前者整段吞空，后者把三级标题前缀当成段边界提前截断）。
 * @returns {string | undefined} undefined = 该段不存在
 */
function sectionBody(text, title) {
  const lines = text.split('\n');
  let start = -1;
  for (let i = 0; i < lines.length; i++) {
    const m = /^##[ \t]*(.+?)[ \t]*\r?$/.exec(lines[i]);
    if (m && m[1].trim() === title) { start = i + 1; break; }
  }
  if (start < 0) return undefined;
  const body = [];
  for (let i = start; i < lines.length; i++) {
    if (/^#{1,2}[ \t]+\S/.test(lines[i])) break; // 下一个 ## 段或 # 一级标题
    body.push(lines[i]);
  }
  return body.join('\n').trim();
}

/** 单份 spec 的结构 / 澄清 / 体量判定；tasks 传入时兼判 FR 覆盖 */
function checkSpec(specPath, tasksPath) {
  const v = [];
  const w = [];
  const text = readFileSync(specPath, 'utf8');
  const rel = specPath.split(/[\\/]/).slice(-3).join('/');
  const fm = parseFront(text);

  // ② 结构完整：段存在且非空（"空"= 去掉空行/表头分隔行后无实质内容行）
  const hasContent = (sec) => {
    const body = sectionBody(text, sec);
    if (body === undefined) return undefined;
    const substantive = body.split('\n').filter((l) => {
      const t = l.trim();
      if (!t) return false;
      if (/^\|?[\s|:-]*-{2,}[\s|:-]*\|?$/.test(t)) return false; // 表头分隔行 |---|---|
      if (/^(?:[-*+]\s*|>\s*)$/.test(t)) return false;           // 空列表项 / 空引用
      return true;
    });
    return substantive.length;
  };
  for (const sec of REQUIRED_SECTIONS) {
    if (sectionBody(text, sec) === undefined) v.push({ name: rel, kind: 'missing-section', dest: `缺「## ${sec}」段（模板 templates/spec/spec-template.md）` });
    else if (sec !== 'Clarifications' && !hasContent(sec)) v.push({ name: rel, kind: 'empty-section', dest: `「## ${sec}」无实质内容（Clarifications 允许空——表示无遗留分歧）` });
  }

  // ① 澄清门禁
  //    判「遗留」的唯一口径：**标记所在的那一行**是否同时满足
  //      (a) 位于 ## Clarifications 段内，且
  //      (b) 带解决标记（[x] / 已解决 / answered）。
  //    只看"字符串在 Clarifications 段里出现过"会漏判——标记追加在段尾、或写进
  //    表格外的说明行时，段内确实能找到该字符串，但它并未被收编。
  const clar = text.match(CLARIFY_RE) || [];
  // 收编的正确定义：标记出现在 ## Clarifications 的**表格行内**（行以 | 开头），
  // 且该行带解决标记（[x] / 已解决 / answered）。
  // 不能只判"标记是否在 Clarifications 段内"——Clarifications 常是最后一段，
  // 随手追加在段尾的独立标记行也会被算进段正文，从而把未收编的标记误判为已解决。
  // 也不能只判字符串出现过——表格外的说明行同样能找到该字符串。
  const clarRows = new Set(
    (sectionBody(text, 'Clarifications') || '').split('\n')
      .map((l) => l.replace(/\r$/, '').trim())
      .filter((l) => l.startsWith('|'))
  );
  const leftover = clar.filter((m) => {
    const idx = text.indexOf(m);
    const line = text.slice(idx, text.indexOf('\n', idx)).trim();
    const resolved = /\[x\]|已解决|answered|已回答/i.test(line);
    if (resolved) return false;          // 行内已标解决：不遗留
    return !clarRows.has(line);          // 未进 Clarifications 表格的才算遗留
  });
  if (leftover.length > 0) v.push({ name: rel, kind: 'leftover-clarification', dest: `遗留 ${leftover.length} 个 [NEEDS CLARIFICATION]：有分歧未问，不得进入 plan / coding` });
  if (clar.length > MAX_CLARIFICATIONS) v.push({ name: rel, kind: 'too-many-clarifications', dest: `标记 ${clar.length} 个 > 上限 ${MAX_CLARIFICATIONS}——先问最关键的，其余记 Open Questions` });

  // ③ 体量纪律
  const lines = text.split('\n').length;
  if (lines > MAX_SPEC_LINES) v.push({ name: rel, kind: 'spec-too-long', dest: `${lines} 行 > 上限 ${MAX_SPEC_LINES}——按 US 边界拆 spec，不是压缩` });
  const langFences = text.split('\n').filter((l) => LANG_FENCE_RE.test(l));
  if (langFences.length > 0) v.push({ name: rel, kind: 'code-block-in-spec', dest: `spec 含 ${langFences.length} 个编程语言代码块（${langFences[0].trim().replace(/\s+/g, ' ').slice(0, 24)}…）——HOW 属 plan.md（RULE-055 §1.2；text/gherkin 围栏的验收场景合法）` });
  const howLines = text.split('\n').filter((l) => HOW_LEAK_RE.test(l) && !/spec|plan|template|门禁|规则|RULE/.test(l));
  if (howLines.length > 0) w.push({ name: rel, kind: 'how-leak', dest: `疑似实现泄漏（技术选型/文件路径）：${howLines[0].trim().slice(0, 70)}` });

  // frontmatter 必备
  for (const k of ['spec_id', 'status', 'spec_version']) {
    if (!fm[k]) v.push({ name: rel, kind: 'missing-frontmatter', dest: `frontmatter 缺 ${k}` });
  }
  if (fm.status && !['draft', 'approved', 'superseded'].includes(fm.status)) {
    v.push({ name: rel, kind: 'bad-status', dest: 'status 只能是 draft / approved / superseded' });
  }
  if (fm.status === 'superseded' && !fm.supersedes) {
    v.push({ name: rel, kind: 'superseded-without-pointer', dest: 'superseded 必须写 supersedes: <新规格>' });
  }
  // ④ 漂移的前置：spec_version 必须形如 vN
  if (fm.spec_version && !/^v\d+$/.test(fm.spec_version)) {
    v.push({ name: rel, kind: 'bad-spec-version', dest: `spec_version 必须形如 v1 / v2（当前 ${fm.spec_version}）` });
  }

  // ⑤ FR 覆盖
  const frs = new Set((text.match(FR_RE) || []).map((s) => s.replace('FR-', '')));
  if (frs.size === 0) {
    v.push({ name: rel, kind: 'no-functional-reqs', dest: '没有编号功能需求（FR-001…）——spec 失去可逐条比对的施工依据' });
  } else if (existsSync(tasksPath)) {
    const ttxt = readFileSync(tasksPath, 'utf8');
    const covered = [...frs].filter((f) => ttxt.includes(`FR-${f}`));
    const missing = [...frs].filter((f) => !covered.includes(f));
    if (missing.length > 0) v.push({ name: rel, kind: 'fr-not-covered', dest: `tasks 未覆盖 FR：${missing.map((f) => `FR-${f}`).join(', ')}` });
  } else {
    w.push({ name: rel, kind: 'tasks-missing', dest: '同目录无 tasks.md——FR 覆盖无法核对（L0/L1 正常）' });
  }

  return { violations: v, warnings: w, lines, clarifications: clar.length, frs: frs.size };
}

/** ④ 漂移：从 git log 抽取代码侧记录的 spec 版本（spec:<slug>@v<N>） */
function codeSideSpecVersion(root, slug) {
  try {
    const { execFileSync } = require('node:child_process');
    const out = execFileSync('git', ['log', '--format=%s', '-n', '500'], { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    const re = new RegExp(`spec:${slug}@v(\\d+)`, 'g');
    let m;
    let max = 0;
    while ((m = re.exec(out))) max = Math.max(max, Number(m[1]));
    return max > 0 ? max : null;
  } catch {
    return null; // 非 git 仓或 git 不可用 → 不判漂移（不制造假红）
  }
}

export function check(root, opts = {}) {
  const v = [];
  const w = [];
  const taskRoot = join(root, 'docs', 'tasks');

  if (!existsSync(taskRoot)) {
    w.push({ name: 'docs/tasks/', kind: 'no-task-dir', dest: '仓内无 docs/tasks/——L0/L1 场景（无落盘 spec）正常，不判 FAIL' });
    return { root, violations: v, warnings: w, summary: { specs: 0, frs: 0 } };
  }

  const specs = [];
  const walk = (dir) => {
    for (const n of readdirSync(dir)) {
      const p = join(dir, n);
      if (statSync(p).isDirectory()) walk(p);
      else if (n === 'spec.md') specs.push(p);
    }
  };
  walk(taskRoot);

  if (specs.length === 0) {
    w.push({ name: 'docs/tasks/', kind: 'no-spec', dest: 'docs/tasks/ 下无 spec.md——L0/L1 场景正常' });
    return { root, violations: v, warnings: w, summary: { specs: 0, frs: 0 } };
  }

  let frs = 0;
  for (const sp of specs) {
    const res = checkSpec(sp, join(dirname(sp), 'tasks.md'));
    v.push(...res.violations);
    w.push(...res.warnings);
    frs += res.frs;

    // ④ 规格—代码绑定：spec_version 不得落后于 commit 里记录的版本
    const fm = parseFront(readFileSync(sp, 'utf8'));
    const slug = fm.spec_id || dirname(sp).split(/[\\/]/).pop();
    const codeVer = codeSideSpecVersion(root, slug);
    if (codeVer !== null && fm.spec_version && /^v\d+$/.test(fm.spec_version)) {
      const specVer = Number(fm.spec_version.replace('v', ''));
      if (specVer < codeVer) {
        v.push({ name: sp.split(/[\\/]/).slice(-3).join('/'), kind: 'spec-drift', dest: `代码侧已记录 ${slug}@v${codeVer}，spec 仍 v${specVer}——改代码未同步规格（RULE-055 §4）` });
      }
    }
  }

  return { root, violations: v, warnings: w, summary: { specs: specs.length, frs } };
}

// ── --selftest：正负双向都必须如预期，否则判定不可信 ─────────────────────
function writeSpec(dir, { body, front }) {
  const fm = front || { spec_id: 'demo', status: 'approved', spec_version: 'v1', created_at: '2026-11-07' };
  const fmText = Object.entries(fm).map(([k, val]) => `${k}: ${val}`).join('\n');
  const text = `---\n${fmText}\n---\n\n# demo\n\n${body}`;
  const { writeFileSync, mkdirSync } = require('node:fs');
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'spec.md'), text, 'utf8');
}

function selftest() {
  const { writeFileSync, mkdirSync, rmSync } = require('node:fs');
  const sandbox = join(tmpdir(), `spec-clarity-selftest-${Date.now()}`);
  const results = [];
  try {
    mkdirSync(sandbox, { recursive: true });
    git(sandbox, ['init', '-q', '.']);
    const good = `## Intent
一句话目标。
## Scope
### in
| 1 | a |
### out
| 1 | b |
## User Stories
### US-01 (P1)
作为 用户，我想要 拖拽，以便 管理。
## Acceptance
\`\`\`text
Given a
When b
Then c
\`\`\`
## Functional Reqs
| FR-001 | 系统 MUST x | P1 | US-01 |
## Clarifications
| 1 | 问题 | 答案 | 2026-11-07 |
`;
    writeSpec(join(sandbox, 'docs', 'tasks', '001-demo'), { body: good });
    writeFileSync(join(sandbox, 'docs', 'tasks', '001-demo', 'tasks.md'), '- T010 实现 FR-001', 'utf8');
    const clean = check(sandbox);
    results.push({ case: '合规 spec 应 PASS', ok: clean.violations.length === 0, detail: clean.violations.map((x) => `${x.name}:${x.kind}`).join(', ') || 'PASS' });

    // CRLF 兼容（Windows 仓常态）：同一份内容换成 \r\n 必须同样 PASS，不得假红
    writeSpec(join(sandbox, 'docs', 'tasks', '011-crlf'), { body: good });
    const crlfPath = join(sandbox, 'docs', 'tasks', '011-crlf', 'spec.md');
    writeFileSync(crlfPath, readFileSync(crlfPath, 'utf8').replace(/\n/g, '\r\n'), 'utf8');
    writeFileSync(join(sandbox, 'docs', 'tasks', '011-crlf', 'tasks.md'), '- T010 实现 FR-001', 'utf8');
    const crlf = check(sandbox);
    const crlfBad = crlf.violations.filter((x) => String(x.name).includes('011-crlf'));
    results.push({ case: 'CRLF 行尾的 spec 必须同样 PASS（Windows 仓常态）', ok: crlfBad.length === 0, detail: crlfBad.map((x) => x.kind).join(', ') || 'PASS' });

    // 负例 1：遗留澄清（单独 1 个，不触发超限） + 超 3 个标记
    writeSpec(join(sandbox, 'docs', 'tasks', '002-clar'), { body: good + '\n[NEEDS CLARIFICATION: q1]\n' });
    const r1 = check(sandbox);
    const k1 = new Set(r1.violations.filter((x) => String(x.name).includes('002-clar')).map((x) => x.kind));
    results.push({ case: '遗留澄清必须 FAIL', ok: k1.has('leftover-clarification'), detail: [...k1].join(' | ') || '未检出' });

    writeSpec(join(sandbox, 'docs', 'tasks', '002b-clar4'), { body: good + '\n[NEEDS CLARIFICATION: q1]\n[NEEDS CLARIFICATION: q2]\n[NEEDS CLARIFICATION: q3]\n[NEEDS CLARIFICATION: q4]\n' });
    const r1b = check(sandbox);
    const k1b = new Set(r1b.violations.filter((x) => String(x.name).includes('002b-clar4')).map((x) => x.kind));
    results.push({ case: '标记超 3 个必须 FAIL', ok: k1b.has('too-many-clarifications'), detail: [...k1b].join(' | ') || '未检出' });

    // 澄清已解决的不得算遗留：写进 Clarifications 段且标记已解决
    writeSpec(join(sandbox, 'docs', 'tasks', '002c-resolved'), {
      body: good + '\n## Clarifications\n\n| # | 问题 | 答案 | 日期 |\n|---|---|---|---|\n| 1 | 已解决的澄清 | 答案 | 2026-11-07 |\n',
    });
    const r1c = check(sandbox);
    const k1c = r1c.violations.filter((x) => String(x.name).includes('002c-resolved'));
    results.push({ case: '已记入 Clarifications 的澄清不得算遗留', ok: k1c.length === 0, detail: k1c.map((x) => x.kind).join(', ') || 'PASS' });

    // 负例 2：缺段 + 代码块
    writeSpec(join(sandbox, 'docs', 'tasks', '003-struct'), { body: '## Intent\nx\n' });
    const r2 = check(sandbox);
    const k2 = new Set(r2.violations.map((x) => `${x.name}:${x.kind}`));
    results.push({ case: '缺 Acceptance/FR 段必须 FAIL', ok: [...k2].some((k) => k.endsWith(':missing-section')), detail: [...k2].slice(0, 3).join(' | ') });

    writeSpec(join(sandbox, 'docs', 'tasks', '004-code'), { body: good + '\n\`\`\`python\nprint(1)\n\`\`\`\n' });
    results.push({ case: 'spec 内代码块必须 FAIL（HOW 属 plan）', ok: check(sandbox).violations.some((x) => x.kind === 'code-block-in-spec'), detail: 'code-block-in-spec' });

    // 负例 3：无 FR / FR 未被 tasks 覆盖
    writeSpec(join(sandbox, 'docs', 'tasks', '005-nofr'), { body: good.replace(/\| FR-001 \| 系统 MUST x \| P1 \| US-01 \|/, '| 无编号需求 |') });
    results.push({ case: '无编号功能需求必须 FAIL', ok: check(sandbox).violations.some((x) => x.kind === 'no-functional-reqs'), detail: 'no-functional-reqs' });

    writeSpec(join(sandbox, 'docs', 'tasks', '006-frcov'), { body: good.replace('FR-001', 'FR-009') });
    writeFileSync(join(sandbox, 'docs', 'tasks', '006-frcov', 'tasks.md'), '- T010 不引用任何 FR', 'utf8');
    results.push({ case: 'tasks 未覆盖 FR 必须 FAIL', ok: check(sandbox).violations.some((x) => x.kind === 'fr-not-covered'), detail: 'fr-not-covered' });

    // 负例 4：体量超限（>200 行）
    writeSpec(join(sandbox, 'docs', 'tasks', '007-long'), { body: good + '\n' + '填充行 x\n'.repeat(260) });
    results.push({ case: '超过 200 行必须 FAIL', ok: check(sandbox).violations.some((x) => x.kind === 'spec-too-long'), detail: 'spec-too-long' });

    // 负例 5：漂移——commit 记 v3 而 spec 仍 v1
    writeSpec(join(sandbox, 'docs', 'tasks', '008-drift'), { front: { spec_id: 'drifted', status: 'approved', spec_version: 'v1', created_at: '2026-11-07' }, body: good });
    writeFileSync(join(sandbox, 'readme.txt'), 'x', 'utf8');
    git(sandbox, ['add', '-A']);
    git(sandbox, ['-c', 'user.email=a@b.c', '-c', 'user.name=t', 'commit', '-q', '-m', 'feat: something spec:drifted@v3']);
    results.push({ case: 'spec_version 落后代码侧必须 FAIL（漂移）', ok: check(sandbox).violations.some((x) => x.kind === 'spec-drift'), detail: 'spec-drift' });

    // 负例 6：bad status / superseded 无指针
    writeSpec(join(sandbox, 'docs', 'tasks', '009-badstatus'), { front: { spec_id: 'bs', status: 'weird', spec_version: 'v1', created_at: '2026-11-07' }, body: good });
    results.push({ case: '非法 status 必须 FAIL', ok: check(sandbox).violations.some((x) => x.kind === 'bad-status'), detail: 'bad-status' });
    writeSpec(join(sandbox, 'docs', 'tasks', '010-sup'), { front: { spec_id: 'sup', status: 'superseded', spec_version: 'v2', created_at: '2026-11-07' }, body: good });
    results.push({ case: 'superseded 缺指针必须 FAIL', ok: check(sandbox).violations.some((x) => x.kind === 'superseded-without-pointer'), detail: 'superseded-without-pointer' });

    // 正例 2：完全无 docs/tasks 的仓 = L0/L1，只 WARN
    const bare = join(tmpdir(), `spec-clarity-bare-${Date.now()}`);
    mkdirSync(bare, { recursive: true });
    writeFileSync(join(bare, 'AGENTS.md'), '# x', 'utf8');
    const rb = check(bare);
    results.push({ case: '无 spec 目录只 WARN 不 FAIL（不制造假红）', ok: rb.violations.length === 0 && rb.warnings.length > 0, detail: `${rb.warnings.length} warnings / ${rb.violations.length} violations` });
    rmSync(bare, { recursive: true, force: true });
  } finally {
    rmSync(sandbox, { recursive: true, force: true });
  }

  const failed = results.filter((r) => !r.ok);
  for (const r of results) console.log(`[selftest] ${r.ok ? 'OK  ' : 'FAIL'} ${r.case} — ${r.detail}`);
  console.log(failed.length ? `[selftest] FAIL — 门禁本身有缺陷（${failed.length} 项）` : '[selftest] PASS — 正负双向自证通过');
  process.exit(failed.length ? 1 : 0);
}

function git(cwd, args) {
  const { execFileSync } = require('node:child_process');
  return execFileSync('git', args, { cwd, stdio: ['ignore', 'ignore', 'ignore'] });
}

function main() {
  const args = process.argv.slice(2);
  const root = resolve(argValue(args, '--root') || process.cwd());
  if (args.includes('--selftest')) selftest();

  const single = argValue(args, '--spec');
  const startedAt = utcNow();
  const trigger = String(argValue(args, '--trigger') || process.env.GATE_TRIGGER || 'manual').toLowerCase();
  if (!['scheduled', 'manual', 'hook'].includes(trigger)) {
    console.error('[gate-runs] 非法 trigger=' + trigger + '（允许 scheduled/manual/hook）；未记录，退出 2');
    process.exit(2);
  }

  let report;
  if (single) {
    const p = resolve(single);
    if (!existsSync(p)) { console.error(`[spec-gate] spec 文件不存在：${p}`); process.exit(2); }
    const res = checkSpec(p, join(dirname(p), 'tasks.md'));
    report = { root, violations: res.violations, warnings: res.warnings, summary: { specs: 1, frs: res.frs } };
  } else {
    report = check(root, { check: args.includes('--check') });
  }

  const exitCode = report.violations.length ? 1 : 0;
  if (args.includes('--json')) console.log(JSON.stringify(report, null, 2));
  else if (exitCode === 0) {
    console.log(`[spec-gate] PASS — ${report.summary.specs} 份 spec、${report.summary.frs} 条 FR；澄清清零、无漂移、FR 有覆盖（RULE-055）`);
    for (const x of report.warnings) console.log(`  [WARN] ${x.name}  [${x.kind}]  → ${x.dest}`);
  } else {
    console.log(`[spec-gate] FAIL — ${report.violations.length} 项违规（RULE-055）`);
    for (const x of report.violations) console.log(`  - ${x.name}  [${x.kind}]  → ${x.dest}`);
    for (const x of report.warnings) console.log(`  [WARN] ${x.name}  [${x.kind}]  → ${x.dest}`);
  }

  try {
    recordGateRun({
      gateId: 'spec-clarity-gate',
      mode: 'dry-run',
      trigger,
      result: exitCode ? 'FAIL' : 'PASS',
      ruleIds: ['RULE-055', 'RULE-056'],
      evidence: {
        checker: 'hooks/scripts/spec-clarity-gate.mjs',
        specs: report.summary.specs,
        frs: report.summary.frs,
        violations: report.violations.length,
        warnings: report.warnings.length,
        sample: report.violations.slice(0, 5).map((x) => `${x.name}:${x.kind}`),
      },
      startedAt,
      exitCode,
    });
  } catch (e) {
    console.error(`[gate-runs] 记录写入失败：${e.message} → 本次运行按 FAIL 处理`);
    process.exit(1);
  }
  process.exit(exitCode);
}

// selftest 在 main 前定义但需要 node:child_process 的惰性 require（ESM 下用 createRequire）
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);

if (process.argv[1] && process.argv[1].endsWith('spec-clarity-gate.mjs')) main();
