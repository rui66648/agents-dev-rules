#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则存活度体检（RULE-057 类结构性失效的防复发门禁）
=====================================================

为什么需要它：RULE-057 于 2026-11-09 写入后跨 8 批真实任务零触发，根因不是内容质量，
而是**接入层断点**（未进入 AGENTS.md §2 入口路由 / 无产物落点 / 无模板 / 无可执行判据 /
applies_to.agents 指向不存在的 Agent）。现有 `rules-consistency-check.py` 只查「路径存在、
编号不重复、版本一致、悬空路径」——**查不出「规则没人读」**，更查不出「按 applies_to 过滤时
永远过滤不出来」这类语义缺陷。本脚本补上这一层。

五项检查：
  C1 幽灵 Agent 引用 —— applies_to.agents 指向 registry/agents/ 中不存在的 Agent
                          （后果：按 agents 过滤加载时该规则永远加载不出来）
  C2 零触发规则     —— 既不在 §2 入口路由、也不被任何 skill/command 引用、
                          不在 §3 速查表落点、也不在 AGENTS.md 其他章节被声明
  C3 编号不自述     —— registry 登记了 rule_id，但落点文件正文不提及该编号（读文件的人无从得知）
  C4 废弃编号自述   —— 文件的「本文件落实」行声明了已在 AGENTS.md「已废弃规则」表中的编号
  C5 编号双重归属   —— 同一 RULE 编号被多个文件以「本文件落实」方式声明（违反一主题一份真源）
  C6 速查表↔registry 双向登记 —— C6a：AGENTS.md §3 速查表登记的编号（落点在 rules/<file>.md）
                          必须登记在 registry 的该 file 名下（抓「速查表有、registry 无」的漏登记）；
                          C6b：registry 登记的每个编号必须在 §3 速查表出现（抓「只登记不入表」）

用法：
    python scripts/rule-liveness-check.py                # 体检，退出码 0=通过 / 1=有缺口
    python scripts/rule-liveness-check.py --json         # JSON 输出
    python scripts/rule-liveness-check.py --selftest     # 临时目录构造正/负例自证

退出码：0 = 全部通过；1 = 存在缺口；2 = 参数非法 / 环境错误
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("[ERR] 需要 PyYAML：pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 「全部 Agent」这类通配值不算幽灵引用
WILDCARD_AGENTS = {"all", "全部 agent", "全部", "全角色", "everyone"}

# AGENTS.md「已废弃规则」表覆盖的编号（AGENTS.md §3 已废弃规则）
DEPRECATED_RANGES = [
    (20, 25), (26, 26), (27, 27), (29, 29), (31, 31),
    (37, 40), (44, 46),
]

FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.S)
RULE_ID_RE = re.compile(r"RULE-[A-Z0-9\-]+")


def _read(path: Path) -> str:
    data = path.read_bytes()
    enc = "utf-8-sig" if data[:3] == b"\xef\xbb\xbf" else "utf-8"
    return data.decode(enc)


def _frontmatter(path: Path) -> dict:
    m = FM_RE.match(_read(path).replace("\r\n", "\n"))
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _is_deprecated(rule_id: str) -> bool:
    m = re.fullmatch(r"RULE-(\d+)", rule_id)
    if not m:
        return False
    n = int(m.group(1))
    return any(lo <= n <= hi for lo, hi in DEPRECATED_RANGES)


def _real_agents(root: Path) -> set[str]:
    agents: set[str] = set()
    reg = yaml.safe_load(_read(root / "plugins" / "registry.yaml"))
    for name in (reg.get("agents") or {}):
        agents.add(str(name).strip())
    agents_dir = root / "agents"
    if agents_dir.is_dir():
        for f in agents_dir.glob("*.md"):
            if f.stem.lower() == "index":  # index.md 是索引，不是 Agent
                continue
            agents.add(f.stem)
    return agents


def _agent_md_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for d in ("skills", "commands"):
        base = root / d
        if base.is_dir():
            out.extend(base.rglob("*.md"))
    return out


def _parse_quick_table(sec3: str) -> list[tuple[str, str]]:
    """解析 AGENTS.md §3「硬性规则速查表」的行 → [(RULE 编号, 详情位置)]。

    排除：§3 内的「已废弃规则」小节、编号区间行（如 RULE-020~025）、表头与分隔行。
    """
    rows: list[tuple[str, str]] = []
    in_deprecated = False
    for ln in sec3.splitlines():
        if ln.startswith("###") and "废弃" in ln:
            in_deprecated = True
            continue
        if ln.startswith("##") and not ln.startswith("###"):
            in_deprecated = False
        if in_deprecated or not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.split("|")]
        if len(cells) < 4:
            continue
        first = cells[1]
        if "~" in first or set(first) <= set("- :"):
            continue  # 区间行 / 分隔行
        m = re.search(r"RULE-[A-Z0-9\-]+", first)
        if not m:
            continue
        rid = m.group(0)
        loc = cells[3]
        rows.append((rid, loc))
    return rows


def analyze(root: Path) -> dict:
    findings: list[dict] = []
    rules_dir = root / "rules"
    agents_md = root / "AGENTS.md"
    reg = yaml.safe_load(_read(root / "plugins" / "registry.yaml"))
    registry_rules = reg.get("rules") or {}
    real_agents = _real_agents(root)

    rule_files = sorted(
        f for f in rules_dir.glob("*.md") if f.name != "applies_to.md"
    )

    # ── AGENTS.md 章节切分 ────────────────────────────────────────────
    agents_text = _read(agents_md).replace("\r\n", "\n")
    lines = agents_text.splitlines()

    def section(start_pat: str, end_pat: str) -> str:
        s = e = None
        for i, ln in enumerate(lines):
            if s is None and re.match(start_pat, ln):
                s = i
            elif s is not None and re.match(end_pat, ln):
                e = i
                break
        if s is None:
            return ""
        return "\n".join(lines[s: e if e is not None else len(lines)])

    sec2 = section(r"^## 2\. 入口路由", r"^## 3\.")
    sec3 = section(r"^## 3\. 硬性规则速查", r"^## 4\.")
    sec_rest = "\n".join(
        ln for ln in lines if not re.match(r"^## [23]\.", ln)
    )

    # §3 速查表「详情位置」列里出现的规则文件（= 可被查得）
    sec3_files = set(re.findall(r"rules/([a-z0-9\-]+)\.md", sec3))
    # §2 入口路由里出现的规则文件（= 会被加载）
    sec2_files = set(re.findall(r"rules/([a-z0-9\-]+)\.md", sec2))
    # AGENTS.md 其他章节（§4 前端组件真源声明等）的声明
    rest_files = set(re.findall(r"rules/([a-z0-9\-]+)\.md", sec_rest))

    # skills/commands 引用（技能与命令是可执行入口，会真正读它）
    skill_cmd_refs: set[str] = set()
    for f in _agent_md_files(root):
        text = _read(f)
        for m in re.finditer(r"rules/([a-z0-9\-]+)\.md", text):
            skill_cmd_refs.add(m.group(1))

    # ── 逐文件检查 ──────────────────────────────────────────────────
    claims: dict[str, list[str]] = {}  # RULE 编号 -> 声明它的文件

    for f in rule_files:
        stem = f.stem
        text = _read(f).replace("\r\n", "\n")
        fm = _frontmatter(f)
        head = "\n".join(text.splitlines()[:25])

        # C1 幽灵 Agent 引用
        applies = fm.get("applies_to") or {}
        for a in (applies.get("agents") or []):
            name = str(a).strip().strip("'\"").strip()
            if not name or name.lower() in WILDCARD_AGENTS:
                continue
            if name not in real_agents:
                findings.append({
                    "check": "C1-ghost-agent",
                    "rule": f.name,
                    "detail": f"applies_to.agents 指向不存在的 Agent: {name}",
                })

        # C3 编号不自述
        reg_ids = [str(x) for x in (registry_rules.get(stem, {}).get("rule_id") or [])]
        for rid in reg_ids:
            if rid not in head:
                findings.append({
                    "check": "C3-id-not-declared",
                    "rule": f.name,
                    "detail": f"registry 登记 {rid}，但落点文件正文未提及该编号",
                })

        # C4 / C5：收集「本文件落实」行里的编号
        # 判定「已废弃」要看编号**紧随其后**的说明：编号后紧跟「已废弃 / 废弃」= 免责声明
        # （如 agent-constraints 的「RULE-026/027/029 已废弃，由运行时会话/轨迹能力替代」），
        # 否则视为真实声明。
        for ln in text.splitlines():
            if "本文件落实" not in ln:
                continue
            for m in RULE_ID_RE.finditer(ln):
                rid = m.group(0)
                tail = ln[m.end(): m.end() + 30]
                if "废弃" in tail:
                    continue  # 免责声明，不是声明
                claims.setdefault(rid, []).append(f.name)
                if _is_deprecated(rid):
                    findings.append({
                        "check": "C4-deprecated-id-claimed",
                        "rule": f.name,
                        "detail": f"「本文件落实」行声明了已废弃编号 {rid}",
                    })

        # C2 零触发
        loadable = (
            stem in sec2_files
            or stem in skill_cmd_refs
            or stem in sec3_files
            or stem in rest_files
        )
        if not loadable:
            findings.append({
                "check": "C2-unreachable-rule",
                "rule": f.name,
                "detail": "无任何加载路径：不在 §2 入口路由、未被 skill/command 引用、"
                          "不在 §3 速查表落点、也未被 AGENTS.md 其他章节声明",
            })

    # C5 编号双重归属
    for rid, owners in sorted(claims.items()):
        uniq = sorted(set(owners))
        if len(uniq) > 1:
            findings.append({
                "check": "C5-dual-ownership",
                "rule": ", ".join(uniq),
                "detail": f"{rid} 被多个文件同时以「本文件落实」方式声明（应为一份真源）",
            })

    # C6 速查表 ↔ registry 双向登记（v4.19.0 补）
    #   C6a 速查表行（详情位置落在 rules/<file>.md）的 RULE 编号，必须登记在 registry 的该 file 名下
    #       —— 抓「速查表有、registry 无」的漏登记（如 RULE-051 曾漏登记 open-source-first）
    #   C6b registry 登记的每个 rule_id，必须在速查表中出现
    #       —— 抓「只登记不入表」的新规则
    # 已废弃规则表（§3 内的小节）与编号区间行（如 RULE-020~025）不参与比对。
    quick_rows = _parse_quick_table(sec3)
    for rid, loc in quick_rows:
        m = re.search(r"rules/([a-z0-9\-]+)\.md", loc)
        if not m:
            continue  # 落点在 docs/ 或 skills/ → 不由 registry 的 rules 段登记
        stem = m.group(1)
        reg_ids = set(registry_rules.get(stem, {}).get("rule_id") or [])
        if rid not in reg_ids:
            findings.append({
                "check": "C6a-quick-table-not-registered",
                "rule": f"{rid} @ rules/{stem}.md",
                "detail": f"AGENTS.md 速查表登记了 {rid} 且落点为 rules/{stem}.md，"
                          f"但 registry.yaml 的 {stem} 未登记该编号",
            })
    quick_ids = {rid for rid, _ in quick_rows}
    for stem, meta in registry_rules.items():
        for rid in (meta.get("rule_id") or []):
            if rid not in quick_ids:
                findings.append({
                    "check": "C6b-registry-not-in-quick-table",
                    "rule": f"{rid} @ rules/{stem}.md",
                    "detail": f"registry 登记了 {rid}，但 AGENTS.md 速查表没有该条目",
                })

    return {
        "root": str(root),
        "scanned": len(rule_files),
        "real_agents": sorted(real_agents),
        "findings": findings,
    }


def selftest(root: Path) -> int:
    """构造正/负例自证，不触碰真实工作区。"""
    import shutil
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="liveness-"))
    passed: list[str] = []
    try:
        (tmp / "rules").mkdir()
        (tmp / "plugins").mkdir()
        (tmp / "agents").mkdir()
        (tmp / "skills").mkdir()
        (tmp / "commands").mkdir()

        (tmp / "plugins" / "registry.yaml").write_text(
            "version: 1\n"
            "agents:\n"
            "  architect:\n"
            "    version: v1.0.0\n"
            "rules:\n"
            "  good-rule:\n"
            "    version: v1.0.0\n"
            "    rule_id: [RULE-001]\n"
            "    level: 铁律\n"
            "  bad-rule:\n"
            "    version: v1.0.0\n"
            "    rule_id: [RULE-002]\n"
            "    level: 建议\n",
            encoding="utf-8",
        )
        (tmp / "agents" / "architect.md").write_text("agent\n", encoding="utf-8")
        (tmp / "skills" / "x").mkdir(parents=True)
        (tmp / "skills" / "x" / "SKILL.md").write_text("skill\n", encoding="utf-8")
        (tmp / "commands").mkdir(exist_ok=True)

        # 负例 1：幽灵 Agent
        (tmp / "rules" / "good-rule.md").write_text(
            "---\nname: good-rule\nversion: v1.0.0\ntype: rule\nenabled: true\n"
            "mode: [standard, creator]\nupdated: 2026-11-11\n"
            "description: d\napplies_to:\n"
            "  agents: ['architect']\n"
            "  phases: ['design']\n  project_types: ['全部']\n  tech_stacks: ['全部']\n---\n"
            "# good\n> **本文件落实**: RULE-001（测试）\n",
            encoding="utf-8",
        )
        # 负例 2：与 good-rule 争抢 RULE-001 的落点（双份声明）
        (tmp / "rules" / "other-rule.md").write_text(
            "---\nname: other-rule\nversion: v1.0.0\ntype: rule\nenabled: true\n"
            "mode: [standard, creator]\nupdated: 2026-11-11\n"
            "description: d\napplies_to:\n"
            "  agents: ['architect']\n"
            "  phases: ['design']\n  project_types: ['全部']\n  tech_stacks: ['全部']\n---\n"
            "# other\n> **本文件落实**: RULE-001（另一处也声明）\n",
            encoding="utf-8",
        )
        # 负例 3：幽灵 Agent + 未自述编号 + 零触发 + 废弃编号
        (tmp / "rules" / "bad-rule.md").write_text(
            "---\nname: bad-rule\nversion: v1.0.0\ntype: rule\nenabled: true\n"
            "mode: [standard, creator]\nupdated: 2026-11-11\n"
            "description: d\napplies_to:\n"
            "  agents: ['devops']\n"
            "  phases: ['design']\n  project_types: ['全部']\n  tech_stacks: ['全部']\n---\n"
            "# bad\n> **本文件落实**: RULE-020（过时编号）\n",
            encoding="utf-8",
        )
        (tmp / "AGENTS.md").write_text(
            "# AGENTS\n\n## 2. 入口路由\n\n| 场景 | 必须读取 |\n|---|---|\n"
            "| x | `rules/good-rule.md` |\n\n"
            "## 3. 硬性规则速查\n\n| 编号 | 规则 | 详情位置 | 门禁 |\n|---|---|---|---|\n"
            "| RULE-001 | good | `rules/good-rule.md` | x |\n"
            "| RULE-003 | 速查表有但 registry 未登记 | `rules/good-rule.md` | x |\n\n"
            "## 4. 其他\n",
            encoding="utf-8",
        )

        r = analyze(tmp)
        kinds = {f["check"] for f in r["findings"]}
        rules_hit = {f["rule"] for f in r["findings"]}

        def assert_(cond: bool, msg: str) -> None:
            if not cond:
                raise AssertionError(msg)
            passed.append(msg)

        assert_("C1-ghost-agent" in kinds, "检出幽灵 Agent 引用")
        assert_("C2-unreachable-rule" in kinds, "检出零触发规则")
        assert_("C3-id-not-declared" in kinds, "检出编号不自述")
        assert_("C4-deprecated-id-claimed" in kinds, "检出废弃编号自述")
        assert_("C5-dual-ownership" in kinds, "检出编号双重归属")
        assert_("C6a-quick-table-not-registered" in kinds, "检出速查表有、registry 未登记")
        assert_("C6b-registry-not-in-quick-table" in kinds, "检出 registry 有、速查表未登记")
        assert_("bad-rule.md" in rules_hit, "负例文件被报出")
        assert_(
            not any(
                f["check"] == "C2-unreachable-rule" and f["rule"] == "good-rule.md"
                for f in r["findings"]
            ),
            "正例（已在 §2 路由）不被误判为零触发",
        )
        assert_(
            not any(
                f["check"] == "C4-deprecated-id-claimed" and f["rule"] == "good-rule.md"
                for f in r["findings"]
            ),
            "正例不被误判为废弃编号自述",
        )
        print("[selftest] PASS")
        for m in passed:
            print("  + " + m)
        return 0
    except AssertionError as e:
        print(f"[selftest] FAIL: {e}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="规则存活度体检")
    ap.add_argument("--root", default=None, help="规则库根目录（默认脚本上级目录）")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--selftest", action="store_true", help="正负例自证")
    args = ap.parse_args()

    if args.selftest:
        return selftest(Path(__file__).resolve().parent.parent)

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    if not (root / "rules").is_dir() or not (root / "plugins" / "registry.yaml").exists():
        print(f"[ERR] 不是规则库根目录: {root}", file=sys.stderr)
        return 2

    r = analyze(root)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 1 if r["findings"] else 0

    print(f"[liveness] root={r['root']}")
    print(f"[liveness] 扫描规则文件 {r['scanned']} 个 | 缺口 {len(r['findings'])} 项")
    for f in r["findings"]:
        print(f"  [{f['check']}] {f['rule']} — {f['detail']}")
    if not r["findings"]:
        print("[liveness] PASS — 无结构性失效缺口（触发入口 / 产物落点 / 模板 / 判据 四件套齐备）")
    return 1 if r["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
