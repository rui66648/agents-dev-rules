#!/usr/bin/env python3
"""插件清单校验器 — 落实 RULE-042/RULE-043。

校验范围：
  1. 所有技能/规则/命令/Agent 的 frontmatter 是否符合 plugin-interface.jsonschema
  2. plugins/registry.yaml 与磁盘目录一致性
  3. depends_on / composes / owns 引用完整性

用法：
  python hooks/scripts/plugin-validator.py --check-all
  python hooks/scripts/plugin-validator.py --check <file>
  python hooks/scripts/plugin-validator.py --check-registry
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:  # pragma: no cover - 无 PyYAML 时降级
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "plugin-interface.jsonschema"
REGISTRY_PATH = ROOT / "plugins" / "registry.yaml"
SKILLS_DIR = ROOT / "skills"
RULES_DIR = ROOT / "rules"
COMMANDS_DIR = ROOT / "commands"
AGENTS_DIR = ROOT / "agents"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

TYPE_DIRS = {
    "skill": SKILLS_DIR,
    "rule": RULES_DIR,
    "command": COMMANDS_DIR,
    "agent": AGENTS_DIR,
}


def parse_frontmatter(path: Path) -> dict[str, Any]:
    """解析 Markdown frontmatter，返回 dict（无 frontmatter 返回空 dict）。"""
    text = path.read_text(encoding="utf-8-sig")
    text = text.lstrip("\ufeff\u00a0 \t")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    if yaml is None:
        return _simple_yaml(m.group(1))
    try:
        data = yaml.safe_load(m.group(1))
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _simple_yaml(text: str) -> dict[str, Any]:
    """无 PyYAML 时的极简 frontmatter 解析（仅支持标量/列表）。"""
    result: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
            result[key] = items
        else:
            result[key] = value.strip("'\"")
    return result


def infer_type(path: Path) -> str | None:
    """按目录推断插件类型。"""
    for ptype, pdir in TYPE_DIRS.items():
        if pdir in path.parents:
            return ptype
    return None


def collect_plugins() -> list[tuple[Path, dict[str, Any], str]]:
    """收集全部插件文件及其 frontmatter。"""
    plugins: list[tuple[Path, dict[str, Any], str]] = []
    for ptype, pdir in TYPE_DIRS.items():
        if not pdir.exists():
            continue
        for path in sorted(pdir.iterdir()):
            if path.is_dir():
                path = path / "SKILL.md"
            if not path.is_file() or path.suffix != ".md":
                continue
            if path.name == "README.md" or path.name == "index.md":
                continue
            fm = parse_frontmatter(path)
            if not fm:
                # 无 frontmatter = 非插件文件（索引/元数据文档），跳过
                continue
            plugins.append((path, fm, ptype))
    return plugins


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_registry() -> dict[str, Any]:
    if yaml is None:
        raise SystemExit("错误：校验注册表需要 PyYAML")
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


def validate_manifest(fm: dict[str, Any], ptype: str, path: Path) -> tuple[list[str], list[str]]:
    """校验单个插件清单，返回 (errors, warnings)。

    errors 为硬性违规（非法值/引用断裂），warnings 为遗留兼容提示（缺字段）。
    """
    errors: list[str] = []
    warnings: list[str] = []
    name = fm.get("name", path.stem)
    label = f"{ptype}:{name} ({path})"

    if "name" not in fm:
        warnings.append(f"{label}: 缺少字段 name（遗留文件，建议补充）")
    elif not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", fm["name"]):
        errors.append(f"{label}: name 必须为 kebab-case")

    if "version" not in fm:
        warnings.append(f"{label}: 缺少字段 version（遗留文件，建议补充）")
    elif not re.match(r"^v\d+\.\d+\.\d+$", fm["version"]):
        errors.append(f"{label}: version 必须为 vX.Y.Z 格式")

    if "type" not in fm:
        warnings.append(f"{label}: 缺少字段 type（按目录推断为 {ptype}）")
    elif fm["type"] not in ("skill", "rule", "command", "agent"):
        errors.append(f"{label}: type 非法：{fm['type']}")

    if "mode" in fm:
        invalid = [m for m in fm["mode"] if m not in ("standard", "minimal", "creator")]
        if invalid:
            errors.append(f"{label}: mode 含非法值 {invalid}")

    for dep_key in ("depends_on", "composes"):
        if dep_key in fm and not isinstance(fm[dep_key], list):
            errors.append(f"{label}: {dep_key} 必须为列表")

    return errors, warnings


def check_registry_consistency() -> list[str]:
    """校验注册表与磁盘一致性 + 引用完整性。"""
    errors: list[str] = []
    registry = load_registry()
    plugins = collect_plugins()

    disk_ids = {fm.get("name", p.stem) for p, fm, _ in plugins}
    reg_ids = set()
    for ptype in ("skills", "rules", "commands", "agents"):
        reg_ids.update(registry.get(ptype, {}).keys())

    missing_in_registry = disk_ids - reg_ids
    if missing_in_registry:
        errors.append(f"注册表缺失以下插件: {sorted(missing_in_registry)}")

    stale_in_registry = reg_ids - disk_ids
    if stale_in_registry:
        errors.append(f"注册表含已不存在的插件: {sorted(stale_in_registry)}")

    skill_ids = set(registry.get("skills", {}).keys())
    for sid, meta in registry.get("skills", {}).items():
        for dep in meta.get("depends_on", []) + meta.get("composes", []):
            if dep not in skill_ids:
                errors.append(f"skills/{sid}: 引用不存在的技能插件 {dep}")

    agent_ids = set(registry.get("agents", {}).keys())
    for aid, meta in registry.get("agents", {}).items():
        for own in meta.get("owns", []):
            if own not in skill_ids:
                errors.append(f"agents/{aid}: owns 引用不存在的技能 {own}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="插件清单校验器")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-all", action="store_true", help="校验全部插件清单")
    group.add_argument("--check", metavar="FILE", help="校验单个插件文件")
    group.add_argument("--check-registry", action="store_true", help="校验注册表一致性")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    if args.check_registry:
        errors = check_registry_consistency()
    elif args.check:
        path = Path(args.check)
        if not path.exists():
            print(f"错误：文件不存在 {path}")
            return 1
        ptype = infer_type(path) or "unknown"
        errs, warns = validate_manifest(parse_frontmatter(path), ptype, path)
        errors, warnings = errs, warns
    else:
        for path, fm, ptype in collect_plugins():
            errs, warns = validate_manifest(fm, ptype, path)
            errors.extend(errs)
            warnings.extend(warns)
        errors.extend(check_registry_consistency())

    if warnings:
        print(f"⚠ 插件校验警告（{len(warnings)} 项，遗留兼容不阻断）:")
        for w in warnings[:20]:
            print(f"  - {w}")
        if len(warnings) > 20:
            print(f"  ... 其余 {len(warnings) - 20} 项省略")

    if errors:
        print(f"✗ 插件校验失败（{len(errors)} 项）:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("✓ 插件校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
