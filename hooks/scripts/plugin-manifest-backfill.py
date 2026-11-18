#!/usr/bin/env python3
"""批量补全插件清单字段（type/enabled/mode）— 落实 RULE-043。

用法：
  python hooks/scripts/plugin-manifest-backfill.py --dry-run   # 预览（不写文件）
  python hooks/scripts/plugin-manifest-backfill.py             # 执行补全
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"
RULES_DIR = ROOT / "rules"
COMMANDS_DIR = ROOT / "commands"
AGENTS_DIR = ROOT / "agents"

TYPE_DIRS = {
    "skill": SKILLS_DIR,
    "rule": RULES_DIR,
    "command": COMMANDS_DIR,
    "agent": AGENTS_DIR,
}

FRONTMATTER_RE = re.compile(r"^(?P<bom>\ufeff?)(?P<fm>---[ \t]*\n.*?\n---[ \t]*\n)(?P<body>.*)$", re.DOTALL)
FIELD_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z_][A-Za-z0-9_]*):\s*(?P<value>.*)$")

# 默认注入值
DEFAULTS = {
    "type": "{ptype}",
    "enabled": "true",
    "mode": "[standard, creator]",
}


def collect_files() -> list[tuple[Path, str]]:
    """收集全部插件文件（排除 README/index）。"""
    files: list[tuple[Path, str]] = []
    for ptype, pdir in TYPE_DIRS.items():
        if not pdir.exists():
            continue
        for path in sorted(pdir.iterdir()):
            if path.is_dir():
                path = path / "SKILL.md"
            if not path.is_file() or path.suffix != ".md":
                continue
            if path.name in ("README.md", "index.md"):
                continue
            files.append((path, ptype))
    return files


def parse_fields(fm_text: str) -> set[str]:
    """提取 frontmatter 中已存在的字段名。"""
    keys: set[str] = set()
    for line in fm_text.splitlines():
        m = FIELD_RE.match(line)
        if m:
            keys.add(m.group("key"))
    return keys


def backfill(path: Path, ptype: str) -> list[str]:
    """为单个文件补全缺失字段，返回注入的字段列表。"""
    text = path.read_text(encoding="utf-8-sig")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return []
    bom = m.group("bom")
    fm_text = m.group("fm")
    body = m.group("body")

    # 去掉首尾 --- 分隔符，得到内部行
    lines = fm_text.splitlines()
    # lines[0] == '---', lines[-1] == '---'
    inner = lines[1:-1]
    # 防御：去掉末尾空行（避免正则贪婪引入）
    while inner and not inner[-1].strip():
        inner.pop()

    existing = parse_fields("\n".join(inner))

    # 确定插入锚点：version 行之后；无 version 则 name 行之后
    anchor_idx = None
    for i, line in enumerate(inner):
        m2 = FIELD_RE.match(line)
        if m2 and m2.group("key") == "version":
            anchor_idx = i
            break
    if anchor_idx is None:
        for i, line in enumerate(inner):
            m2 = FIELD_RE.match(line)
            if m2 and m2.group("key") == "name":
                anchor_idx = i
                break
    if anchor_idx is None:
        anchor_idx = 0

    # 按顺序注入缺失字段
    injected: list[str] = []
    insert_at = anchor_idx + 1
    for key, tmpl in DEFAULTS.items():
        if key in existing:
            continue
        value = tmpl.format(ptype=ptype)
        inner.insert(insert_at, f"{key}: {value}")
        injected.append(key)
        insert_at += 1

    if not injected:
        return []

    new_fm = "---\n" + "\n".join(inner) + "\n---\n"
    new_text = bom + new_fm + body
    path.write_text(new_text, encoding="utf-8")
    return injected


def main() -> int:
    parser = argparse.ArgumentParser(description="批量补全插件清单字段")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写文件")
    args = parser.parse_args()

    total_injected = 0
    changed_files = 0
    for path, ptype in collect_files():
        injected = backfill(path, ptype) if args.dry_run else _apply(path, ptype)
        if injected:
            changed_files += 1
            total_injected += len(injected)
            action = "将注入" if args.dry_run else "已注入"
            print(f"{action} [{ptype}] {path.name}: {', '.join(injected)}")

    print(f"\n共 {changed_files} 个文件，{total_injected} 个字段"
          f"（{'预览' if args.dry_run else '完成'}）")
    return 0


def _apply(path: Path, ptype: str) -> list[str]:
    return backfill(path, ptype)


if __name__ == "__main__":
    sys.exit(main())
