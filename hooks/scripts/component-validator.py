#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
component-validator.py — 前端组件组合校验器（RULE-034/035/036）v2.0

v2.0 变更：
  - AST 解析替代正则提取（精确 JSX 树深度计算）
  - 裸 hex 值从 warning 升级为 error（当 design-tokens.yaml 已定义时）
  - 新增 forbidden 组合检测（Modal 内套 Drawer/Card 等）
  - 新增 examples.correct/incorrect 校验支持

校验范围：
  RULE-034：页面模板匹配（page-templates.yaml）
  RULE-035：组件元数据查询（components/manifest.json 的 usage/forbidden/examples）
  RULE-036：生成后组件组合校验（嵌套深度、primary 数量、token 一致性、forbidden 组合）

用法：
  python hooks/scripts/component-validator.py --validate-template --page-type list_page --components "PageHeader,FilterBar,DataTable,Pagination"
  python hooks/scripts/component-validator.py --check-component Button --context "B端后台"
  python hooks/scripts/component-validator.py --check-components src/frontend/pages/OrderList.tsx
  python hooks/scripts/component-validator.py --full-check
  python hooks/scripts/component-validator.py --cross-file-check src/frontend/pages
  python hooks/scripts/component-validator.py --full-check --output-report reports/component-validation.json

退出码：
  0 = 全部校验通过
  1 = 校验失败（需修复）
  2 = 脚本执行错误
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    yaml = None


# ──────────────────────────────────────────────
# 路径常量
# ──────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
PAGE_TEMPLATES_PATH = ROOT / "rules" / "page-templates.yaml"
MANIFEST_PATH = ROOT / "components" / "manifest.json"
DESIGN_TOKENS_PATH = ROOT / "schemas" / "design-tokens.yaml"
CONTENT_GUIDELINES_PATH = ROOT / "rules" / "content-guidelines.yaml"

# 前端源码目录（用于 --full-check 扫描）
# v4.10.1：支持项目级覆盖 —— 其它项目的前端源码不在共享规则根内，硬编码共享根路径
# 会让任何项目在其自身目录运行 --full-check 时"0 文件 0 组件"静默通过（RULE-036 失效）。
# 覆盖优先级：--src-dir 参数 > COMPONENT_VALIDATOR_SRC 环境变量（os.pathsep 分隔）> 共享根默认值
FRONTEND_SOURCES_DEFAULT = [
    ROOT / "src" / "frontend" / "pages",
    ROOT / "src" / "frontend" / "components",
    ROOT / "src" / "frontend" / "app",
]


def resolve_frontend_sources(src_dir_args=None):
    """解析 --full-check 的前端源码目录（项目级覆盖，修复静默通过缺陷）"""
    candidates = [Path(d) for d in (src_dir_args or []) if d]
    env_src = os.environ.get("COMPONENT_VALIDATOR_SRC")
    if env_src:
        candidates.extend(Path(p) for p in env_src.split(os.pathsep) if p.strip())
    return candidates or FRONTEND_SOURCES_DEFAULT

# JSX 组件标签名正则（匹配 <ComponentName 或 </ComponentName>）
JSX_TAG_RE = re.compile(r"</?([A-Z][a-zA-Z0-9]*)\s")
# import 语句中的组件名
IMPORT_RE = re.compile(r"import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]")
# 裸 hex 值（排除 Tailwind 类名中的 #xxx / #xxxxxx）
HEX_RE = re.compile(r"(?<![a-zA-Z0-9_-])#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})(?![a-zA-Z0-9_-])")
# Tailwind 任意值语法中的 hex，如 bg-[#FF0000]、text-[#ff0000]（合法，放行）
# 匹配模式：- [ #hex ]（可含颜色通道 / 透明度，如 #FF0000/50）
TAILWIND_ARBITRARY_HEX_RE = re.compile(r"(?:[a-zA-Z0-9_-]+-)?\[#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})(?:/[0-9]+)?\]")


# ──────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────
@dataclass
class ValidationError:
    """校验失败项"""
    rule: str           # RULE-034 / RULE-035 / RULE-036
    severity: str       # error / warning
    component: str      # 组件名
    message: str
    location: str = ""  # 文件路径 + 行号


@dataclass
class ValidationResult:
    """校验结果汇总"""
    errors: "list" = field(default_factory=list)
    warnings: "list" = field(default_factory=list)
    files_checked: int = 0
    components_found: int = 0


# ──────────────────────────────────────────────
# AST 解析器（轻量级，无需外部依赖）
# ──────────────────────────────────────────────
class JSXASTParser:
    """
    轻量级 JSX AST 解析器。
    将 JSX 文本解析为树形结构，支持：
    - 嵌套深度计算
    - 组件标签查找
    - Props 提取
    """

    def __init__(self, source: str):
        self.source = source
        self.tokens: list[dict] = []
        self._tokenize()

    def _tokenize(self) -> None:
        """将 JSX 文本 tokenize 为标签、属性、文本节点"""
        i = 0
        while i < len(self.source):
            # 标签开始
            # 标签结束 </Component> 优先判断（在 < 分支之前）
            if self.source[i:i+2] == '</':
                end = self.source.find('>', i)
                if end == -1:
                    i += 1
                    continue
                tag_name = self.source[i+2:end].strip()
                # v4.10.1：标签名合法性校验 —— `</` 出现在注释/文本中时 find('>')
                # 会吞到真实代码的 `>`，提取出垃圾名；非法名视为普通文本，跳过继续扫描
                if tag_name and not re.match(r'^[A-Za-z_$][A-Za-z0-9_$]*$', tag_name.lstrip('/')):
                    i += 1
                    continue
                self.tokens.append({
                    'type': 'jsx-close',
                    'name': tag_name.lstrip('/'),
                    'pos': i,
                })
                i = end + 1
            # 标签开始
            elif self.source[i:i+1] == '<':
                # 自闭合标签 <Component />
                end = self.source.find('>', i)
                if end == -1:
                    i += 1
                    continue
                tag_content = self.source[i+1:end].strip()
                is_self_closing = tag_content.endswith('/')
                if is_self_closing:
                    tag_content = tag_content[:-1].strip()
                # 提取标签名和属性
                parts = tag_content.split(None, 1)
                tag_name = parts[0] if parts else ""
                # v4.10.1：标签名合法性校验 —— `<` 出现在注释/文本中时（如"出现率 1/3 < 50%）"），
                # find('>') 会吞到真实代码的 `>`，产生 "50%）" 垃圾 token 并吞掉真实开标签
                # （导致组件误报缺失 + 垃圾组件名假警告）。非法名（非标识符，含泛型
                # `Foo<Bar` 等）视为普通文本，跳过该 `<` 继续扫描。
                if tag_name and not re.match(r'^[A-Za-z_$][A-Za-z0-9_$]*$', tag_name):
                    i += 1
                    continue
                attrs_str = parts[1] if len(parts) > 1 else ""
                self.tokens.append({
                    'type': 'jsx-open',
                    'name': tag_name,
                    'self_closing': is_self_closing,
                    'attrs': attrs_str,
                    'pos': i,
                })
                i = end + 1
            else:
                i += 1

    def get_max_depth(self) -> int:
        """计算 JSX 树的最大嵌套深度"""
        max_depth = 0
        current_depth = 0
        for token in self.tokens:
            if token['type'] == 'jsx-open':
                if not token['self_closing']:
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
            elif token['type'] == 'jsx-close':
                if current_depth > 0:
                    current_depth -= 1
        return max_depth

    def get_component_counts(self) -> dict[str, int]:
        """统计各组件出现次数（仅 open 标签）"""
        counts: dict[str, int] = {}
        for token in self.tokens:
            if token['type'] == 'jsx-open' and token['name']:
                counts[token['name']] = counts.get(token['name'], 0) + 1
        return counts

    def get_nested_pairs(self) -> list[tuple[str, str]]:
        """检测 forbidden 组合（如 Modal 内套 Drawer）"""
        stack: list[str] = []
        pairs: list[tuple[str, str]] = []
        for token in self.tokens:
            if token['type'] == 'jsx-open':
                if not token['self_closing']:
                    if stack:
                        pairs.append((stack[-1], token['name']))
                    stack.append(token['name'])
            elif token['type'] == 'jsx-close':
                if stack and stack[-1] == token['name']:
                    stack.pop()
        return pairs

    def get_primary_button_count(self) -> int:
        """统计 variant='primary' 的 Button 组件数量"""
        count = 0
        for token in self.tokens:
            if token['type'] == 'jsx-open' and token['name'] == 'Button':
                if "primary" in token['attrs']:
                    count += 1
        return count

    def get_all_component_names(self) -> set[str]:
        """获取文件中所有引用的组件名"""
        names: set[str] = set()
        for token in self.tokens:
            if token['type'] == 'jsx-open' and token['name']:
                names.add(token['name'])
        return names


def parse_jsx_ast(source: str) -> JSXASTParser:
    """解析 JSX 源码，返回 AST 解析器"""
    return JSXASTParser(source)


# ──────────────────────────────────────────────
# 加载工具
# ──────────────────────────────────────────────
def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    """加载 YAML，自动剥离 Jekyll/TRAE 风格 frontmatter（--- 包裹的头部元数据）"""
    if not path.exists():
        return {}
    if yaml is None:
        print(f"警告：缺少 PyYAML，跳过 {label} 加载", file=sys.stderr)
        return {}
    text = path.read_text(encoding="utf-8")
    # 剥离 frontmatter：文件以 '---' 开头，则截断到第二个 '---'
    if text.lstrip().startswith("---"):
        lines = text.splitlines()
        # 找到第一个分隔符后的下一个 '---'
        sep_count = 0
        end_idx = None
        for idx, line in enumerate(lines):
            if line.strip() == "---":
                sep_count += 1
                if sep_count == 2:
                    end_idx = idx
                    break
        if end_idx is not None:
            body = "\n".join(lines[end_idx + 1:])
        else:
            body = text
    else:
        body = text
    data = yaml.safe_load(body)
    return data if isinstance(data, dict) else {}


def load_page_templates() -> dict[str, Any]:
    """加载 page-templates.yaml。
    page-templates.yaml 是 Markdown 文档，YAML 定义嵌在 ```yaml fenced code block 中。
    本 loader 提取所有 fenced YAML block，并把含 page_type 的定义展开为 {page_type: {...}}。
    """
    if not PAGE_TEMPLATES_PATH.exists():
        return {}
    if yaml is None:
        print("警告：缺少 PyYAML，跳过 page-templates 校验", file=sys.stderr)
        return {}
    text = PAGE_TEMPLATES_PATH.read_text(encoding="utf-8")
    # 剥离 frontmatter
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        sep_count = 0
        body_lines: list[str] = []
        skip = True
        for line in lines:
            if line.strip() == "---":
                sep_count += 1
                if sep_count == 1:
                    continue  # 跳过开头分隔符
                if sep_count == 2:
                    skip = False  # 第二个分隔符：body 开始
                    continue
            if not skip:
                body_lines.append(line)
        body = "\n".join(body_lines)
    else:
        body = text

    # 提取 fenced ```yaml ... ``` 块，逐个解析并合并（只认 yaml/无标记的 YAML 块）
    result: dict[str, Any] = {}
    in_fence = False
    fence_is_yaml = False
    fence_buf: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_fence:
                # 关闭 fence，仅当标注为 yaml（或无标注）时解析
                if fence_is_yaml:
                    block_text = "\n".join(fence_buf)
                    if block_text.strip():
                        try:
                            block = yaml.safe_load(block_text)
                            if isinstance(block, dict):
                                # 含 page_type 的定义按 page_type 展开为顶层 key
                                if "page_type" in block and isinstance(block["page_type"], str):
                                    result[block["page_type"]] = block
                                else:
                                    # 通用规则块按原样展开
                                    for k, v in block.items():
                                        if k not in result or not isinstance(result.get(k), dict):
                                            result[k] = v
                        except Exception as e:
                            print(f"警告：page-templates 代码块解析失败：{e}", file=sys.stderr)
                fence_buf = []
                in_fence = False
                fence_is_yaml = False
            else:
                in_fence = True
                fence_is_yaml = stripped in ("```yaml", "```yml", "```")
            continue
        if in_fence:
            fence_buf.append(line)
    return result


def load_manifest() -> dict[str, Any]:
    """加载 components/manifest.json"""
    if not MANIFEST_PATH.exists():
        print("错误：components/manifest.json 不存在", file=sys.stderr)
        return {}
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    return json.loads(text)


def load_design_tokens() -> dict[str, Any]:
    """加载设计令牌（返回完整结构，用于 hex 值校验）"""
    return _load_yaml(DESIGN_TOKENS_PATH, "design-tokens")


def load_content_guidelines() -> dict[str, Any]:
    """加载内容指南（RULE-035 扩展）"""
    return _load_yaml(CONTENT_GUIDELINES_PATH, "content-guidelines")


def get_all_token_names(tokens: dict[str, Any]) -> set[str]:
    """从 design-tokens.yaml 中提取所有 token 名称"""
    names: set[str] = set()
    for category, values in tokens.items():
        if isinstance(values, dict):
            names.update(values.keys())
    return names


# ──────────────────────────────────────────────
# RULE-034：页面模板匹配
# ──────────────────────────────────────────────
def validate_page_template(page_type: str, components: list[str]) -> ValidationResult:
    """RULE-034：校验组件组合是否匹配页面模板"""
    result = ValidationResult()
    templates = load_page_templates()

    if not templates:
        result.warnings.append(ValidationError(
            rule="RULE-034", severity="warning", component="",
            message="page-templates.yaml 为空或不存在，跳过模板匹配校验"
        ))
        return result

    # 查找页面模板
    page_template = None
    for key, value in templates.items():
        if isinstance(value, dict) and value.get("page_type") == page_type:
            page_template = value
            break

    if page_template is None:
        result.warnings.append(ValidationError(
            rule="RULE-034", severity="warning", component="",
            message=f"未找到页面类型 '{page_type}' 的模板定义"
        ))
        return result

    # 检查 required 组件
    required = page_template.get("required", [])
    required_names = {r["component"] if isinstance(r, dict) else r for r in required}
    missing = required_names - set(components)
    for comp in missing:
        result.errors.append(ValidationError(
            rule="RULE-034", severity="error", component=comp,
            message=f"页面模板 '{page_type}' 要求必需组件 '{comp}' 缺失"
        ))

    # 检查 forbidden 组件
    forbidden = page_template.get("forbidden", [])
    forbidden_names = {f["component"] if isinstance(f, dict) else f for f in forbidden}
    violations = forbidden_names & set(components)
    for comp in violations:
        reason = ""
        for f in forbidden:
            if isinstance(f, dict) and f.get("component") == comp:
                reason = f.get("reason", "")
                break
        msg = f"页面模板 '{page_type}' 禁止使用组件 '{comp}'"
        if reason:
            msg += f"（原因：{reason}）"
        result.errors.append(ValidationError(
            rule="RULE-034", severity="error", component=comp,
            message=msg
        ))

    return result


# ──────────────────────────────────────────────
# RULE-035：组件元数据查询
# ──────────────────────────────────────────────
def validate_component_metadata(component_name: str, context: str = "") -> ValidationResult:
    """RULE-035：校验组件元数据（usage/forbidden/examples）"""
    result = ValidationResult()
    manifest = load_manifest()

    if not manifest:
        result.warnings.append(ValidationError(
            rule="RULE-035", severity="warning", component=component_name,
            message="manifest.json 为空，跳过元数据校验"
        ))
        return result

    # 收集所有组件
    all_components: dict[str, dict] = {}
    for category in manifest.get("categories", []):
        for comp in category.get("components", []):
            all_components[comp["name"]] = comp
    for comp in manifest.get("shadcn_registry", {}).get("base_components", []):
        all_components[comp["name"]] = comp

    if component_name not in all_components:
        result.warnings.append(ValidationError(
            rule="RULE-035", severity="warning", component=component_name,
            message=f"组件 '{component_name}' 未在 manifest.json 中定义，无法校验元数据"
        ))
        return result

    comp = all_components[component_name]

    # 检查 forbidden
    forbidden = comp.get("forbidden", [])
    for forbid_item in forbidden:
        if context and forbid_item.lower() in context.lower():
            result.errors.append(ValidationError(
                rule="RULE-035", severity="error", component=component_name,
                message=f"组件 '{component_name}' 在上下文 '{context}' 中被禁止：{forbid_item}"
            ))

    # 检查 depth_limit
    depth_limit = comp.get("depth_limit", 1)
    if depth_limit < 0:
        result.errors.append(ValidationError(
            rule="RULE-035", severity="error", component=component_name,
            message=f"组件 '{component_name}' 的 depth_limit 无效：{depth_limit}"
        ))

    # 检查 examples（如果有 incorrect 示例，输出建议）
    examples = comp.get("examples", {})
    if examples.get("incorrect"):
        result.warnings.append(ValidationError(
            rule="RULE-035", severity="warning", component=component_name,
            message=f"组件 '{component_name}' 有以下错误使用示例（避免）：{examples['incorrect']}"
        ))

    return result


# ──────────────────────────────────────────────
# RULE-036：生成后组件组合校验（AST 版）
# ──────────────────────────────────────────────
def validate_component_combination(filepath: str) -> ValidationResult:
    """RULE-036：使用 AST 校验单个文件的组件组合"""
    result = ValidationResult()
    manifest = load_manifest()
    design_tokens = load_design_tokens()
    token_names = get_all_token_names(design_tokens) if design_tokens else set()

    path = Path(filepath)
    if not path.exists():
        result.warnings.append(ValidationError(
            rule="RULE-036", severity="warning", component="",
            message=f"文件不存在：{filepath}"
        ))
        return result

    text = path.read_text(encoding="utf-8")

    # ── AST 解析 ──
    ast = parse_jsx_ast(text)
    result.files_checked = 1

    # 1. 嵌套深度校验
    max_depth = ast.get_max_depth()
    global_max_depth = manifest.get("validation_rules", {}).get("max_nested_depth", 3)
    if max_depth > global_max_depth:
        result.errors.append(ValidationError(
            rule="RULE-036", severity="error", component="JSX",
            message=f"文件 {filepath} 中 JSX 嵌套深度为 {max_depth}，超过限制 {global_max_depth}"
        ))

    # 2. Primary 按钮数量校验
    primary_count = ast.get_primary_button_count()
    max_primary = manifest.get("validation_rules", {}).get("max_primary_per_screen", 1)
    if primary_count > max_primary:
        result.errors.append(ValidationError(
            rule="RULE-036", severity="error", component="Button",
            message=f"文件 {filepath} 中 primary 按钮数量为 {primary_count}，超过限制 {max_primary}"
        ))

    # 3. 组件名白名单校验
    ast_components = ast.get_all_component_names()
    allowed_components = set()
    for category in manifest.get("categories", []):
        for comp in category.get("components", []):
            allowed_components.add(comp["name"])
    for comp in manifest.get("shadcn_registry", {}).get("base_components", []):
        allowed_components.add(comp["name"])

    # 允许标准 React 组件和内置 HTML 元素
    builtin_components = {"div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
                          "a", "button", "input", "select", "textarea", "form",
                          "ul", "ol", "li", "table", "tr", "td", "th", "thead",
                          "tbody", "tfoot", "img", "svg", "path", "g", "circle",
                          "rect", "line", "polyline", "polygon", "iframe", "video",
                          "audio", "source", "canvas", "label", "fieldset", "legend",
                          "section", "article", "header", "footer", "nav", "main",
                          "aside", "details", "summary", "dialog", "slot"}
    unknown_components = [c for c in ast_components
                          if c not in allowed_components
                          and c not in builtin_components
                          and not c.startswith("use")  # hooks
                          and not c.startswith("get")  # getters
                          ]
    for comp in unknown_components[:5]:
        result.warnings.append(ValidationError(
            rule="RULE-036", severity="warning", component=comp,
            message=f"组件 '{comp}' 未在 manifest.json 白名单中，可能为自研组件"
        ))

    # 4. 图标库单例校验
    icon_library_re = re.compile(r"from\s+['\"](@?lucide|@?tabler-icons|phosphor-react|hugeicons)['\"]")
    icon_libraries = set(icon_library_re.findall(text))
    if len(icon_libraries) > 1:
        result.errors.append(ValidationError(
            rule="RULE-036", severity="error", component="Icons",
            message=f"文件 {filepath} 中混用了多个图标库：{icon_libraries}"
        ))

    # 5. 图表库单例校验
    chart_library_re = re.compile(r"from\s+['\"](recharts|echarts|@ant-design/charts|@antv/g6|datav-react)['\"]")
    chart_libraries = set(chart_library_re.findall(text))
    if len(chart_libraries) > 1:
        result.errors.append(ValidationError(
            rule="RULE-036", severity="error", component="Charts",
            message=f"文件 {filepath} 中混用了多个图表库：{chart_libraries}"
        ))

    # 6. 裸 hex 值校验（升级为 error）
    if token_names:
        # 裸 hex 检测：
        #   - className/class 属性内的 hex（Tailwind 任意值，如 bg-[#FF0000]）→ 放行
        #   - 其余位置（style={}、JS 表达式、CSS 变量、模板字符串）→ 视为裸值，必须改用 token
        hex_in_code = []
        for line_no, line in enumerate(text.splitlines(), 1):
            # 找出 Tailwind 任意值 hex 的原文（用于从行内剔除）
            tailwind_hex = set(TAILWIND_ARBITRARY_HEX_RE.findall(line))
            matches = HEX_RE.findall(line)
            if not matches:
                continue
            # 该行属于纯 className 声明（属性赋值里的 hex 全是 Tailwind 类）
            if re.search(r"(?:className|class)=[\s]*[`'\"]", line) and not re.search(r"style={|=\s*\{", line):
                continue
            for m in matches:
                if m in tailwind_hex:
                    continue
                hex_in_code.append((m, line_no))

        if hex_in_code:
            result.errors.append(ValidationError(
                rule="RULE-036", severity="error", component="Tokens",
                message=f"文件 {filepath} 中发现 {len(hex_in_code)} 处裸 hex 值，必须使用设计令牌（design-tokens.yaml 已定义）。"
                        f"示例：将 {hex_in_code[0][0]} 替换为对应的 token 名称"
            ))

    # 7. Forbidden 组合校验（Modal 内套 Drawer/Card）
    forbidden_combinations = [
        ("Modal", "Modal"),    # Modal 内套 Modal
        ("Modal", "Drawer"),   # Modal 内套 Drawer
        ("Card", "Card"),      # Card 内套 Card
        ("Drawer", "Drawer"),  # Drawer 内套 Drawer
        ("Tabs", "Tabs"),      # TabPanel 内套 Tabs
    ]
    nested_pairs = ast.get_nested_pairs()
    for parent, child in nested_pairs:
        for fp, fc in forbidden_combinations:
            if parent == fp and child == fc:
                result.errors.append(ValidationError(
                    rule="RULE-036", severity="error", component=f"{parent}+{child}",
                    message=f"文件 {filepath} 中存在禁止的组合：{parent} 内嵌套 {child}"
                ))

    # 8. 组件元数据 depth_limit 校验
    comp_counts = ast.get_component_counts()
    for comp_name, count in comp_counts.items():
        if comp_name in manifest.get("shadcn_registry", {}).get("base_components", []) or \
           any(c["name"] == comp_name for cat in manifest.get("categories", []) for c in cat.get("components", [])):
            comp_data = None
            for cat in manifest.get("categories", []):
                for c in cat.get("components", []):
                    if c["name"] == comp_name:
                        comp_data = c
                        break
                if comp_data:
                    break
            if not comp_data:
                for c in manifest.get("shadcn_registry", {}).get("base_components", []):
                    if c["name"] == comp_name:
                        comp_data = c
                        break
            if comp_data:
                depth_limit = comp_data.get("depth_limit", 1)
                # 如果组件出现在超过 depth_limit 的深度层级，发出警告
                if count > 1 and depth_limit == 0:
                    result.warnings.append(ValidationError(
                        rule="RULE-036", severity="warning", component=comp_name,
                        message=f"组件 '{comp_name}' 的 depth_limit=0（容器组件），但在文件中使用 {count} 次，建议扁平化"
                    ))

    # 9. 文案规范校验（content-guidelines.yaml，v4.10.1 接入原未使用的 load_content_guidelines）
    # 可确定性执行子集：copy_length.button / copy_length.page_title 的字符数上限
    # （button_verbs 动词开头、state_copy 等语义规则属提示层，由 Agent 按规范执行）
    guidelines = load_content_guidelines()
    if guidelines:
        copy_length = guidelines.get("copy_length", {})
        max_btn = copy_length.get("button", {}).get("max_chars")
        max_title = copy_length.get("page_title", {}).get("max_chars")
        if max_btn:
            for m in re.finditer(r"<(button|Button)(?:[^>]*)(?<!/)>([^<>]*)</\1>", text):
                btn_text = m.group(2).strip()
                if btn_text and len(btn_text) > max_btn:
                    result.warnings.append(ValidationError(
                        rule="RULE-036", severity="warning", component="Button",
                        message=f"文件 {filepath} 中按钮文本 '{btn_text}' 长度 {len(btn_text)} 超过 {max_btn} 字符"
                                f"（content-guidelines.yaml copy_length.button），应动词开头并精简"
                    ))
        if max_title:
            for m in re.finditer(r"<PageHeader[^>]*title=[\"']([^\"']*)[\"']", text):
                title_text = m.group(1).strip()
                if title_text and len(title_text) > max_title:
                    result.warnings.append(ValidationError(
                        rule="RULE-036", severity="warning", component="PageHeader",
                        message=f"文件 {filepath} 中页面标题 '{title_text}' 长度 {len(title_text)} 超过 {max_title} 字符"
                                f"（content-guidelines.yaml copy_length.page_title），禁止空泛词"
                    ))

    result.components_found = len(ast_components)
    return result


# ──────────────────────────────────────────────
# 跨文件一致性检查（页面类型分组 + 组合漂移检测）
# ──────────────────────────────────────────────
def infer_page_type(filepath: str, templates: dict[str, Any] | None = None) -> str | None:
    """根据文件名与路径关键词推断页面类型（用于跨文件分组）。

    优先级：
      1. 页面模板 aliases 精确匹配文件名（如 admin-list -> list_page）
      2. 典型文件名词干（如 OrderList.tsx 含 'list' -> list_page）
      3. 路径中页签名（如 /settings/ /preference/ -> settings_page）
    """
    templates = templates or load_page_templates()
    stem = Path(filepath).stem.lower()
    path_lower = filepath.replace("\\", "/").lower()

    # 1. aliases 精确匹配
    for pt, cfg in templates.items():
        if not isinstance(cfg, dict):
            continue
        aliases = cfg.get("aliases", [])
        if any(a.lower() == stem or a.lower() in path_lower for a in aliases):
            return pt

    # 2. 文件名词干关键词
    stem_keywords = {
        "list": "list_page", "table": "list_page", "index": "list_page",
        "detail": "detail_page", "view": "detail_page",
        "form": "form_page", "create": "form_page", "edit": "form_page", "new": "form_page",
        "settings": "settings_page", "preference": "settings_page",
        "dashboard": "dashboard_page", "board": "dashboard_page",
    }
    for kw, kind in stem_keywords.items():
        if kw in stem:
            return kind

    return None


def infer_page_type_from_components(components: set[str]) -> str | None:
    """根据组件集合推断页面类型（文件名无法判断时兜底）"""
    signature = {
        "list_page": {"DataTable", "FilterBar"},
        "detail_page": {"DetailCard"},
        "form_page": {"Form"},
        "dashboard_page": {"DashboardGrid"},
        "settings_page": {"SettingsLayout", "SettingsSection"},
        "error_page": {"ErrorState"},
    }
    best, best_score = None, 0
    for kind, comps in signature.items():
        score = len(comps & components)
        if score > best_score:
            best, best_score = kind, score
    return best if best_score > 0 else None


def validate_cross_file_consistency(directory: str) -> ValidationResult:
    """跨文件一致性检查（RULE-036 扩展）。

    按页面类型对目录下所有 .tsx/.ts 文件分组，检测：
      1. 组合漂移：同类型页面使用了相互不一致的组件组合
         （如列表页 A 用 Drawer 删除、列表页 B 用 Modal 删除）
      2. Mobile 判定：无法归组但组件集合存在 -> 归入兜底组
      3. 只对同组内 >=2 个文件时做一致性判定（单一文件无参照）
    """
    result = ValidationResult()
    templates = load_page_templates()

    dir_path = Path(directory)
    if not dir_path.exists():
        result.warnings.append(ValidationError(
            rule="RULE-036", severity="warning", component="",
            message=f"跨文件检查目录不存在：{directory}"
        ))
        return result

    files = sorted(dir_path.rglob("*.tsx")) + sorted(dir_path.rglob("*.ts"))
    # 跳过测试/spec 文件
    files = [f for f in files if "test" not in f.stem.lower() and "spec" not in f.stem.lower()]
    if not files:
        result.warnings.append(ValidationError(
            rule="RULE-036", severity="warning", component="",
            message=f"跨文件检查目录 {directory} 下无 tsx/ts 文件"
        ))
        return result

    # 按页面类型分组 {page_type: [(file, components)]}
    groups: dict[str, list[tuple[Path, set[str]]]] = {}
    for f in files:
        try:
            ast = parse_jsx_ast(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        comps = ast.get_all_component_names()
        pt = infer_page_type(str(f), templates) or infer_page_type_from_components(comps) or "unknown"
        groups.setdefault(pt, []).append((f, comps))

    for pt, entries in groups.items():
        if len(entries) < 2 or pt == "unknown":
            continue

        # 主流组合：统计每个组件在该类型页面中的出现率
        total = len(entries)
        comp_occurrence: dict[str, int] = {}
        for _, comps in entries:
            for c in comps:
                comp_occurrence[c] = comp_occurrence.get(c, 0) + 1

        # 漂移检测 1：同一类型页面，某组件出现率 > 50% 却在某个文件中缺失
        # （= 该页面缺了同类型页面的主流组件）
        for file_path, comps in entries:
            missing_main = [c for c, occ in comp_occurrence.items()
                            if occ > total * 0.5 and c not in comps and c not in {"div", "span"}]
            for c in missing_main[:5]:
                result.warnings.append(ValidationError(
                    rule="RULE-036", severity="warning", component=pt,
                    message=f"跨文件不一致：页面类型 '{pt}' 的主流组件 '{c}'（出现率 {comp_occurrence[c]}/{total}）在 {entry_name(directory, file_path)} 中缺失"
                ))

        # 漂移检测 2：同类型页面，出现率 < 50% 却在个别文件出现（孤立用法）
        for file_path, comps in entries:
            minority_comps = [c for c in comps
                              if comp_occurrence.get(c, 0) < total * 0.5
                              and c not in {"div", "span", "Map", "href"}]
            for c in minority_comps[:3]:
                result.warnings.append(ValidationError(
                    rule="RULE-036", severity="warning", component=pt,
                    message=f"跨文件不一致：组件 '{c}' 仅出现在 {entry_name(directory, file_path)}，与同类型 '{pt}' 页面组合偏离"
                ))

        # 漂移检测 3：Forbidden 组合在个别文件出现（用模板 forbidden 校验）
        template_cfg = templates.get(pt, {})
        forbidden = template_cfg.get("forbidden", []) if isinstance(template_cfg, dict) else []
        forbidden_names = {f["component"] if isinstance(f, dict) else f for f in forbidden}
        for file_path, comps in entries:
            violated = forbidden_names & comps
            for c in violated:
                result.errors.append(ValidationError(
                    rule="RULE-036", severity="error", component=pt,
                    message=f"跨文件违规：页面类型 '{pt}' 禁止组件 '{c}'，但出现在 {entry_name(directory, file_path)}"
                ))

    result.files_checked = len(files)
    return result


def entry_name(base_dir: str, p: Path) -> str:
    """返回相对 base 目录的短路径，便于报告定位"""
    try:
        return str(p.relative_to(base_dir))
    except ValueError:
        return str(p)


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="前端组件组合校验器 v2.0（RULE-034/035/036）"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--validate-template",
        action="store_true",
        help="RULE-034：校验页面模板匹配"
    )
    group.add_argument(
        "--check-component",
        metavar="COMPONENT",
        help="RULE-035：校验单个组件元数据"
    )
    group.add_argument(
        "--check-components",
        metavar="FILE",
        help="RULE-036：校验单个文件的组件组合"
    )
    group.add_argument(
        "--full-check",
        action="store_true",
        help="RULE-036：全量校验所有前端文件（其它项目配合 --src-dir 指定源码目录）"
    )
    parser.add_argument(
        "--src-dir",
        metavar="DIR",
        action="append",
        help="--full-check 前端源码目录（项目级覆盖，可多次指定；也可用环境变量 COMPONENT_VALIDATOR_SRC，os.pathsep 分隔）"
    )
    group.add_argument(
        "--cross-file-check",
        metavar="DIR",
        help="RULE-036：跨文件一致性检查（目录，检测同类型页面组合漂移）"
    )
    parser.add_argument(
        "--page-type",
        metavar="TYPE",
        help="页面类型（用于 --validate-template）"
    )
    parser.add_argument(
        "--components",
        metavar="COMPS",
        help="组件列表，逗号分隔（用于 --validate-template）"
    )
    parser.add_argument(
        "--context",
        metavar="CTX",
        help="组件使用上下文（用于 --check-component）"
    )
    parser.add_argument(
        "--output-report",
        metavar="FILE",
        help="输出 JSON 报告到指定文件"
    )

    args = parser.parse_args()

    total_result = ValidationResult()

    try:
        if args.validate_template:
            if not args.page_type:
                print("错误：--validate-template 需要 --page-type 参数", file=sys.stderr)
                return 2
            comps = args.components.split(",") if args.components else []
            result = validate_page_template(args.page_type, comps)
            total_result.errors.extend(result.errors)
            total_result.warnings.extend(result.warnings)

        elif args.check_component:
            result = validate_component_metadata(
                args.check_component,
                args.context or ""
            )
            total_result.errors.extend(result.errors)
            total_result.warnings.extend(result.warnings)

        elif args.check_components:
            result = validate_component_combination(args.check_components)
            total_result.errors.extend(result.errors)
            total_result.warnings.extend(result.warnings)
            total_result.files_checked = result.files_checked
            total_result.components_found = result.components_found

        elif args.full_check:
            src_dirs = resolve_frontend_sources(args.src_dir)
            scanned_any = False
            for src_dir in src_dirs:
                if not src_dir.exists():
                    continue
                for tsx_file in sorted(src_dir.rglob("*.tsx")):
                    scanned_any = True
                    result = validate_component_combination(str(tsx_file))
                    total_result.errors.extend(result.errors)
                    total_result.warnings.extend(result.warnings)
                    total_result.files_checked += result.files_checked
                    total_result.components_found += result.components_found

            for src_dir in src_dirs:
                if not src_dir.exists():
                    continue
                for ts_file in sorted(src_dir.rglob("*.ts")):
                    if "test" in str(ts_file).lower() or "spec" in str(ts_file).lower():
                        continue
                    scanned_any = True
                    result = validate_component_combination(str(ts_file))
                    total_result.errors.extend(result.errors)
                    total_result.warnings.extend(result.warnings)
                    total_result.files_checked += result.files_checked
                    total_result.components_found += result.components_found

            if not scanned_any:
                # v4.10.1：0 文件不再是静默通过 —— 明确告警并给出覆盖方式
                total_result.warnings.append(ValidationError(
                    rule="RULE-036",
                    severity="warning",
                    component="",
                    message=(
                        "全量校验未扫描到任何前端文件（源目录不存在或为空）："
                        + ", ".join(str(d) for d in src_dirs)
                        + " — 其它项目请用 --src-dir <项目前端目录> 或环境变量 "
                        + "COMPONENT_VALIDATOR_SRC 指定源码位置，避免静默通过"
                    ),
                ))

        elif args.cross_file_check:
            result = validate_cross_file_consistency(args.cross_file_check)
            total_result.errors.extend(result.errors)
            total_result.warnings.extend(result.warnings)
            total_result.files_checked = result.files_checked
            total_result.components_found = result.components_found

        # 输出结果
        if total_result.warnings:
            print(f"\n⚠ 组件校验警告（{len(total_result.warnings)} 项）:")
            for w in total_result.warnings[:20]:
                loc = f" [{w.location}]" if w.location else ""
                print(f"  [{w.rule}] {w.message}{loc}")
            if len(total_result.warnings) > 20:
                print(f"  ... 其余 {len(total_result.warnings) - 20} 项省略")

        if total_result.errors:
            print(f"\n✗ 组件校验失败（{len(total_result.errors)} 项）:")
            for e in total_result.errors:
                loc = f" [{e.location}]" if e.location else ""
                print(f"  [{e.rule}] {e.message}{loc}")
            print(f"\n文件检查：{total_result.files_checked} | 组件发现：{total_result.components_found}")
        else:
            print(f"\n✓ 组件校验通过（{total_result.files_checked} 文件，{total_result.components_found} 组件）")

        # 输出报告
        if args.output_report:
            import datetime
            report = {
                "timestamp": datetime.datetime.now().isoformat(),
                "errors": [
                    {"rule": e.rule, "severity": e.severity, "component": e.component,
                     "message": e.message, "location": e.location}
                    for e in total_result.errors
                ],
                "warnings": [
                    {"rule": w.rule, "severity": w.severity, "component": w.component,
                     "message": w.message, "location": w.location}
                    for w in total_result.warnings
                ],
                "summary": {
                    "files_checked": total_result.files_checked,
                    "components_found": total_result.components_found,
                    "errors": len(total_result.errors),
                    "warnings": len(total_result.warnings),
                }
            }
            report_path = Path(args.output_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\n报告已输出至：{report_path}")

        return 1 if total_result.errors else 0

    except Exception as e:
        print(f"错误：校验脚本执行失败：{e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
