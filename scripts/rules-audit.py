import os, re, sys
import sys

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 路径基于脚本位置推导，避免硬编码绝对路径（跨机/跨工具兼容）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_ROOT = os.path.dirname(SCRIPT_DIR)        # scripts/ 的父目录即为规则库根
PROJECTS_ROOT = os.path.dirname(RULES_ROOT)     # 规则库通常位于项目集合目录下

def find_references(target):
    """搜索对 target 的引用（支持短名称）"""
    base_name = os.path.basename(target).replace('.md', '')
    patterns = [
        target,
        target.replace('.md', ''),
        os.path.basename(target),
        os.path.basename(target).replace('.md', ''),
        base_name,
    ]
    results = []
    search_dirs = [RULES_ROOT, PROJECTS_ROOT]
    exclude_dirs = {
        os.path.join(RULES_ROOT, 'hooks'),
        os.path.join(RULES_ROOT, 'memory'),
        os.path.join(RULES_ROOT, 'templates'),
    }
    for search_root in search_dirs:
        if not os.path.exists(search_root):
            continue
        for root, dirs, files in os.walk(search_root):
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in exclude_dirs]
            for f in files:
                if not f.endswith('.md'):
                    continue
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    for pat in patterns:
                        if pat in content:
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if pat in line:
                                    rel = os.path.relpath(fpath, RULES_ROOT)
                                    results.append((rel, i, line.strip()[:80]))
                            break
                except:
                    pass
    return results

def audit_rule(rule_file):
    rule_path = os.path.join(RULES_ROOT, rule_file)
    if not os.path.exists(rule_path):
        print(f"错误: 规则文件不存在: {rule_path}")
        return
    print(f"\n{'='*60}")
    print(f"规则影响分析: {rule_file}")
    print(f"{'='*60}\n")
    print("### 被以下 Agent 引用")
    found = False
    agents_dir = os.path.join(RULES_ROOT, "agents")
    if os.path.isdir(agents_dir):
        for f in sorted(os.listdir(agents_dir)):
            if not f.endswith('.md'):
                continue
            fpath = os.path.join(agents_dir, f)
            with open(fpath, 'r', encoding='utf-8') as fh:
                content = fh.read()
            for pat in [rule_file, os.path.basename(rule_file), os.path.basename(rule_file).replace('.md', '')]:
                if pat in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if pat in line:
                            print(f"  - {f} (L{i}): {line.strip()[:60]}")
                    found = True
                    break
    if not found:
        print("  （无）")
    print("\n### 被以下 Skills 引用")
    found = False
    skills_dir = os.path.join(RULES_ROOT, "skills")
    if os.path.isdir(skills_dir):
        for root, dirs, files in os.walk(skills_dir):
            for f in files:
                if not f.endswith('.md'):
                    continue
                fpath = os.path.join(root, f)
                with open(fpath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                for pat in [rule_file, os.path.basename(rule_file), os.path.basename(rule_file).replace('.md', '')]:
                    if pat in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if pat in line:
                                rel = os.path.relpath(fpath, RULES_ROOT)
                                print(f"  - {rel} (L{i}): {line.strip()[:60]}")
                        found = True
                        break
    if not found:
        print("  （无）")
    print("\n### 被以下 Commands 引用")
    found = False
    cmds_dir = os.path.join(RULES_ROOT, "commands")
    if os.path.isdir(cmds_dir):
        for f in sorted(os.listdir(cmds_dir)):
            if not f.endswith('.md'):
                continue
            fpath = os.path.join(cmds_dir, f)
            with open(fpath, 'r', encoding='utf-8') as fh:
                content = fh.read()
            for pat in [rule_file, os.path.basename(rule_file), os.path.basename(rule_file).replace('.md', '')]:
                if pat in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if pat in line:
                            print(f"  - commands/{f} (L{i}): {line.strip()[:60]}")
                    found = True
                    break
    if not found:
        print("  （无）")
    print("\n### 被以下项目 tech-stack.md 引用")
    found = False
    for item in sorted(os.listdir(PROJECTS_ROOT)):
        tech_path = os.path.join(PROJECTS_ROOT, item, "tech-stack.md")
        if not os.path.exists(tech_path):
            continue
        with open(tech_path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        for pat in [rule_file, os.path.basename(rule_file), os.path.basename(rule_file).replace('.md', '')]:
            if pat in content:
                print(f"  - {item}/tech-stack.md")
                found = True
                break
    if not found:
        print("  （无）")
    print("\n### 被 AGENTS.md 引用")
    agents_md = os.path.join(RULES_ROOT, "AGENTS.md")
    if os.path.exists(agents_md):
        with open(agents_md, 'r', encoding='utf-8') as fh:
            content = fh.read()
        for pat in [rule_file, os.path.basename(rule_file), os.path.basename(rule_file).replace('.md', '')]:
            if pat in content:
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if pat in line:
                        print(f"  - AGENTS.md (L{i}): {line.strip()[:60]}")
                break
    print(f"\n{'='*60}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python rules-audit.py <规则文件>")
        print("示例: python rules-audit.py rules/security-rules.md")
        sys.exit(1)
    audit_rule(sys.argv[1])
