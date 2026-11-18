#!/usr/bin/env python3
"""
取消共享规则版本锁定的跨项目脚本

用法:
    python scripts/update-rules-version.py [--dry-run]

目标机制:
    共享规则根：<RULES_ROOT>\\AGENTS.md（版本唯一真源 vX.Y.Z）
    其他项目：AGENTS.md 中引用共享规则时【不再锁版本号】，
            去除 "( vX.Y.Z )" 后缀，引用变成无版本形式。
    效果：共享规则一更新，所有引用它的项目自动拿到最新版，无需任何同步。

用法说明:
    该脚本会遍历 <PROJECTS_ROOT>\\ 下所有含 AGENTS.md 的项目。
    Windows 沙箱可能阻止写入兄弟项目目录；如遇 PermissionError，
    请授予跨项目写权限后在终端手动运行本脚本。
"""

import argparse
import re
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 仓库根目录 = 本脚本所在目录的上一级；扫描范围 = 其父目录（通常是多仓工作区容器根）
RULES_ROOT = Path(__file__).resolve().parents[1]
PROJECTS_ROOT = RULES_ROOT.parent


def strip_version_lock(project_agents: Path, dry_run: bool = False) -> bool:
    r"""
    去除 AGENTS.md 中共享规则引用的版本号锁。

    处理两类写法：
      1. `<<RULES_ROOT>>\AGENTS.md（v3.3.0）` -> `<<RULES_ROOT>>\AGENTS.md`
      2. 引用行内裸露的版本 `(v3.3.0)` -> 移除
    """
    if not project_agents.exists():
        return False

    content = project_agents.read_text(encoding="utf-8")
    original = content

    # 模式1：<<RULES_ROOT>>\AGENTS.md（vX.Y.Z） 或 (vX.Y.Z) 后缀
    content = re.sub(
        r"(<<RULES_ROOT>>\s*\\\\?\s*AGENTS\.md)\s*[（(]\s*v\d+\.\d+\.\d+\s*[)）]",
        r"\1",
        content,
    )
    # 通用括号版本锁（脱壳兜底）：中文括号 (v3.3.0)
    content = re.sub(r"\s*[（(]\s*v\d+\.\d+\.\d+\s*[)）]", "", content)

    if content == original:
        return False

    if not dry_run:
        project_agents.write_text(content, encoding="utf-8")
        print(f"  [已更新] 去除版本锁: {project_agents.parent.name}")
    else:
        print(f"  [DRY-RUN] 将去除版本锁: {project_agents.parent.name}")
    return True


def find_all_agents_md() -> list[Path]:
    files = []
    for d in PROJECTS_ROOT.iterdir():
        if d.is_dir() and (d / "AGENTS.md").exists():
            files.append(d / "AGENTS.md")
    return files


def main():
    parser = argparse.ArgumentParser(description="去除跨项目共享规则版本锁")
    parser.add_argument("--dry-run", action="store_true", help="预览，不实际修改")
    args = parser.parse_args()

    print("=" * 60)
    print("取消共享规则版本锁定工具")
    print("=" * 60)
    print(f"共享规则唯一年份真源: {RULES_ROOT / 'AGENTS.md'}")

    agents_files = find_all_agents_md()
    print(f"\n扫描到 {len(agents_files)} 个项目:")
    for f in agents_files:
        print(f"  - {f.parent.name}/")

    n = sum(strip_version_lock(f, args.dry_run) for f in agents_files)
    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}去除版本锁: {n} 个项目")
    print("=" * 60)


if __name__ == "__main__":
    main()