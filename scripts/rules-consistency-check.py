#!/usr/bin/env python3
"""
规则库一致性审计（供 CI 与 rules/gate.sh 调用）

确定性检查以下一致性契约：
  1. AGENTS.md 硬性规则速查表每个条目的"详情位置"文件存在
  2. RULE 编号无重复（废弃规则允许跳号）
  3. 每个 rules/*.md 均已在 applies_to.md 索引中登记，反之亦然
  4. 规则/技能 frontmatter 版本与 plugins/registry.yaml、rules/applies_to.md 一致
  5. AGENTS.md / rules/ / skills/ 中引用的 hooks|scripts 路径真实存在
  6. License 交叉一致：黑名单 License（AGPL-3.0 等）工具不得在规则正文被推荐而不写 ADR 豁免标注
  7. 选型决策的 ADR 存在性（推荐具名外部工具须有 ADR）
  8. 规则存活度体检（RULE-057 类结构性失效）：幽灵 Agent 引用 / 零触发规则 /
     编号不自述 / 废弃编号自述 / 编号双重归属（委托 scripts/rule-liveness-check.py）

用法:
  python scripts/rules-consistency-check.py [--verbose] [--trigger scheduled|manual|hook]

每次运行会向 logs/gate-runs/<YYYYMM>.jsonl 追加一条记录（gate_id=rules-consistency）。
记录写失败时按 FAIL 处理（退出码 1），并在 stderr 说明。

退出码: 0 = 全部通过；1 = 存在不一致或记录写入失败；2 = 参数非法
"""

import os
import re
import sys
from pathlib import Path

from gate_runs import utc_now, write_record

# Windows GBK 控制台兼容：强制 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
RULES_ROOT = SCRIPT_DIR.parent  # scripts/ 的父目录即规则库根

RULE_CELL_RE = re.compile(r"^\s*\|\s*\*{0,2}(RULE-(?:\d{3}|[A-Z]+))\*{0,2}\s*\|")
BACKTICK_RE = re.compile(r"`([^`]+)`")
VER_RE = re.compile(r"^version:\s*(v[\d.]+)", re.MULTILINE)


def parse_frontmatter_version(text: str) -> str | None:
    m = re.search(r"^---\s*$", text, re.MULTILINE)
    if not m:
        return None
    end = text.find("\n---", m.end())
    if end < 0:
        return None
    vm = VER_RE.search(text[m.end():end])
    return vm.group(1) if vm else None


def agents_rules() -> list[tuple[str, str]]:
    """从 AGENTS.md 速查表提取 (RULE 编号, 详情位置)。取第 3 列（详情位置）。"""
    agents_md = RULES_ROOT / "AGENTS.md"
    out: list[tuple[str, str]] = []
    if not agents_md.exists():
        return out
    for line in agents_md.read_text(encoding="utf-8").splitlines():
        if not RULE_CELL_RE.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        rule_id = cells[0].replace("*", "").strip()
        location = ""
        for bt in BACKTICK_RE.findall(cells[2]):
            if bt.endswith(".md") or "/" in bt:
                location = bt
                break
        if location:
            out.append((rule_id, location))
    return out


def collect_rule_files() -> list[Path]:
    rules_dir = RULES_ROOT / "rules"
    return sorted(p for p in rules_dir.glob("*.md") if p.name != "applies_to.md")


def collect_indexed_versions() -> dict[str, str]:
    """applies_to.md: 文件名 -> 版本"""
    index_file = RULES_ROOT / "rules" / "applies_to.md"
    out: dict[str, str] = {}
    if not index_file.exists():
        return out
    for line in index_file.read_text(encoding="utf-8").splitlines():
        m = re.search(r"\`rules/([^\`]+\.md)\`\s*\|\s*(v[\d.]+)", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def collect_registry_versions(section: str) -> dict[str, str]:
    """plugins/registry.yaml 指定 section 下 name -> version（缩进 2/4 空格）"""
    reg = RULES_ROOT / "plugins" / "registry.yaml"
    out: dict[str, str] = {}
    if not reg.exists():
        return out
    lines = reg.read_text(encoding="utf-8").splitlines()
    in_sec = False
    name = None
    for line in lines:
        if re.match(rf"^{section}:\s*$", line):
            in_sec = True
            continue
        if in_sec and re.match(r"^[a-z]", line):
            break
        if not in_sec:
            continue
        m = re.match(r"^  ([a-z0-9-]+):\s*$", line)
        if m:
            name = m.group(1)
            continue
        if name:
            vm = re.match(r"^    version:\s*(v[\d.]+)", line)
            if vm:
                out[name] = vm.group(1)
    return out


def scan_dangling_paths() -> list[str]:
    """扫描 AGENTS.md / rules / skills 中 hooks|scripts 路径引用是否存在

    两级豁免（v4.16.1 取代原文件级 exempt 名单）：
       原来 exempt = {"scripts/deploy.sh", "scripts/update-deployed.py"} 是**自我豁免**——
       命中实体其实是 rules/cicd-rules.md 的部署示例，而那些内容是在说明「本库**不**包含
       这些脚本/这是项目侧自建」。名单式豁免让这两个路径今后在任何规则里被引用都不报警
       （fail-open），与 root-exemptions.yaml 的 fail-closed 哲学冲突，读者无法预期。
       改为两级判定：
         L1 行级：本行是否定式陈述（含 不含/不存在/需项目自建…）
         L2 上下文级：向前 6 行内有「示例/自建/不含」声明
                  —— 覆盖 yaml/代码块内引用（否定说明只能写在块外的情况）
       两者皆不满足仍 FAIL：肯定式引用 + 无任何声明 = FAIL。
    """
    issues: list[str] = []
    targets: list[Path] = [RULES_ROOT / "AGENTS.md"]
    for d in ("rules", "skills"):
        targets += [p for p in (RULES_ROOT / d).rglob("*.md") if "archive" not in p.parts]
    pat = re.compile(r"(?<![A-Za-z0-9_./-])(?:hooks|scripts)/[A-Za-z0-9_./-]+\.(?:py|js|sh|ts)(?![A-Za-z0-9])")
    NEGATION_RE = re.compile(r"不含|不包含|不存在|无此|未提供|需项目|自建|自行实现|项目侧|示例")
    CONTEXT_LOOKBACK = 6
    for f in targets:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            for rel in pat.findall(line):
                # hooks/README.md 等文件内的路径以其所在目录为基准，跳过相对误报
                if f.name == "README.md" and f.parent.name == "hooks":
                    continue
                if NEGATION_RE.search(line):
                    continue  # L1 行级否定
                ctx = "\n".join(lines[max(0, i - 1 - CONTEXT_LOOKBACK):i - 1])
                if NEGATION_RE.search(ctx):
                    continue  # L2 上下文级：前置几行已声明「示例/项目自建」
                if not (RULES_ROOT / rel).exists():
                    issues.append(f"{f.relative_to(RULES_ROOT)}:{i} 引用不存在的路径: {rel}")
    return issues


def scan_license_conflicts() -> list[str]:
    """黑名单 License 工具（open-source-first.md §3）在 rules/ 正文被推荐时必须同行标注豁免。

    判据：同一行同时出现工具名与黑名单 License 串，且无「豁免/exception」标注即报 issue。
    仅判同行，避免黑名单定义行、工具名单独出现等误报。
    """
    issues: list[str] = []
    tools: dict[str, str] = {"grafana": "agpl-3.0", "loki": "agpl-3.0", "minio": "agpl-3.0"}
    for p in collect_rule_files():
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            for tool, lic in tools.items():
                if tool in low and lic in low and "豁免" not in line and "exception" not in low:
                    issues.append(
                        f"rules/{p.name}:{i} 推荐 {tool}（{lic}，License 黑名单）但未标注 ADR 豁免"
                    )
    return issues


def scan_adr_required() -> list[str]:
    """RULE-017/019：规则正文推荐**外部工具/框架/服务/依赖**时，必须有对应 ADR。

    判据（刻意收窄，避免变成"公文式 ADR 制造机"）：
      只覆盖**选型类表述**——规则里推荐某个具名的外部框架/库/平台/服务，
      且未标注豁免（「ADR 已记」「豁免」「例外」）。纯内部约定、流程纪律、
      通用原则不判（那是 RULE-015/YAGNI 的领地，不是选型）。

    为什么收窄：ADR-008 的教训是"为填模板编标准只会制造噪音"。
    无边界的"每个决策都要 ADR"会产出大量无信息量的 ADR；反过来，
    "引入了外部依赖却无 ADR"是**具体、可判、后果明确**的一类。
    本项只抓这一类。

    已知豁免（不判）：
      - 已在同文件/同段被声明为「ADR-00N 已记」或「豁免/exception」的
      - 仅在历史归档/报告中出现的（collect_rule_files 已排除 archive）
    """
    issues: list[str] = []
    # 选型句：出现「采用/引入/选用/推荐/优先使用 <X>」的具名外部工具。
    # 工具名形态约束：至少 3 字符、含大写字母或点号/连字符（React、FastAPI、node.js、
    # @deepseek-ai/dsh-*、wrangler），排除 const/let/Tag/Index 这类语言关键字与普通词。
    SELECTION_RE = re.compile(
        r"(?:采用|引入|选用|推荐|优先(?:使用|采用)|统一使用)\s*[`*]+([A-Za-z][A-Za-z0-9._-]{2,})"
    )
    KEYWORD_DENY = {
        "const", "let", "var", "tag", "index", "file", "type", "name", "date",
        "list", "dict", "self", "true", "false", "none", "null", "test", "main",
    }
    EXEMPT_RE = re.compile(r"ADR-\d+|豁免|exception|已记录|无需 ADR|不必写 ADR")
    for p in collect_rule_files():
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            m = SELECTION_RE.search(line)
            if not m:
                continue
            tool = m.group(1)
            if tool.lower() in KEYWORD_DENY:
                continue  # 语言关键字/普通词，不是具名外部工具
            # 具名工具的必要特征：含大写字母（React/FastAPI/Docker）或点号/连字符（node.js/josa-x）
            if not any(c.isupper() for c in tool) and ("." not in tool and "-" not in tool):
                continue
            # 同行已声明 ADR 或豁免 → 放行
            if EXEMPT_RE.search(line):
                continue
            # 同文件正文中任意位置出现该工具 + ADR 关联声明 → 放行
            # （"本文的选型决策已记录在 ADR-00N"这类段落级豁免）
            if re.search(rf"{re.escape(tool)}[^\n]{{0,80}}ADR-\d+", text) or re.search(
                rf"ADR-\d+[^\n]{{0,80}}{re.escape(tool)}", text
            ):
                continue
            issues.append(
                f"rules/{p.name}:{i} 推荐外部工具「{tool}」但未记录 ADR（RULE-017/019）"
            )
    return issues


def scan_rule_liveness() -> list[str]:
    """第 8 项：规则存活度体检（RULE-057 类结构性失效）。

    调用 scripts/rule-liveness-check.py 的 analyze()，把缺口转成 issues 文本。
    检查内容：幽灵 Agent 引用 / 零触发规则 / 编号不自述 / 废弃编号自述 / 编号双重归属。
    体检脚本缺失时**跳过**（不因工具缺失制造假红）。
    """
    mod_path = RULES_ROOT / "scripts" / "rule-liveness-check.py"
    if not mod_path.exists():
        return []
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("_rule_liveness", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        res = mod.analyze(RULES_ROOT)
    except Exception as exc:  # noqa: BLE001
        return [f"规则存活度体检执行失败: {exc}"]
    return [
        f"[{f['check']}] {f['rule']} — {f['detail']}"
        for f in res.get("findings", [])
    ]


def main() -> int:
    verbose = "--verbose" in sys.argv
    started_at = utc_now()
    trigger = os.environ.get("GATE_TRIGGER", "manual").lower()
    if "--trigger" in sys.argv:
        i = sys.argv.index("--trigger")
        if i + 1 >= len(sys.argv):
            print("[gate-runs] --trigger 缺少取值", file=sys.stderr)
            return 2
        trigger = sys.argv[i + 1].lower()
    if trigger not in ("scheduled", "manual", "hook"):
        print(f"[gate-runs] 非法 trigger={trigger!r}（允许 scheduled/manual/hook）", file=sys.stderr)
        return 2
    issues: list[str] = []

    # 1 & 2. AGENTS 速查表：位置存在 + 编号重复
    rules = agents_rules()
    if not rules:
        issues.append("AGENTS.md 速查表解析失败（未找到 RULE 条目）")
    else:
        for rule_id, loc in rules:
            cand = RULES_ROOT / loc if loc.startswith(("rules/", "skills/", "hooks/", "docs/")) else RULES_ROOT / "rules" / loc
            if not cand.exists():
                issues.append(f"{rule_id} 详情位置文件不存在: {loc}")
            elif verbose:
                print(f"  {rule_id}: {loc} -> OK")
        nums = [int(r.replace("RULE-", "")) for r, _ in rules if r[5:].isdigit()]
        seen: set[int] = set()
        dup = sorted({n for n in nums if n in seen or seen.add(n)})
        if dup:
            issues.append(f"RULE 编号重复: {['RULE-%03d' % n for n in dup]}")

    # 3. rules/*.md 与 applies_to.md 索引双向对齐
    rule_files = collect_rule_files()
    indexed_versions = collect_indexed_versions()
    unindexed = [p.name for p in rule_files if p.name not in indexed_versions]
    if unindexed:
        issues.append(f"rules/ 存在但未登记到 applies_to.md: {unindexed}")
    stale = [f for f in indexed_versions if not (RULES_ROOT / "rules" / f).exists()]
    if stale:
        issues.append(f"applies_to.md 登记但 rules/ 不存在: {stale}")

    # 4. 版本一致性
    registry_rules = collect_registry_versions("rules")
    registry_skills = collect_registry_versions("skills")
    for p in rule_files:
        fv = parse_frontmatter_version(p.read_text(encoding="utf-8"))
        if not fv:
            continue
        rv = registry_rules.get(p.stem)
        av = indexed_versions.get(p.name)
        if rv and rv != fv:
            issues.append(f"版本不一致: rules/{p.name} file={fv} registry={rv}")
        if av and av != fv:
            issues.append(f"版本不一致: rules/{p.name} file={fv} applies_to={av}")
    for sk in sorted((RULES_ROOT / "skills").glob("*/SKILL.md")):
        fv = parse_frontmatter_version(sk.read_text(encoding="utf-8"))
        rv = registry_skills.get(sk.parent.name)
        if fv and rv and rv != fv:
            issues.append(f"版本不一致: skills/{sk.parent.name}/SKILL.md file={fv} registry={rv}")

    # 5. 悬空路径引用
    issues += scan_dangling_paths()

    # 6. License 交叉一致（黑名单工具推荐必须带豁免标注）
    issues += scan_license_conflicts()

    # 7. 选型决策的 ADR 存在性（RULE-017/019，v4.16.1）
    issues += scan_adr_required()

    # 8. 规则存活度体检（RULE-057 类结构性失效，v4.19.0）
    issues += scan_rule_liveness()

    print(f"规则文件数: {len(rule_files)} | AGENTS.md RULE 条目: {len(rules)} | 索引登记数: {len(indexed_versions)}")
    exit_code = 0
    if issues:
        print("\n[FAIL] 规则库一致性审计发现以下问题:")
        for it in issues:
            print(f"  - {it}")
        exit_code = 1
    else:
        print("\n[PASS] 规则库一致性审计通过（位置存在、编号不重复、索引双向对齐、版本一致、无悬空路径、License 交叉一致）")

    logged = write_record(
        gate_id="rules-consistency",
        mode="dry-run",
        trigger=trigger,
        result="FAIL" if exit_code else "PASS",
        rule_ids=[],
        evidence={
            "checker": "scripts/rules-consistency-check.py",
            "rule_files": len(rule_files),
            "agents_rule_entries": len(rules),
            "indexed_entries": len(indexed_versions),
            "issues": len(issues),
            "sample": issues[:5],
        },
        started_at=started_at,
        exit_code=exit_code,
    )
    return exit_code if logged else 1


if __name__ == "__main__":
    sys.exit(main())
