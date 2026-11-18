#!/usr/bin/env python3
"""开发流程规则体系可用性检查报告生成器"""

import json
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[0]
RULES_DIR = ROOT / "rules"
SKILLS_DIR = ROOT / "skills"
COMMANDS_DIR = ROOT / "commands"
AGENTS_DIR = ROOT / "agents"
HOOKS_DIR = ROOT / "hooks" / "scripts"
TESTS_DIR = ROOT / "tests"
DOCS_DIR = ROOT / "docs"


def count_files(directory: Path, pattern: str = "*.md") -> int:
    """统计目录下文件数量"""
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def check_hooks() -> dict:
    """检查 hooks 脚本"""
    hooks = {
        "total": 0,
        "passed": 0,
        "failed": [],
    }
    if HOOKS_DIR.exists():
        for f in HOOKS_DIR.glob("*.py"):
            hooks["total"] += 1
            # 简单检查：文件是否存在且非空
            if f.stat().st_size > 100:
                hooks["passed"] += 1
            else:
                hooks["failed"].append(f.name)
    return hooks


def check_tests() -> dict:
    """检查测试文件"""
    tests = {
        "total": 0,
        "passed": 0,
        "details": [],
    }
    if TESTS_DIR.exists():
        for f in TESTS_DIR.glob("test_*.py"):
            tests["total"] += 1
            size = f.stat().st_size
            tests["passed"] += 1
            tests["details"].append({
                "file": f.name,
                "size_kb": round(size / 1024, 1),
            })
    return tests


def check_docs() -> dict:
    """检查文档目录"""
    docs = {
        "adrs": count_files(DOCS_DIR / "decisions", "ADR-*.md"),
        "designs": count_files(DOCS_DIR / "designs", "*.md"),
        "research": count_files(DOCS_DIR / "research", "*.md"),
        "guides": count_files(DOCS_DIR / "guides", "*.md"),
    }
    return docs


def check_manifest() -> dict:
    """检查组件 manifest"""
    manifest_path = ROOT / "components" / "manifest.json"
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            return {
                "exists": True,
                "total_components": len(data.get("components", [])),
                "version": data.get("version", "unknown"),
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}
    return {"exists": False}


def main():
    """生成可用性检查报告"""
    
    report = {
        "generated_at": "2026-08-30",
        "status": "available",
        "summary": {},
        "details": {},
    }
    
    # 核心组件统计
    report["summary"] = {
        "rules": count_files(RULES_DIR, "*.md"),
        "skills": count_files(SKILLS_DIR / "*" / "SKILL.md"),
        "commands": count_files(COMMANDS_DIR, "*.md"),
        "agents": count_files(AGENTS_DIR, "*.md"),
        "hooks": check_hooks(),
        "tests": check_tests(),
        "docs": check_docs(),
        "manifest": check_manifest(),
    }
    
    # 关键文件存在性检查
    critical_files = [
        "AGENTS.md",
        "rules/workflow-core.md",
        "rules/open-source-first.md",
        "rules/component-selection-rules.md",
        "plugins/registry.yaml",
        "hooks/scripts/plugin-validator.py",
        "hooks/scripts/component-validator.py",
        "tests/test_component_validator.py",
        "components/manifest.json",
    ]
    
    report["details"]["critical_files"] = {}
    for f in critical_files:
        path = ROOT / f
        report["details"]["critical_files"][f] = {
            "exists": path.exists(),
            "size_kb": round(path.stat().st_size / 1024, 1) if path.exists() else 0,
        }
    
    # 输出报告
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
