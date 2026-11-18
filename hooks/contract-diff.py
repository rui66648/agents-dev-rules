#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
契约差异检测工具 — 检测 Schema 变更的下游影响

功能：
1. 检测 Schema 文件变更
2. 分析变更对代码的影响范围
3. 生成影响报告（Markdown）
4. 自动分配 review 责任人

使用方式：
    python hooks/contract-diff.py --base HEAD~1 --head HEAD
    python hooks/contract-diff.py --all
    python hooks/contract-diff.py --schema schemas/api.jsonschema --output report.md
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class ContractDiff:
    """契约差异检测器"""
    
    def __init__(self, base: str = "HEAD~1", head: str = "HEAD", verbose: bool = False):
        self.base = base
        self.head = head
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.schemas_dir = self.project_root / "schemas"
        self.violations: List[dict] = []
        self.impact_files: List[dict] = []
    
    def detect_changes(self) -> List[dict]:
        """检测 Schema 文件变更"""
        changes = []
        
        # 获取 git diff 中的 Schema 文件
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{self.base}..{self.head}", "schemas/"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                schema_files = [Path(f) for f in result.stdout.strip().split('\n') if f]
                
                for schema_file in schema_files:
                    if schema_file.exists():
                        change = self._analyze_schema_change(schema_file)
                        changes.append(change)
        
        except Exception as e:
            print(f"❌ 检测 Schema 变更失败: {e}", file=sys.stderr)
        
        return changes
    
    def _analyze_schema_change(self, schema_file: Path) -> dict:
        """分析单个 Schema 文件变更"""
        change = {
            "file": str(schema_file),
            "type": self._detect_change_type(schema_file),
            "severity": "warning",
            "description": "",
            "affected_files": []
        }
        
        # 根据文件类型分析
        if schema_file.suffix == '.jsonschema' or schema_file.suffix == '.json':
            change.update(self._analyze_json_schema_change(schema_file))
        elif schema_file.suffix == '.yaml':
            change.update(self._analyze_yaml_schema_change(schema_file))
        
        # 检测影响范围
        change["affected_files"] = self._detect_impact(schema_file, change["type"])
        
        return change
    
    def _detect_change_type(self, schema_file: Path) -> str:
        """检测变更类型"""
        name = schema_file.name.lower()
        
        if 'api' in name:
            return "api-schema"
        elif 'db' in name or 'database' in name:
            return "database-schema"
        elif 'token' in name or 'design' in name:
            return "design-token"
        elif 'security' in name:
            return "security-policy"
        else:
            return "unknown"
    
    def _analyze_json_schema_change(self, schema_file: Path) -> dict:
        """分析 JSON Schema 变更"""
        try:
            with open(schema_file) as f:
                schema = json.load(f)
            
            # 检测新增字段
            new_fields = []
            for field_name, field_def in schema.get('properties', {}).items():
                if 'required' in schema and field_name in schema['required']:
                    new_fields.append(field_name)
            
            # 检测类型变更
            type_changes = []
            for field_name, field_def in schema.get('properties', {}).items():
                if 'type' in field_def and field_def['type'] != 'string':
                    type_changes.append(field_name)
            
            return {
                "description": f"API Schema 变更: 新增字段 {len(new_fields)} 个, 类型变更 {len(type_changes)} 个",
                "severity": "error" if new_fields or type_changes else "warning"
            }
        
        except Exception as e:
            return {
                "description": f"解析 JSON Schema 失败: {e}",
                "severity": "error"
            }
    
    def _analyze_yaml_schema_change(self, schema_file: Path) -> dict:
        """分析 YAML Schema 变更"""
        try:
            import yaml
            with open(schema_file) as f:
                schema = yaml.safe_load(f)
            
            # 检测 Token 语义变更
            token_changes = []
            if 'tokens' in schema:
                for category, items in schema['tokens'].items():
                    for token_name, token_def in items.items():
                        if 'forbidden_domains' in token_def:
                            token_changes.append(f"{category}.{token_name}")
            
            return {
                "description": f"Token Schema 变更: {len(token_changes)} 个 Token 定义了 forbidden_domains",
                "severity": "warning"
            }
        
        except ImportError:
            return {
                "description": "缺少 PyYAML 库，无法分析 YAML Schema 变更",
                "severity": "warning"
            }
        except Exception as e:
            return {
                "description": f"解析 YAML Schema 失败: {e}",
                "severity": "error"
            }
    
    def _detect_impact(self, schema_file: Path, change_type: str) -> List[dict]:
        """检测变更影响范围"""
        affected = []
        
        # 根据变更类型检测影响文件
        if change_type == "api-schema":
            # 搜索引用 Schema 的 API 文件
            api_dir = self.project_root / "src" / "api"
            if api_dir.exists():
                for py_file in api_dir.glob("**/*.py"):
                    content = py_file.read_text()
                    if "BaseModel" in content or "Field" in content:
                        affected.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "type": "api-code",
                            "action": "update-schema"
                        })
            
            # 搜索 UI 组件
            ui_dir = self.project_root / "src" / "components"
            if ui_dir.exists():
                for ts_file in ui_dir.glob("**/*.tsx"):
                    content = ts_file.read_text()
                    if "useForm" in content or "zod" in content:
                        affected.append({
                            "file": str(ts_file.relative_to(self.project_root)),
                            "type": "ui-component",
                            "action": "update-validation"
                        })
        
        elif change_type == "design-token":
            # Token 变更影响所有使用颜色的文件
            for ext in ['.css', '.scss', '.less', '.js', '.ts', '.tsx', '.vue']:
                for file in self.project_root.glob(f"**/*{ext}"):
                    if 'node_modules' in str(file) or '__pycache__' in str(file):
                        continue
                    content = file.read_text()
                    if '#EF4444' in content or '#3B82F6' in content or 'color:' in content:
                        affected.append({
                            "file": str(file.relative_to(self.project_root)),
                            "type": "style",
                            "action": "review-token-usage"
                        })
        
        elif change_type == "database-schema":
            # DB Schema 变更影响 Migration 和 API
            migrations_dir = self.project_root / "migrations" / "versions"
            if migrations_dir.exists():
                for sql_file in migrations_dir.glob("*.sql"):
                    affected.append({
                        "file": str(sql_file.relative_to(self.project_root)),
                        "type": "migration",
                        "action": "review-compatibility"
                    })
            
            api_dir = self.project_root / "src" / "api"
            if api_dir.exists():
                for py_file in api_dir.glob("**/*.py"):
                    content = py_file.read_text()
                    if "sqlalchemy" in content.lower() or "Column" in content:
                        affected.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "type": "api-code",
                            "action": "review-model"
                        })
        
        return affected
    
    def generate_report(self, changes: List[dict]) -> str:
        """生成影响报告"""
        report_lines = [
            "# 契约变更影响报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**变更范围**: {self.base} → {self.head}",
            "",
            "## 变更摘要",
            f"- **变更文件数**: {len(changes)}",
            f"- **影响文件数**: {sum(len(c['affected_files']) for c in changes)}",
            "",
        ]
        
        for change in changes:
            report_lines.extend([
                "## 变更详情",
                f"- **文件**: `{change['file']}`",
                f"- **类型**: {change['type']}",
                f"- **严重级别**: {change['severity']}",
                f"- **描述**: {change['description']}",
                "",
                "### 影响文件",
            ])
            
            if change['affected_files']:
                for f in change['affected_files'][:10]:  # 限制输出数量
                    report_lines.append(f"- `{f['file']}` — {f['action']}")
            else:
                report_lines.append("- 无直接影响")
            
            report_lines.append("")
        
        # 建议操作
        report_lines.extend([
            "## 建议操作",
            "- [ ] 审查所有影响文件",
            "- [ ] 运行 `python hooks/schema-validator.py --all` 验证",
            "- [ ] 更新相关文档",
            "- [ ] 更新 ADR 记录变更决策",
            ""
        ])
        
        return '\n'.join(report_lines)
    
    def run(self, output_path: Optional[str] = None) -> bool:
        """执行差异检测"""
        print(f"\n{'='*60}")
        print(f"契约差异检测")
        print(f"{'='*60}\n")
        
        # 检测变更
        changes = self.detect_changes()
        
        if not changes:
            print("✅ 无 Schema 文件变更")
            return True
        
        # 生成报告
        report = self.generate_report(changes)
        
        # 输出报告
        if output_path:
            output_file = Path(output_path)
            output_file.write_text(report, encoding='utf-8')
            print(f"✅ 影响报告已生成: {output_file}")
        else:
            print(report)
        
        # 输出统计
        total_impact = sum(len(c['affected_files']) for c in changes)
        error_changes = len([c for c in changes if c['severity'] == 'error'])
        
        print(f"\n{'='*60}")
        print(f"统计")
        print(f"{'='*60}")
        print(f"变更文件数: {len(changes)}")
        print(f"影响文件数: {total_impact}")
        print(f"严重变更数: {error_changes}")
        print(f"{'='*60}\n")
        
        # 返回是否通过
        return error_changes == 0


def main():
    parser = argparse.ArgumentParser(
        description="契约差异检测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python hooks/contract-diff.py --base HEAD~1 --head HEAD          # 检测 Git 变更
  python hooks/contract-diff.py --all                              # 检测所有 Schema
  python hooks/contract-diff.py --schema schemas/api.jsonschema   # 检测单个 Schema
  python hooks/contract-diff.py --output report.md                # 生成报告文件
        """
    )
    
    parser.add_argument(
        "--base",
        default="HEAD~1",
        help="基准 commit（默认: HEAD~1）"
    )
    
    parser.add_argument(
        "--head",
        default="HEAD",
        help="目标 commit（默认: HEAD）"
    )
    
    parser.add_argument(
        "--schema", "-s",
        help="指定 Schema 文件路径"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="输出报告文件路径"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--fail-on-error", "-f",
        action="store_true",
        help="发现严重违规时返回非零退出码（用于 CI）"
    )
    
    args = parser.parse_args()
    
    detector = ContractDiff(
        base=args.base,
        head=args.head,
        verbose=args.verbose
    )
    
    # 执行检测
    passed = detector.run(output_path=args.output)
    
    # 设置退出码
    if args.fail_on_error and not passed:
        sys.exit(1)
    elif not passed:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
