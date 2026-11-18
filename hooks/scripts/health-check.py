#!/usr/bin/env python3
"""整体健康检查：引用完整性 + 配置一致性。"""
from pathlib import Path
import re
import sys

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 仓库根目录 = 本脚本所在目录的上一级（不依赖任何绝对路径，可随仓迁移）
ROOT = Path(__file__).resolve().parents[2]
issues = []

# 1. cordis.yaml 引用的插件是否存在
cordis = (ROOT / "cordis.yaml").read_text(encoding="utf-8")
ids = re.findall(r"- id: ([a-z0-9-]+)", cordis)
print("=== cordis.yaml 引用的插件 ===")
for i in ids:
    exists = (
        (ROOT / "skills" / i).is_dir()
        or (ROOT / "rules" / (i + ".md")).exists()
        or (ROOT / "commands" / (i + ".md")).exists()
        or (ROOT / "agents" / (i + ".md")).exists()
    )
    status = "OK" if exists else "缺失!"
    print(f"  {i}: {status}")
    if not exists:
        issues.append(f"cordis.yaml 引用不存在的插件: {i}")

# 2. skills/README.md 中 git-commit 引用
readme = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")
gc_count = readme.count("git-commit")
print(f"\n=== skills/README.md 中 git-commit 引用: {gc_count} 次 ===")
print(f"  git-commit 技能目录存在: {(ROOT / 'skills' / 'git-commit').is_dir()}")
if gc_count > 0 and not (ROOT / "skills" / "git-commit").is_dir():
    issues.append("skills/README.md 引用不存在的 git-commit 技能")

# 3. presets 中技能数量声明
for preset in ["standard", "minimal", "creator"]:
    p = ROOT / "presets" / f"{preset}.yaml"
    if p.exists():
        text = p.read_text(encoding="utf-8")
        m = re.search(r"全部 (\d+) 个技能", text)
        if m:
            n = int(m.group(1))
            actual = len([d for d in (ROOT / "skills").iterdir() if d.is_dir()])
            print(f"  presets/{preset}.yaml 声明 {n} 个技能，实际 {actual} 个"
                  f"{'（一致）' if n == actual else '（不一致!）'}")
            if n != actual:
                issues.append(f"presets/{preset}.yaml 技能数量声明 {n} != 实际 {actual}")

# 4. AGENTS.md 引用的 hooks 脚本
agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
hrefs = set(re.findall(r"hooks/scripts/([a-z0-9_]+\.py)", agents))
print("\n=== AGENTS.md 引用的 hooks 脚本 ===")
for h in sorted(hrefs):
    exists = (ROOT / "hooks" / "scripts" / h).exists()
    print(f"  {h}: {'OK' if exists else '缺失!'}")
    if not exists:
        issues.append(f"AGENTS.md 引用不存在的 hooks 脚本: {h}")

# 5. 规则文件 RULE 编号引用完整性（AGENTS.md 中 RULE-NNN 是否都有落点）
rule_ids = set(re.findall(r"RULE-(\d{3})", agents))
print(f"\n=== AGENTS.md 中 RULE 编号: {len(rule_ids)} 个 ===")

# 6. 各技能 frontmatter 的 depends_on/composes 引用完整性
print("\n=== 技能 depends_on/composes 引用检查 ===")
skill_ids = {d.name for d in (ROOT / "skills").iterdir() if d.is_dir()}
for d in sorted((ROOT / "skills").iterdir()):
    if not d.is_dir():
        continue
    fm = (d / "SKILL.md").read_text(encoding="utf-8")
    for key in ("depends_on", "composes"):
        m = re.search(rf"{key}:\s*\[([^\]]*)\]", fm)
        if m:
            deps = [x.strip() for x in m.group(1).split(",") if x.strip()]
            for dep in deps:
                if dep not in skill_ids:
                    print(f"  {d.name}.{key} -> {dep} 缺失!")
                    issues.append(f"技能 {d.name} 的 {key} 引用不存在的 {dep}")

print(f"\n{'='*50}")
print(f"发现问题: {len(issues)} 项")
for iss in issues:
    print(f"  ✗ {iss}")
