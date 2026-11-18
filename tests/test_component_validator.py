"""
component-validator.py 单元测试（RULE-034/035/036）

测试范围：
  - RULE-034：页面模板匹配（page-templates.yaml）
  - RULE-035：组件元数据查询（components/manifest.json）
  - RULE-036：生成后组件组合校验（AST 深度、primary 计数、forbidden 组合、hex 校验）

用法：
  pytest tests/test_component_validator.py -v
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

# 目标模块 component-validator.py 文件名含连字符，无法直接 import。
# 用 runpy.run_path 加载，它会建立正确的模块命名空间，
# 使 dataclass 能解析 ValidationError 等相对类型注解。
VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "component-validator.py"

# 注意：guard 语句 __name__ 判断在 runpy 下不触发，main() 不会自动执行
_ns = runpy.run_path(str(VALIDATOR_PATH))

# 导出供测试使用
JSXASTParser = _ns["JSXASTParser"]
load_page_templates = _ns["load_page_templates"]
load_manifest = _ns["load_manifest"]
load_design_tokens = _ns["load_design_tokens"]
validate_page_template = _ns["validate_page_template"]
validate_component_metadata = _ns["validate_component_metadata"]
validate_component_combination = _ns["validate_component_combination"]
validate_cross_file_consistency = _ns["validate_cross_file_consistency"]
infer_page_type = _ns["infer_page_type"]
ValidationResult = _ns["ValidationResult"]
ValidationError = _ns["ValidationError"]


# 测试 fixtures 目录（复用 component-validator negative 样本）
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def manifest() -> dict[str, Any]:
    """加载 components/manifest.json"""
    return load_manifest()


@pytest.fixture
def page_templates() -> dict[str, Any]:
    """加载 page-templates.yaml"""
    return load_page_templates()


@pytest.fixture
def design_tokens() -> dict[str, Any]:
    """加载 design-tokens.yaml"""
    return load_design_tokens()


@pytest.fixture
def negative_fixture() -> Path:
    """返回负面测试用例文件路径"""
    return FIXTURES_DIR / "component-validator-negative.tsx"


# =============================================================================
# Tests: JSXASTParser
# =============================================================================

class TestJSXASTParser:
    """AST 解析器单元测试"""

    def test_basic_nesting_depth(self):
        """测试基础嵌套深度计算"""
        source = """
        <div>
          <Card>
            <Button>Click</Button>
          </Card>
        </div>
        """
        ast = JSXASTParser(source)
        assert ast.get_max_depth() == 3  # div > Card > Button

    def test_self_closing_tags_no_depth_increment(self):
        """测试自闭合标签不增加深度"""
        source = """
        <div>
          <Input />
          <Button variant="primary" />
        </div>
        """
        ast = JSXASTParser(source)
        assert ast.get_max_depth() == 1  # div 是第 1 层，Input/Button 自闭合不加深

    def test_nested_forbidden_combinations(self):
        """测试 forbidden 组合检测"""
        source = """
        <Modal>
          <Drawer>
            <Button>确认</Button>
          </Drawer>
        </Modal>
        """
        ast = JSXASTParser(source)
        pairs = ast.get_nested_pairs()
        # Modal > Drawer 应该被检测到
        assert ("Modal", "Drawer") in pairs

    def test_card_nested_card_detection(self):
        """测试 Card 内套 Card 检测"""
        source = """
        <Card>
          <Card>
            <div>内容</div>
          </Card>
        </Card>
        """
        ast = JSXASTParser(source)
        pairs = ast.get_nested_pairs()
        assert ("Card", "Card") in pairs

    def test_primary_button_counting(self):
        """测试 primary 按钮计数"""
        source = """
        <div>
          <Button variant="primary">提交</Button>
          <Button variant="secondary">取消</Button>
          <Button variant="primary">再次确认</Button>
        </div>
        """
        ast = JSXASTParser(source)
        assert ast.get_primary_button_count() == 2

    def test_component_counts(self):
        """测试组件计数"""
        source = """
        <div>
          <Button>按钮1</Button>
          <Button>按钮2</Button>
          <Card>卡片</Card>
        </div>
        """
        ast = JSXASTParser(source)
        counts = ast.get_component_counts()
        assert counts["Button"] == 2
        assert counts["Card"] == 1

    def test_empty_source(self):
        """测试空源码处理"""
        ast = JSXASTParser("")
        assert ast.get_max_depth() == 0
        assert ast.get_primary_button_count() == 0
        assert ast.get_component_counts() == {}

    def test_jsx_close_tag_not_confused(self):
        """测试 </Card> 不被误判为 /Card 组件（历史 bug 回归）"""
        source = "<Card></Card>"
        ast = JSXASTParser(source)
        tokens = ast.tokens
        # 应该有 1 个 open 和 1 个 close，没有多余的 token
        open_tokens = [t for t in tokens if t["type"] == "jsx-open"]
        close_tokens = [t for t in tokens if t["type"] == "jsx-close"]
        assert len(open_tokens) == 1
        assert len(close_tokens) == 1
        assert open_tokens[0]["name"] == "Card"
        assert close_tokens[0]["name"] == "Card"


# =============================================================================
# Tests: RULE-034 页面模板匹配
# =============================================================================

class TestRule034:
    """RULE-034：页面模板匹配校验"""

    def test_list_page_valid_combination(self, page_templates):
        """测试 list_page 模板的正确组件组合"""
        result = validate_page_template("list_page", ["PageHeader", "FilterBar", "DataTable", "Pagination"])
        assert len(result.errors) == 0, f"预期无错误，实际: {[e.message for e in result.errors]}"

    def test_list_page_missing_required_component(self, page_templates):
        """测试 list_page 模板缺少必需组件 FilterBar"""
        result = validate_page_template("list_page", ["PageHeader", "DataTable", "Pagination"])
        assert len(result.errors) > 0
        assert any("FilterBar" in e.message and "必需" in e.message for e in result.errors)

    def test_list_page_forbidden_component(self, page_templates):
        """测试 list_page 模板禁止使用 Modal"""
        result = validate_page_template("list_page", ["PageHeader", "FilterBar", "DataTable", "Pagination", "Modal"])
        assert len(result.errors) > 0
        assert any("Modal" in e.message and "禁止" in e.message for e in result.errors)

    def test_unknown_page_type(self, page_templates):
        """测试未知页面类型返回警告"""
        result = validate_page_template("unknown_page_type", ["PageHeader"])
        assert len(result.warnings) > 0
        assert any("未找到" in w.message for w in result.warnings)

    def test_page_templates_loading(self, page_templates):
        """测试 page-templates.yaml 加载正常"""
        assert "list_page" in page_templates
        assert "detail_page" in page_templates
        assert "form_page" in page_templates


# =============================================================================
# Tests: RULE-035 组件元数据查询
# =============================================================================

class TestRule035:
    """RULE-035：组件元数据查询校验"""

    def test_known_component_metadata(self, manifest):
        """测试已知组件的元数据查询"""
        result = validate_component_metadata("Button", context="B端后台")
        # Button 在 B端后台 场景下不应该报错（usage 包含"所有交互按钮"）
        errors = [e for e in result.errors if "Button" in e.component]
        assert len(errors) == 0, f"预期无错误，实际: {[e.message for e in errors]}"

    def test_unknown_component_warning(self, manifest):
        """测试未知组件返回警告"""
        result = validate_component_metadata("UnknownComponent", context="")
        assert len(result.warnings) > 0
        assert any("未在 manifest.json 中定义" in w.message for w in result.warnings)

    def test_manifest_has_examples(self, manifest):
        """测试 manifest.json 包含 examples 字段"""
        shadcn = manifest.get("shadcn_registry", {}).get("base_components", [])
        for comp in shadcn[:5]:  # 检查前 5 个组件
            assert "examples" in comp, f"组件 {comp['name']} 缺少 examples 字段"
            assert "correct" in comp["examples"], f"组件 {comp['name']} 缺少 examples.correct"
            assert "incorrect" in comp["examples"], f"组件 {comp['name']} 缺少 examples.incorrect"


# =============================================================================
# Tests: RULE-036 组件组合校验
# =============================================================================

class TestRule036:
    """RULE-036：生成后组件组合校验"""

    def test_negative_fixture_all_rules(self, negative_fixture):
        """测试负面用例文件：应触发多个规则违反"""
        assert negative_fixture.exists(), f"测试 fixture 不存在: {negative_fixture}"

        result = validate_component_combination(str(negative_fixture))

        # 应该检测到以下问题：
        # 1. 嵌套深度超过限制（5 > 3）
        depth_errors = [e for e in result.errors if "嵌套深度" in e.message or "max_depth" in e.message.lower()]
        assert len(depth_errors) > 0, "应检测到嵌套深度超限"

        # 2. primary 按钮超过限制（2 > 1）
        primary_errors = [e for e in result.errors if "primary" in e.message.lower()]
        assert len(primary_errors) > 0, "应检测到 primary 按钮超限"

        # 3. Card 内套 Card
        card_card_errors = [e for e in result.errors if "Card" in e.message and "Card" in e.component]
        assert len(card_card_errors) > 0, "应检测到 Card 内套 Card 的 forbidden 组合"

        # 4. Modal 内套 Drawer
        modal_drawer_errors = [e for e in result.errors if "Modal" in e.message and "Drawer" in e.message]
        assert len(modal_drawer_errors) > 0, "应检测到 Modal 内套 Drawer 的 forbidden 组合"

        print(f"\n负面用例检测结果：")
        print(f"  错误数：{len(result.errors)}")
        print(f"  警告数：{len(result.warnings)}")
        for e in result.errors:
            print(f"    [{e.rule}] {e.message}")

    def test_valid_file_no_errors(self, tmp_path: Path):
        """测试有效文件不产生错误"""
        valid_source = """
        import { Button, Card } from '@/components/ui'

        export function GoodComponent() {
          return (
            <Card>
              <Button variant="primary">提交</Button>
            </Card>
          )
        }
        """
        test_file = tmp_path / "good-component.tsx"
        test_file.write_text(valid_source, encoding="utf-8")

        result = validate_component_combination(str(test_file))
        assert len(result.errors) == 0, f"预期无错误，实际: {[e.message for e in result.errors]}"

    def test_tailwind_arbitrary_hex_allowed(self, tmp_path: Path):
        """测试 Tailwind 任意值 hex 不应报错（如 bg-[#FF0000]）"""
        tailwind_source = """
        export function ColoredBox() {
          return (
            <div className="bg-[#FF0000] text-white p-4">
              自定义颜色
            </div>
          )
        }
        """
        test_file = tmp_path / "tailwind-hex.tsx"
        test_file.write_text(tailwind_source, encoding="utf-8")

        result = validate_component_combination(str(test_file))
        # Tailwind 任意值 hex 应被放行，不报裸 hex 错误
        hex_errors = [e for e in result.errors if "裸 hex" in e.message or "design tokens" in e.message]
        assert len(hex_errors) == 0, f"Tailwind 任意值应被放行，实际: {[e.message for e in hex_errors]}"

    def test_naked_hex_raises_error(self, tmp_path: Path):
        """测试裸 hex 值应报错（当 design-tokens.yaml 存在时）"""
        hex_source = """
        export function ColoredBox() {
          return (
            <div style={{ backgroundColor: '#FF0000' }}>
              错误用法
            </div>
          )
        }
        """
        test_file = tmp_path / "naked-hex.tsx"
        test_file.write_text(hex_source, encoding="utf-8")

        result = validate_component_combination(str(test_file))
        hex_errors = [e for e in result.errors if "裸 hex" in e.message]
        assert len(hex_errors) > 0, "应检测到裸 hex 值错误"

    def test_nonexistent_file_warning(self):
        """测试不存在的文件返回警告"""
        result = validate_component_combination("/nonexistent/path/file.tsx")
        assert len(result.warnings) > 0
        assert any("文件不存在" in w.message for w in result.warnings)


# =============================================================================
# Tests: 跨文件一致性检查
# =============================================================================

class TestCrossFileConsistency:
    """跨文件一致性检查：按页面类型分组，检测同类型页面组合漂移"""

    def test_consistent_pages_no_drift(self, tmp_path: Path):
        """一致的同类型页面不应产生漂移警告"""
        # 两个结构完全一致的列表页
        base = """
        import {{ PageHeader, FilterBar, DataTable, Pagination }} from "@/components";
        export default function {{ name }}View() {{
          return (
            <div>
              <PageHeader title="{{ name }}" />
              <FilterBar />
              <DataTable data={{ [] }} />
              <Pagination total={{ 0 }} />
            </div>
          );
        }}
        """
        for name in ["Order", "User"]:
            f = tmp_path / f"{name}List.tsx"
            f.write_text(base.replace("{{ name }}", name), encoding="utf-8")

        result = validate_cross_file_consistency(str(tmp_path))
        # 结构一致：不应报漂移/违禁错误
        assert len(result.errors) == 0, [e.message for e in result.errors]
        drift = [w for w in result.warnings if "不一致" in w.message or "偏离" in w.message]
        assert len(drift) == 0, [w.message for w in drift]

    def test_drifted_page_detected(self):
        """漂移页面（缺主流组件 + 用违禁组件）应被检测"""
        dir_path = FIXTURES_DIR / "cross-file"
        assert dir_path.exists(), "cross-file fixture 目录不存在"

        result = validate_cross_file_consistency(str(dir_path))

        # 漂移检测 1：ProductList 缺 FilterBar（主流组件）→ 警告
        drift_msgs = [w.message for w in result.warnings if "不一致" in w.message]
        assert any("FilterBar" in m and "ProductList" in m for m in drift_msgs), drift_msgs

        # 漂移检测 3：ProductList 用了 Modal（list_page 禁止）→ 错误
        forbidden_msgs = [e.message for e in result.errors if "禁止组件" in e.message]
        assert any("Modal" in m and "ProductList" in m for m in forbidden_msgs), forbidden_msgs

    def test_infer_page_type(self):
        """页面类型推断"""
        assert infer_page_type("/pages/OrderList.tsx") == "list_page"
        assert infer_page_type("/pages/UserTable.tsx") == "list_page"
        assert infer_page_type("/pages/EditProduct.tsx") == "form_page"
        assert infer_page_type("/pages/Dashboard.tsx") == "dashboard_page"
        # 无清晰关键词的文件名 -> None（交给组件兜底推断）
        assert infer_page_type("/pages/Account.tsx") is None


# =============================================================================
# Tests: 集成测试 - AST 解析准确性
# =============================================================================

class TestASTAccuracy:
    """AST 解析准确性回归测试"""

    def test_deeply_nested_structure(self):
        """测试深层嵌套结构的深度计算"""
        source = """
        <Page>
          <Section>
            <Card>
              <Modal>
                <Form>
                  <Button>Submit</Button>
                </Form>
              </Modal>
            </Card>
          </Section>
        </Page>
        """
        ast = JSXASTParser(source)
        assert ast.get_max_depth() == 6  # Page > Section > Card > Modal > Form > Button

    def test_mixed_self_closing_and_nested(self):
        """测试混合自闭合与嵌套结构"""
        source = """
        <Layout>
          <Header />
          <Sidebar>
            <MenuItem />
            <MenuItem />
          </Sidebar>
          <Footer />
        </Layout>
        """
        ast = JSXASTParser(source)
        assert ast.get_max_depth() == 2  # Layout 第1层，Sidebar 第2层；MenuItem 自闭合不加深

    def test_multiple_sibling_components(self):
        """测试多个兄弟组件"""
        source = """
        <div>
          <Button>A</Button>
          <Button>B</Button>
          <Button>C</Button>
        </div>
        """
        ast = JSXASTParser(source)
        counts = ast.get_component_counts()
        assert counts["Button"] == 3
        assert ast.get_max_depth() == 2  # div > Button


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
