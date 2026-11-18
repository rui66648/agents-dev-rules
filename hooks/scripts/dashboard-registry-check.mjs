#!/usr/bin/env node
/**
 * RULE-054 项目图形资产门禁（canonical 实现，零依赖）
 * ============================================================================
 * 唯一原则：一图一决策；**只更新不重生成** —— 同一槽位出现第二份文件即 FAIL。
 *
 * 用法：
 *   node hooks/scripts/dashboard-registry-check.mjs --root <仓根> [--json] [--check]
 *   ... --emit-registry   从各图 frontmatter 派生 docs/dashboards/registry.json
 *   ... --check           与已提交的 registry.json 对账（漂移即 FAIL）
 *   ... --init            从共享根 templates/dashboards/ 铺骨架；任何槽位已存在则整体拒绝
 *   ... --selftest        正负双向自证（先证明门禁可信，再谈合规）
 *
 * 判定表只在本文件维护；各项目只放 tools/dashboard-check.mjs 启动器转发到这里
 * （与 RULE-053 的 root-cleanliness-check 同一形态，不留第二份实现）。
 */
import { readFileSync, writeFileSync, existsSync, readdirSync, mkdirSync, copyFileSync, statSync, rmSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';

const HERE = dirname(fileURLToPath(import.meta.url));

/** 十个固定槽位：id + slug 一经定版不许改（改名即造重复图） */
const SLOTS = [
  { id: '00', slug: 'cockpit', cadence: 'weekly', strictStale: true },
  { id: '01', slug: 'scope-wbs', cadence: 'change' },
  { id: '02', slug: 'milestone-critical-path', cadence: 'weekly' },
  { id: '03', slug: 'flow-board-cfd', cadence: 'weekly' },
  { id: '04', slug: 'resource-load-heat', cadence: 'weekly' },
  { id: '05', slug: 'evm-s-curve', cadence: 'monthly' },
  { id: '06', slug: 'risk-issue-matrix', cadence: 'weekly', terms: ['责任人', '截止'] },
  { id: '07', slug: 'architecture-dependency', cadence: 'quarterly' },
  { id: '08', slug: 'code-health', cadence: 'weekly', terms: ['PR', '覆盖率', '评审', '分支'] },
  { id: '09', slug: 'env-release-dora-slo', cadence: 'weekly', strictStale: true, terms: ['部署频率', '失败率', '恢复', 'SLO'] },
];
const SECTIONS = ['决策', '读数', '图', '变化', '取数'];
const SLOT_IDS = new Set(SLOTS.map((s) => s.id));
const ALWAYS_OK_FILES = new Set(['README.md', 'thresholds.md', 'registry.json', 'sources.json']);
const SLOT_MD_RE = /^(\d{2})-([a-z0-9][a-z0-9-]*)\.md$/;
const RENDER_RE = /^(\d{2})-([a-z0-9][a-z0-9-]*)\.render\.html$/;
/** 重复图的典型命名形态（历史坑：每次汇报另存一张） */
const DUP_RE = /20\d{2}[-_.]?\d{2}([-_.]?\d{2})?|-v\d+|final|copy|backup|副本|备份|[-_]old[-_.]|旧/i;
const LIGHT_RE = /🟢|🟡|🔴|\b(green|amber|red)\b|(?<=[|>》\s|])[绿黄红](?=[\s|。]|$)/i;
/** 空置天数上限（≈2× 节奏）；change/release 型按变更驱动，不判空置 */
const STALE_DAYS = { daily: 3, weekly: 14, monthly: 70, quarterly: 200 };
const STATUSES = new Set(['active', 'deferred', 'not_applicable']);

const fileName = (s) => `${s.id}-${s.slug}.md`;

function argValue(args, name) {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : undefined;
}

/** 只取 frontmatter 的扁平键（零依赖，不引 YAML 解析器） */
function parseFront(text) {
  const m = /^---\s*\n([\s\S]*?)\n---/.exec(text);
  const out = {};
  if (!m) return out;
  for (const line of m[1].split('\n')) {
    const kv = /^([a-z_]+):\s*(.*)$/.exec(line.trim());
    if (kv) out[kv[1]] = kv[2].trim().replace(/^["']|["']$/g, '');
  }
  return out;
}

function sectionBody(text, title) {
  const re = new RegExp(`^##\\s*${title}[\\s\\S]*?(?=^##\\s|(?![\\s\\S]))`, 'm');
  const m = re.exec(text);
  if (!m) return undefined;
  return m[0].replace(new RegExp(`^##\\s*${title}\\s*`), '').trim();
}

function daysSince(dateStr, now) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return Infinity;
  return Math.floor((now - d.getTime()) / 86400000);
}

/** thresholds.md 的指标列 = 图里允许出现的颜色依据白名单 */
function thresholdMetrics(dir) {
  const p = join(dir, 'thresholds.md');
  if (!existsSync(p)) return null;
  const names = [];
  for (const line of readFileSync(p, 'utf8').split('\n')) {
    const cells = line.split('|').map((c) => c.trim());
    if (cells.length < 7) continue;
    const name = cells[1];
    if (!name || /^:?-{2,}:?$/.test(name) || /^(指标|metric)$/i.test(name)) continue;
    names.push(name.replace(/[*`]/g, ''));
  }
  return names;
}

function slotMetaFrom(dir, s) {
  const p = join(dir, fileName(s));
  if (!existsSync(p)) return null;
  const fm = parseFront(readFileSync(p, 'utf8'));
  return {
    slot: s.id, slug: s.slug, file: fileName(s),
    title: fm.title || '', decision: fm.decision || '', cadence: fm.cadence || s.cadence,
    owner: fm.owner || '', status: fm.status || 'active',
    last_updated: fm.last_updated || '', revisit: fm.revisit || '',
  };
}

const deriveRegistry = (metas, hasThresholds) => ({
  schema: 1,
  generator: 'hooks/scripts/dashboard-registry-check.mjs --emit-registry',
  thresholds: hasThresholds ? 'thresholds.md' : null,
  slots: SLOTS.map((s) => metas.find((m) => m && m.slot === s.id)).filter(Boolean),
});

export function check(root, opts = {}) {
  const now = Date.now();
  const dir = join(root, 'docs', 'dashboards');
  const v = [];
  const w = [];

  if (!existsSync(dir)) {
    v.push({ name: 'docs/dashboards/', kind: 'missing-dir', dest: 'node <共享根>/hooks/scripts/dashboard-registry-check.mjs --root <仓根> --init（一次性铺骨架，之后只更新）' });
    return { root, violations: v, warnings: w, summary: { slots: 0, active: 0 } };
  }

  // ── §2 只更新不重生成：一个槽位只准一份源文件 ──────────────────────────
  const canonical = new Map();   // 槽位 -> 与 SLOTS 同名的那份
  for (const f of readdirSync(dir).filter((n) => statSync(join(dir, n)).isFile())) {
    if (ALWAYS_OK_FILES.has(f)) continue;
    const md = SLOT_MD_RE.exec(f);
    const rd = RENDER_RE.exec(f);
    if (!md && !rd) {
      v.push({ name: f, kind: DUP_RE.test(f) ? 'duplicate-artifact' : 'undeclared-artifact', dest: DUP_RE.test(f) ? '就地更新对应槽位文件，历史交给 git（RULE-054 §2）' : '删除，或归入槽位文件；派生清单由 --emit-registry 生成' });
      continue;
    }
    const id = (md || rd)[1];
    const slug = (md || rd)[2];
    if (!SLOT_IDS.has(id)) { v.push({ name: f, kind: 'unknown-slot', dest: '槽位固定 00–09，不得自造' }); continue; }
    const slot = SLOTS.find((s) => s.id === id);
    if (slug !== slot.slug) {
      v.push({ name: f, kind: 'duplicate-artifact', dest: `与 ${fileName(slot)} 同槽位（${slot.slug}）的另存件——合并读数后删除本文件` });
      continue;
    }
    const seen = canonical.get(id) || [];
    seen.push(f);
    canonical.set(id, seen);
  }
  for (const [id, list] of canonical) {
    const mds = list.filter((f) => f.endsWith('.md'));
    const htmls = list.filter((f) => f.endsWith('.html'));
    if (mds.length > 1) v.push({ name: mds.join(' / '), kind: 'duplicate-slot', dest: '同一槽位出现多份同名文件（大小写或目录差异）——只保留一份' });
    if (htmls.length > 1) v.push({ name: htmls.join(' / '), kind: 'duplicate-render', dest: '每槽位只允许唯一一份 <id>-<slug>.render.html，且不得反向成为真源' });
  }

  // ── 阈值表：红黄绿唯一来源 ─────────────────────────────────────────────
  const metrics = thresholdMetrics(dir);
  if (metrics === null) v.push({ name: 'thresholds.md', kind: 'missing-thresholds', dest: '建 指标|口径|数据源|绿|黄|红|责任人 表；图里的灯必须由它推导' });
  else if (metrics.length === 0) v.push({ name: 'thresholds.md', kind: 'empty-thresholds', dest: '阈值表没有数据行，红黄绿无从推导' });

  // ── 逐槽位：文件恒在、五段骨架、口径可追、不许半成品冒充 ────────────────
  const metas = [];
  for (const s of SLOTS) {
    const fname = fileName(s);
    const path = join(dir, fname);
    if (!existsSync(path)) {
      v.push({ name: fname, kind: 'missing-slot', dest: '十槽恒在；未开工用 status: deferred + reason + revisit 声明，不许让槽位消失' });
      continue;
    }
    const text = readFileSync(path, 'utf8');
    const meta = slotMetaFrom(dir, s);
    metas.push(meta);
    const status = meta.status;

    if (status !== 'active' && !STATUSES.has(status)) v.push({ name: fname, kind: 'bad-status', dest: 'status 只能是 active / deferred / not_applicable' });
    if (status !== 'active' && !String(parseFront(text).reason || '').trim()) v.push({ name: fname, kind: 'status-without-reason', dest: 'deferred / not_applicable 必须写 reason' });
    if (status === 'deferred' && !meta.revisit) v.push({ name: fname, kind: 'deferred-without-revisit', dest: 'deferred 必须写复评日期，否则永久失踪' });

    for (const sec of SECTIONS) {
      const body = sectionBody(text, sec);
      if (body === undefined) { v.push({ name: fname, kind: 'missing-section', dest: `缺「## ${sec}」段（五段骨架见 RULE-054 §3）` }); continue; }
      if (sec === '决策' && !body) v.push({ name: fname, kind: 'empty-decision', dest: '一图一决策：不回答任何决策动作的图不该存在' });
    }

    if (status === 'active') {
      if (metrics && metrics.length) {
        const bad = (sectionBody(text, '读数') || '').split('\n').find((line) => LIGHT_RE.test(line) && !metrics.some((m) => line.toLowerCase().includes(m.toLowerCase())));
        if (bad) v.push({ name: fname, kind: 'light-without-metric', dest: `灯必须由 thresholds.md 的指标名推导：「${bad.trim().slice(0, 70)}」` });
      }
      for (const t of s.terms || []) if (!text.includes(t)) v.push({ name: fname, kind: 'missing-required-term', dest: `本图必须覆盖「${t}」（RULE-054 §7 常见坑对照）` });
      const lu = meta.last_updated || (/last_updated:\s*([\d-]+)/.exec(text) || [])[1] || '';
      if (!lu) v.push({ name: fname, kind: 'no-last-updated', dest: '取数段必须写 `- last_updated: YYYY-MM-DD`，否则读数不可信' });
      else {
        const limit = STALE_DAYS[meta.cadence];
        const age = daysSince(lu, now);
        if (limit && age > limit) {
          const item = { name: fname, kind: 'stale-beyond-cadence', dest: `节奏 ${meta.cadence}（阈值 ${limit} 天），已 ${age} 天未更` };
          if (s.strictStale) v.push(item); else w.push(item);
        }
      }
    } else {
      const body = sectionBody(text, '读数') || '';
      if (body && !/^[（(]/.test(body)) v.push({ name: fname, kind: 'inactive-slot-with-readings', dest: `status=${status} 却填了读数——要么转 active 补口径，要么清空` });
    }
  }

  // ── 统一 ID 贯穿抽查：00 的里程碑必须能在 02 解引用 ─────────────────────
  const cockpitPath = join(dir, fileName(SLOTS[0]));
  const ganttPath = join(dir, fileName(SLOTS[2]));
  if (existsSync(cockpitPath) && existsSync(ganttPath)) {
    const gtxt = readFileSync(ganttPath, 'utf8');
    for (const id of new Set(readFileSync(cockpitPath, 'utf8').match(/M\d+/g) || [])) {
      if (!gtxt.includes(id)) w.push({ name: fileName(SLOTS[0]), kind: 'id-not-resolvable', dest: `${id} 在 02 里程碑图里解引用不到（统一 ID 断链）` });
    }
  }

  // ── registry 必须派生 + 与磁盘对账 ────────────────────────────────────
  const regPath = join(dir, 'registry.json');
  const derived = deriveRegistry(metas, metrics !== null);
  if (existsSync(regPath)) {
    let committed = null;
    try { committed = JSON.parse(readFileSync(regPath, 'utf8')); } catch (e) { v.push({ name: 'registry.json', kind: 'broken-registry', dest: String(e.message) }); }
    if (committed) {
      for (const a of derived.slots) {
        const b = (committed.slots || []).find((x) => x.slot === a.slot);
        if (!b) v.push({ name: a.file, kind: 'registry-missing-entry', dest: '跑 --emit-registry 重新派生（清单不许手写）' });
        else if (JSON.stringify(b) !== JSON.stringify(a)) v.push({ name: a.file, kind: 'registry-drift', dest: 'frontmatter 与 registry.json 不一致，跑 --emit-registry' });
      }
      for (const b of committed.slots || []) if (!derived.slots.some((a) => a.slot === b.slot)) v.push({ name: b.file || `槽位 ${b.slot}`, kind: 'stale-registry-entry', dest: '清单里有而磁盘已不存在的僵尸条目' });
    }
  } else if (opts.check) {
    v.push({ name: 'registry.json', kind: 'missing-registry', dest: '跑 --emit-registry 生成（RULE-053 §3 同纪律：清单必须派生）' });
  }

  return { root, violations: v, warnings: w, summary: { slots: metas.length, active: metas.filter((m) => m.status === 'active').length } };
}

function emitRegistry(root) {
  const dir = join(root, 'docs', 'dashboards');
  const metas = SLOTS.map((s) => slotMetaFrom(dir, s)).filter(Boolean);
  const out = join(dir, 'registry.json');
  writeFileSync(out, JSON.stringify(deriveRegistry(metas, existsSync(join(dir, 'thresholds.md'))), null, 2) + '\n', 'utf8');
  console.log(`[dashboards] registry.json 已派生：${metas.length}/10 槽位（内容只由图文件 frontmatter 决定，不含时间戳，可 --check 对账）`);
}

function initFromTemplates(root) {
  const tplDir = join(HERE, '..', '..', 'templates', 'dashboards');
  if (!existsSync(tplDir)) { console.error(`[dashboards] 模板目录不存在：${tplDir}`); process.exit(1); }
  const dir = join(root, 'docs', 'dashboards');
  const present = SLOTS.map(fileName).filter((f) => existsSync(join(dir, f)));
  if (present.length) {
    // 「只更新不重生成」同样约束采用动作：绝不覆盖在用的图
    console.error(`[dashboards] 拒绝 --init：以下槽位已存在 → ${present.join(', ')}`);
    console.error('             缺哪槽就从共享根 templates/dashboards/ 手工复制哪一份单文件，不要整目录覆盖。');
    process.exit(1);
  }
  mkdirSync(dir, { recursive: true });
  let copied = 0;
  for (const name of readdirSync(tplDir)) {
    if (existsSync(join(dir, name))) continue;
    copyFileSync(join(tplDir, name), join(dir, name));
    copied++;
  }
  emitRegistry(root);
  console.log(`[dashboards] 已铺 ${copied} 个文件到 docs/dashboards/（十槽齐备，全部 deferred 起步；开工一张转 active 一张）`);
}

// ── --selftest：正负双向都必须如预期，否则判定不可信 ─────────────────────
function writeCleanSet(d, today) {
  writeFileSync(join(d, 'thresholds.md'), ['# 阈值表', '', '| 指标 | 口径 | 数据源 | 绿 | 黄 | 红 | 责任人 |', '|---|---|---|---|---|---|---|', '| SPI | EV/PV | 挣值台账 | ≥0.95 | 0.90–0.95 | <0.90 | PM |', '| 发布失败率 | 失败/总 | 发布看板 | <5% | 5–10% | >10% | 运维 |', ''].join('\n'), 'utf8');
  for (const s of SLOTS) {
    const terms = (s.terms || []).join(' / ');
    const rows = ['| 指标 | 值 | 灯 |', '|---|---|---|', '| SPI | 0.97 | 🟢 |', '| 发布失败率 | 2% | 🟢 |'];
    if (s.id === '06') rows[0] = '| ID | 风险 | 概率 | 影响 | 责任人 | 截止 | 灯 |';
    writeFileSync(join(d, fileName(s)), [
      '---', `slot: ${s.id}`, `slug: ${s.slug}`, `title: ${s.slug}`, 'decision: 继续 / 加人 / 收缩 / 暂停', `cadence: ${s.cadence}`, 'owner: PM', `status: active`, `last_updated: ${today}`, '---', '',
      `# ${s.slug}`, '', '## 决策', 'SPI 落到黄档即收缩范围；M01 为对外承诺里程碑。', '', '## 读数', ...rows, '', '## 图', '（表格即图）', '', `## 变化`, `- 首次铺图${terms ? `（必含项：${terms}）` : ''}`, '', '## 取数', `- last_updated: ${today}`, '',
    ].join('\n'), 'utf8');
  }
}

function selftest() {
  const sandbox = join(tmpdir(), `dashboards-selftest-${Date.now()}`);
  const d = join(sandbox, 'docs', 'dashboards');
  const results = [];
  const today = new Date().toISOString().slice(0, 10);
  try {
    mkdirSync(d, { recursive: true });
    writeCleanSet(d, today);
    const clean = check(sandbox);
    results.push({ case: '十槽齐备 + 灯有指标名 + M01 可解引用 应 PASS', ok: clean.violations.length === 0, detail: clean.violations.map((x) => `${x.name}:${x.kind}`).join(', ') || 'PASS' });

    // 负例：另存图 / 未声明件 / 空决策 / 无指标名的灯 / 超期 / 缺段 / 风险图缺责任人截止
    writeFileSync(join(d, '02-milestone-critical-path-2026-10-15.md'), '# 另存一份\n', 'utf8');
    writeFileSync(join(d, '03-flow-board-cfd-v2.md'), '# 又一份\n', 'utf8');
    writeFileSync(join(d, 'random-snapshot.png'), 'x', 'utf8');
    writeFileSync(join(d, '10-my-own-slot.md'), '# 自造槽位\n', 'utf8');
    writeFileSync(join(d, '05-evm-s-curve.md'), ['---', 'slot: 05', 'slug: evm-s-curve', 'title: EVM', 'decision: x', 'cadence: monthly', 'owner: PM', 'status: active', 'last_updated: 2020-01-01', '---', '', '# EVM', '', '## 决策', '', '## 读数', '| 值 | 灯 |', '|---|---|', '| 0.5 | 🔴 |', ''].join('\n'), 'utf8');
    writeFileSync(join(d, '06-risk-issue-matrix.md'), ['---', 'slot: 06', 'slug: risk-issue-matrix', 'title: 风险', 'decision: 关闭 / 升级', 'cadence: weekly', 'owner: QA', 'status: active', `last_updated: ${today}`, '---', '', '# 风险', '', '## 决策', 'R01 超截止即升级。', '', '## 读数', '| ID | 风险 |', '|---|---|', '| R01 | a |', '', '## 图', 'x', '', '## 变化', 'x', '', '## 取数', `x`, ''].join('\n'), 'utf8');
    writeFileSync(join(d, '09-env-release-dora-slo.md'), ['---', 'slot: 09', 'slug: env-release-dora-slo', 'title: 发布', 'decision: 放行 / 回滚', 'cadence: weekly', 'owner: 运维', 'status: active', 'last_updated: 2020-01-01', '---', '', '# 发布', '', '## 决策', '失败率红档冻结发布窗口。', '', '## 读数', '| SPI | 0.97 | 🟢 |', '', '## 图', 'x', '', '## 变化', 'x', '', '## 取数', 'x', ''].join('\n'), 'utf8');

    const dirty = check(sandbox);
    const kinds = new Set(dirty.violations.map((x) => `${x.name}:${x.kind}`));
    const expect = [
      '02-milestone-critical-path-2026-10-15.md:duplicate-artifact',
      '03-flow-board-cfd-v2.md:duplicate-artifact',
      'random-snapshot.png:undeclared-artifact',
      '10-my-own-slot.md:unknown-slot',
      '05-evm-s-curve.md:empty-decision',
      '05-evm-s-curve.md:missing-section',
      '05-evm-s-curve.md:light-without-metric',
      '06-risk-issue-matrix.md:missing-required-term',
      '09-env-release-dora-slo.md:stale-beyond-cadence',
      '09-env-release-dora-slo.md:missing-required-term',
    ];
    results.push({ case: '重复图 / 未声明件 / 自造槽位 / 空决策 / 缺段 / 无指标名的灯 / 必含项缺失 / 00·09 超期 全部 FAIL', ok: expect.every((e) => kinds.has(e)), detail: expect.filter((e) => !kinds.has(e)).join(' | ') || '全中' });
    results.push({ case: '普通槽位超期应是 WARN 而不是 FAIL（分档正确）', ok: dirty.warnings.some((x) => x.kind === 'stale-beyond-cadence' && x.name === '03-flow-board-cfd.md') === false && dirty.warnings.every((x) => x.kind !== 'stale-beyond-cadence' || !x.name.startsWith('09')), detail: dirty.warnings.map((x) => `${x.name}:${x.kind}`).join(', ') || '无同类告警' });

    rmSync(join(d, '04-resource-load-heat.md'));
    results.push({ case: '槽位文件消失应被抓（槽位不许消失）', ok: check(sandbox).violations.some((x) => x.kind === 'missing-slot' && x.name === '04-resource-load-heat.md'), detail: 'missing-slot' });

    writeFileSync(join(d, 'registry.json'), JSON.stringify({ schema: 1, slots: [{ slot: '99', file: 'ghost.md' }] }, null, 2), 'utf8');
    results.push({ case: '僵尸清单条目与派生漂移应被抓', ok: check(sandbox).violations.some((x) => x.kind === 'stale-registry-entry'), detail: 'stale-registry-entry' });
  } finally {
    rmSync(sandbox, { recursive: true, force: true });
  }
  const failed = results.filter((r) => !r.ok);
  for (const r of results) console.log(`[selftest] ${r.ok ? 'OK  ' : 'FAIL'} ${r.case} — ${r.detail}`);
  console.log(failed.length ? `[selftest] FAIL — 门禁本身有缺陷（${failed.length} 项）` : '[selftest] PASS — 正负双向自证通过');
  process.exit(failed.length ? 1 : 0);
}

function main() {
  const args = process.argv.slice(2);
  const root = resolve(argValue(args, '--root') || process.cwd());
  if (args.includes('--selftest')) selftest();
  if (args.includes('--init')) initFromTemplates(root);
  if (args.includes('--emit-registry')) { emitRegistry(root); process.exit(0); }

  const report = check(root, { check: args.includes('--check') });
  if (args.includes('--json')) console.log(JSON.stringify(report, null, 2));
  else if (report.violations.length === 0) console.log(`[dashboards] PASS — ${report.summary.active}/${report.summary.slots} 槽位 active，一图一决策且无重复图（RULE-054）`);
  else {
    console.log(`[dashboards] FAIL — ${report.violations.length} 项违规（RULE-054）`);
    for (const x of report.violations) console.log(`  - ${x.name}  [${x.kind}]  → ${x.dest}`);
  }
  for (const x of report.warnings) console.log(`  [WARN] ${x.name}  [${x.kind}]  → ${x.dest}`);
  process.exit(report.violations.length ? 1 : 0);
}

main();
