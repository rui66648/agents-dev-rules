import os, sys
import sys

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
# 仓库根目录 = 本脚本所在目录的上一级（不依赖任何绝对路径，可随仓迁移）
RULES_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RULES_ROOT, "scripts"))
# Import the audit functions
import importlib.util
spec = importlib.util.spec_from_file_location("audit", os.path.join(RULES_ROOT, "scripts", "rules-audit.py"))
# Just test the find_references function directly
import os, re

# 扫描范围：仓库自身 + 其父目录（父目录通常是多仓工作区容器根）
PROJECTS_ROOT = os.path.dirname(RULES_ROOT)

def find_references(filepath, target):
    results = []
    base_name = os.path.basename(target).replace('.md', '')
    patterns = [
        target,
        target.replace('.md', ''),
        os.path.basename(target),
        os.path.basename(target).replace('.md', ''),
        base_name,
    ]
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

# Test with hotl-contracts (short name from index.md)
results = find_references("rules/hotl-contracts.md", "rules/hotl-contracts.md")
print(f"hotl-contracts references: {len(results)} found")
for r in results[:5]:
    print(f"  {r[0]} (L{r[1]}): {r[2][:60]}")

# Test with security-rules
results = find_references("rules/security-rules.md", "rules/security-rules.md")
print(f"security-rules references: {len(results)} found")
for r in results[:5]:
    print(f"  {r[0]} (L{r[1]}): {r[2][:60]}")

# Test applies_to frontmatter
rules_dir = os.path.join(RULES_ROOT, "rules")
with_fm = 0
for f in sorted(os.listdir(rules_dir)):
    if not f.endswith('.md') or f.startswith('_'):
        continue
    fpath = os.path.join(rules_dir, f)
    with open(fpath, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if content.startswith('---') and 'applies_to' in content:
        with_fm += 1
print(f"Rules with applies_to frontmatter: {with_fm}/22")
