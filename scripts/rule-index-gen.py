#!/usr/bin/env python3
"""规则索引生成器：plugins/registry.yaml 为唯一真源，生成 applies_to.md 的索引区块。

设计口径（对应"单一真源"改造）：
  · 真源 = plugins/registry.yaml 的 rules 段（name / version / rule_id / level）。
  · 生成区 = rules/applies_to.md 里 `<!-- generated:rule-index begin/end -->` 之间的表格。
  · 附带同步：各 rules/*.md frontmatter 的 `version:` 行由真源覆盖（仅改这一行，正文不动）。
  · 区块外正文（说明、使用流程）是人工资产，生成器一律不碰。

用法:
  python scripts/rule-index-gen.py           # 生成（仅在内容有差异时写盘）
  python scripts/rule-index-gen.py --check   # 只校验是否有漂移，不写盘；有漂移退出码 1
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "plugins" / "registry.yaml"
APPLIES = ROOT / "rules" / "applies_to.md"
BEGIN = "<!-- generated:rule-index begin -->"
END = "<!-- generated:rule-index end -->"
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.S)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def read_keep_eol(path: Path) -> tuple[bytes, str, str]:
    """读文件，返回 (原始字节, LF 归一化文本, 换行符)。"""
    data = path.read_bytes()
    enc = "utf-8-sig" if data[:3] == b"\xef\xbb\xbf" else "utf-8"
    text = data.decode(enc)
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    nl = "\r\n" if crlf > lf else "\n"
    return data, text.replace("\r\n", "\n"), nl


def write_if_changed(path: Path, old_bytes: bytes, lf_text: str, nl: str) -> bool:
    new_bytes = lf_text.replace("\n", nl).encode("utf-8")
    if new_bytes == old_bytes:
        return False
    path.write_bytes(new_bytes)
    return True


def load_frontmatter(path: Path) -> dict:
    data, lf_text, _ = read_keep_eol(path)
    m = FRONTMATTER_RE.match(lf_text)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def cell(values) -> str:
    if not values:
        return "—"
    if not isinstance(values, list):
        values = [values]
    out = []
    for v in values:
        v = str(v).strip()
        out.append("全部 Agent" if v.lower() == "all" else v)
    return ", ".join(out)


def registry_rules() -> dict:
    reg = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    return reg.get("rules", {})


def build_block(rules: dict) -> list[str]:
    lines = [
        BEGIN,
        "<!-- 本区块由 scripts/rule-index-gen.py 生成：版本/RULE/级别取自 plugins/registry.yaml，",
        "     Agent/阶段/项目类型/技术栈取自各 rules/*.md 的 frontmatter。勿手改，改源后重跑生成器。 -->",
        "| 规则文件 | 版本 | RULE | 级别 | 适用 Agent | 适用阶段 | 适用项目类型 | 适用技术栈 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, meta in rules.items():
        md = ROOT / "rules" / f"{name}.md"
        fm = load_frontmatter(md) if md.exists() else {}
        applies = fm.get("applies_to") or {}
        rule_ids = cell(meta.get("rule_id"))
        lines.append(
            "| `rules/{name}.md` | {ver} | {rid} | {lvl} | {agents} | {phases} | {types} | {stacks} |".format(
                name=name,
                ver=meta.get("version", "—"),
                rid=rule_ids,
                lvl=meta.get("level", "—"),
                agents=cell(applies.get("agents")),
                phases=cell(applies.get("phases")),
                types=cell(applies.get("project_types")),
                stacks=cell(applies.get("tech_stacks")),
            )
        )
    lines.append(END)
    return lines


def replace_block(lf_text: str, block: list[str]) -> str:
    start = lf_text.find(BEGIN)
    end = lf_text.find(END)
    if start < 0 or end < start:
        raise SystemExit(f"[ERR] {APPLIES} 缺少生成区标记：{BEGIN} / {END}")
    end += len(END)
    return lf_text[:start] + "\n".join(block) + lf_text[end:]


def sync_versions(rules: dict) -> list[str]:
    changed = []
    for name, meta in rules.items():
        md = ROOT / "rules" / f"{name}.md"
        if not md.exists() or not meta.get("version"):
            continue
        old_bytes, lf_text, nl = read_keep_eol(md)
        m = FRONTMATTER_RE.match(lf_text)
        if not m:
            continue
        body, fm_text = m.group(1), m.group(1)
        new_fm, n = re.subn(
            r"^version:\s*v[\d.]+$",
            f"version: {meta['version']}",
            fm_text,
            count=1,
            flags=re.M,
        )
        if n == 0:
            continue
        new_text = lf_text.replace(body, new_fm, 1)
        if write_if_changed(md, old_bytes, new_text, nl):
            changed.append(f"rules/{name}.md")
    return changed


def main() -> int:
    check = "--check" in sys.argv
    rules = registry_rules()
    if not rules:
        print("[ERR] plugins/registry.yaml 没有 rules 段")
        return 2

    old_bytes, lf_text, nl = read_keep_eol(APPLIES)
    new_text = replace_block(lf_text, build_block(rules))

    drift = []
    if new_text != lf_text:
        drift.append("rules/applies_to.md")
    for name, meta in rules.items():
        md = ROOT / "rules" / f"{name}.md"
        if not md.exists():
            drift.append(f"rules/{name}.md（缺失）")
            continue
        fm = load_frontmatter(md)
        if fm.get("version") and meta.get("version") and fm["version"] != meta["version"]:
            drift.append(f"rules/{name}.md（frontmatter {fm['version']} ≠ registry {meta['version']}）")

    if check:
        if drift:
            print("[DRIFT] 以下文件与真源不一致：")
            for d in drift:
                print(f"  - {d}")
            return 1
        print(f"[OK] 索引与真源一致（{len(rules)} 条规则）")
        return 0

    wrote = write_if_changed(APPLIES, old_bytes, new_text, nl)
    synced = sync_versions(rules)
    print(f"规则数: {len(rules)}")
    print(f"applies_to 区块: {'已更新' if wrote else '无变化'}")
    print(f"frontmatter 版本同步: {len(synced)} 个文件")
    for s in synced:
        print(f"  - {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
