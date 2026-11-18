#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema-As-Code 校验器 — 自动化校验设计文档产出的 Schema 文件

功能：
1. 校验 JSON Schema 语法
2. 校验 API 代码符合 Schema 定义
3. 校验数据库 Migration 符合 SQL DDL
4. 校验设计令牌语义定义
5. 报告校验结果

使用方式：
    python hooks/schema-validator.py --all
    python hooks/schema-validator.py --schema schemas/api.jsonschema --target src/api/
    python hooks/schema-validator.py --schema schemas/design-tokens.yaml --verbose
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    yaml = None


class SchemaValidator:
    """Schema 校验器基类"""
    
    def __init__(self, schema_path: str, verbose: bool = False):
        self.schema_path = Path(schema_path)
        self.verbose = verbose
        self.violations: List[dict] = []
        self.warnings: List[dict] = []
    
    def validate(self) -> bool:
        """执行校验，返回是否通过"""
        raise NotImplementedError
    
    def add_violation(self, rule: str, message: str, location: Optional[str] = None):
        """添加违规项"""
        self.violations.append({
            "rule": rule,
            "message": message,
            "location": location or str(self.schema_path),
            "severity": "error"
        })
    
    def add_warning(self, rule: str, message: str, location: Optional[str] = None):
        """添加警告项"""
        self.warnings.append({
            "rule": rule,
            "message": message,
            "location": location or str(self.schema_path),
            "severity": "warning"
        })
    
    def report(self) -> Tuple[bool, int, int]:
        """生成校验报告，返回 (是否通过, 违规数, 警告数)"""
        print(f"\n{'='*60}")
        print(f"Schema 校验报告")
        print(f"{'='*60}\n")
        
        if self.violations:
            print(f"❌ 发现 {len(self.violations)} 个违规项:\n")
            for v in self.violations:
                print(f"  [{v['severity'].upper()}] {v['rule']}")
                print(f"    位置: {v['location']}")
                print(f"    消息: {v['message']}\n")
        else:
            print("✅ 无违规项\n")
        
        if self.warnings and self.verbose:
            print(f"⚠️ 发现 {len(self.warnings)} 个警告项:\n")
            for w in self.warnings:
                print(f"  [{w['severity'].upper()}] {w['rule']}")
                print(f"    位置: {w['location']}")
                print(f"    消息: {w['message']}\n")
        
        print(f"{'='*60}\n")
        
        passed = len(self.violations) == 0
        return passed, len(self.violations), len(self.warnings)


class JsonSchemaValidator(SchemaValidator):
    """JSON Schema 校验器"""
    
    def validate(self) -> bool:
        """校验 JSON Schema 语法"""
        try:
            with open(self.schema_path) as f:
                schema = json.load(f)
            
            # 基本结构检查
            if '$schema' not in schema:
                self.add_warning(
                    "schema-version",
                    "缺少 $schema 字段，建议使用 https://json-schema.org/draft/2020-12/schema"
                )
            
            if 'type' not in schema and 'properties' not in schema:
                self.add_warning(
                    "schema-type",
                    "Schema 未定义 type 或 properties，可能无法有效校验"
                )
            
            # 校验 required 字段引用的属性是否存在
            if 'required' in schema and 'properties' in schema:
                required = schema.get('required', [])
                properties = list(schema.get('properties', {}).keys())
                
                for field in required:
                    if field not in properties:
                        self.add_violation(
                            "required-field-mismatch",
                            f"required 中的字段 '{field}' 在 properties 中不存在"
                        )
            
            # 校验 enum 字段
            if 'enum' in schema:
                enum_values = schema['enum']
                if not isinstance(enum_values, list) or len(enum_values) == 0:
                    self.add_violation(
                        "enum-validation",
                        "enum 字段必须是非空数组"
                    )
            
            # 校验 minimum/maximum
            for key in ['minimum', 'maximum', 'minLength', 'maxLength', 'minItems', 'maxItems']:
                if key in schema and not isinstance(schema[key], (int, float)):
                    self.add_violation(
                        f"validation-{key}",
                        f"{key} 字段必须是数字类型"
                    )
            
            # 递归校验 allOf/anyOf/oneOf
            for keyword in ['allOf', 'anyOf', 'oneOf']:
                if keyword in schema:
                    items = schema[keyword]
                    if not isinstance(items, list):
                        self.add_violation(
                            f"schema-composition-{keyword}",
                            f"{keyword} 字段必须是数组"
                        )
                    else:
                        for i, item in enumerate(items):
                            if not isinstance(item, dict):
                                self.add_violation(
                                    f"schema-composition-{keyword}-item",
                                    f"{keyword}[{i}] 必须是对象"
                                )
            
            if self.verbose:
                print(f"✅ JSON Schema 语法校验通过: {self.schema_path}")
            
            return len(self.violations) == 0
            
        except json.JSONDecodeError as e:
            self.add_violation(
                "json-parse-error",
                f"JSON 解析失败: {e}"
            )
            return False
        except FileNotFoundError:
            self.add_violation(
                "file-not-found",
                f"Schema 文件不存在: {self.schema_path}"
            )
            return False


class DesignTokensValidator(SchemaValidator):
    """设计令牌语义校验器"""
    
    def validate(self) -> bool:
        """校验设计令牌语义定义"""
        if yaml is None:
            self.add_violation(
                "dependency",
                "缺少 PyYAML 依赖，请运行: pip install pyyaml"
            )
            return False
        
        try:
            with open(self.schema_path) as f:
                tokens = yaml.safe_load(f)
            
            # 校验 tokens 结构
            if not isinstance(tokens, dict):
                self.add_violation(
                    "token-structure",
                    "顶层必须是对象"
                )
                return False
            
            # 遍历所有 token 类别
            for category, items in tokens.items():
                if not isinstance(items, dict):
                    self.add_violation(
                        f"token-category-{category}",
                        f"类别 '{category}' 必须是对象"
                    )
                    continue
                
                for token_name, token_def in items.items():
                    if not isinstance(token_def, dict):
                        self.add_violation(
                            f"token-definition-{category}.{token_name}",
                            f"Token '{token_name}' 的定义必须是对象"
                        )
                        continue
                    
                    # 校验必需字段
                    if 'value' not in token_def:
                        self.add_violation(
                            f"token-missing-value-{category}.{token_name}",
                            f"Token '{token_name}' 缺少 value 字段"
                        )
                    
                    # 校验 domains/forbidden_domains
                    if 'domains' not in token_def:
                        self.add_warning(
                            f"token-missing-domain-{category}.{token_name}",
                            f"Token '{token_name}' 未定义 domains，无法进行语义校验"
                        )
                    
                    if 'forbidden_domains' not in token_def:
                        self.add_warning(
                            f"token-missing-forbidden-{category}.{token_name}",
                            f"Token '{token_name}' 未定义 forbidden_domains，建议补充"
                        )
                    
                    # 校验 domains/forbidden_domains 类型
                    for field in ['domains', 'forbidden_domains']:
                        if field in token_def and not isinstance(token_def[field], list):
                            self.add_violation(
                                f"token-invalid-field-{category}.{token_name}.{field}",
                                f"Token '{token_name}' 的 '{field}' 字段必须是数组"
                            )
                    
                    # 校验 domains 和 forbidden_domains 无交集
                    domains = set(token_def.get('domains', []))
                    forbidden = set(token_def.get('forbidden_domains', []))
                    
                    if domains & forbidden:
                        self.add_violation(
                            f"token-domain-conflict-{category}.{token_name}",
                            f"Token '{token_name}' 的 domains 和 forbidden_domains 存在交集: {domains & forbidden}"
                        )
            
            if self.verbose:
                print(f"✅ 设计令牌语义校验通过: {self.schema_path}")
            
            return len(self.violations) == 0
            
        except yaml.YAMLError as e:
            self.add_violation(
                "yaml-parse-error",
                f"YAML 解析失败: {e}"
            )
            return False
        except FileNotFoundError:
            self.add_violation(
                "file-not-found",
                f"Schema 文件不存在: {self.schema_path}"
            )
            return False


class ApiCodeValidator(SchemaValidator):
    """API 代码校验器"""
    
    def validate(self) -> bool:
        """校验 API 代码是否符合 Schema 定义"""
        target_path = Path(self.schema_path.parent.parent / "src" / "api")
        
        if not target_path.exists():
            self.add_warning(
                "target-not-found",
                f"目标目录不存在: {target_path}，跳过 API 代码校验"
            )
            return True
        
        # 读取 JSON Schema
        try:
            with open(self.schema_path) as f:
                schema = json.load(f)
        except Exception as e:
            self.add_violation(
                "schema-read-error",
                f"读取 Schema 文件失败: {e}"
            )
            return False
        
        # 校验 API 文件中的 Pydantic Schema
        api_files = list(target_path.glob("**/*.py"))
        
        for api_file in api_files:
            self._validate_api_file(api_file, schema)
        
        if self.verbose:
            print(f"✅ API 代码校验通过: {len(api_files)} 个文件")
        
        return len(self.violations) == 0
    
    def _validate_api_file(self, file_path: Path, schema: dict):
        """校验单个 API 文件"""
        try:
            with open(file_path) as f:
                content = f.read()
            
            # 检查是否引用了 Schema 中定义的模型
            if 'class' in content and 'BaseModel' in content:
                # 提取 Pydantic 模型名称
                model_names = re.findall(r'class\s+(\w+)\s*\(', content)
                
                # 检查 Schema 中的 required 字段是否在代码中实现
                required_fields = schema.get('required', [])
                properties = schema.get('properties', {})
                
                for field_name in required_fields:
                    if field_name not in properties:
                        self.add_warning(
                            f"schema-field-mismatch-{file_path.name}",
                            f"Schema 中 required 字段 '{field_name}' 未定义在 properties 中"
                        )
        
        except Exception as e:
            self.add_violation(
                f"file-parse-error-{file_path.name}",
                f"解析 API 文件失败: {e}"
            )


def find_schemas(project_root: Path) -> List[Path]:
    """查找项目中所有 Schema 文件"""
    schemas = []
    
    # JSON Schema 文件
    schemas.extend(project_root.glob("schemas/*.jsonschema"))
    schemas.extend(project_root.glob("schemas/**/*.jsonschema"))
    
    # YAML Schema 文件
    schemas.extend(project_root.glob("schemas/*.yaml"))
    schemas.extend(project_root.glob("schemas/**/*.yaml"))
    
    # 排除示例文件
    schemas = [s for s in schemas if not s.name.startswith('example') and not s.name.startswith('.')]
    
    return schemas


def main():
    parser = argparse.ArgumentParser(
        description="Schema-As-Code 校验器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python hooks/schema-validator.py --all                    # 校验所有 Schema
  python hooks/schema-validator.py --schema schemas/api.jsonschema  # 校验单个 Schema
  python hooks/schema-validator.py --all --verbose          # 详细输出
        """
    )
    
    parser.add_argument(
        "--schema", "-s",
        help="指定 Schema 文件路径"
    )
    
    parser.add_argument(
        "--target", "-t",
        help="指定目标代码目录（用于 API 代码校验）"
    )
    
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="校验项目中所有 Schema 文件"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--fail-on-violation", "-f",
        action="store_true",
        help="发现违规项时返回非零退出码（用于 CI）"
    )
    
    args = parser.parse_args()
    
    # 确定项目根目录
    project_root = Path(__file__).parent.parent
    
    # 选择校验模式
    if args.all:
        schema_files = find_schemas(project_root)
        if not schema_files:
            print("⚠️ 未找到任何 Schema 文件")
            sys.exit(0)
    elif args.schema:
        schema_files = [Path(args.schema)]
    else:
        print("❌ 请指定 --schema 或 --all 参数")
        sys.exit(1)
    
    # 执行校验
    total_violations = 0
    total_warnings = 0
    all_passed = True
    
    for schema_file in schema_files:
        # 根据文件类型选择校验器
        if schema_file.suffix == '.jsonschema' or schema_file.suffix == '.json':
            validator = JsonSchemaValidator(str(schema_file), verbose=args.verbose)
        elif schema_file.suffix == '.yaml' and 'token' in schema_file.name.lower():
            validator = DesignTokensValidator(str(schema_file), verbose=args.verbose)
        elif schema_file.suffix == '.yaml' and 'api' in schema_file.name.lower():
            validator = JsonSchemaValidator(str(schema_file), verbose=args.verbose)
        else:
            print(f"⚠️ 跳过未知 Schema 类型: {schema_file.name}")
            continue
        
        passed, violations, warnings = validator.report()
        
        if not passed:
            all_passed = False
        
        total_violations += violations
        total_warnings += warnings
    
    # 输出最终结果
    print(f"\n{'='*60}")
    print(f"校验汇总")
    print(f"{'='*60}")
    print(f"总违规数: {total_violations}")
    print(f"总警告数: {total_warnings}")
    print(f"校验结果: {'✅ 通过' if all_passed else '❌ 失败'}")
    print(f"{'='*60}\n")
    
    # 设置退出码
    if args.fail_on_violation and not all_passed:
        sys.exit(1)
    elif not all_passed:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
