---
name: component-selection-rules
version: v1.2.1
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-04
description: 前端组件选型与组合校验规则（RULE-034/035/036）
applies_to:
  agents: ['frontend-developer', 'ui-designer', '全部 Agent']
  phases: ['design', 'implementation', 'review']
  project_types: ['web', 'fullstack']
  tech_stacks: ['typescript', 'react']
---
# 前端组件选型与组合校验规则

> **本文件落实**: RULE-034（组件组合前必须匹配页面模板）、RULE-035（组件选择前必须查 manifest.json）、RULE-036（生成后必须过组件校验）
> **配套文件**: `rules/page-templates.yaml`、`components/manifest.json`、`rules/content-guidelines.yaml`、`hooks/scripts/component-validator.py`、`schemas/design-tokens.yaml`

---

## 核心规则速查

| 编号 | 规则 | Enforcement 路径 | 违规后果 |
|------|------|------------------|---------|
| RULE-034 | 生成前端页面前**建议**匹配 `page-templates.yaml` 作为结构指导；生成后校验结构 | `component-validator.py --validate-template` | 结构偏离给提示，**不阻断生成** |
| RULE-035 | 组件选择前必须查 `components/manifest.json` 的 usage/forbidden | `component-validator.py --check-component` | 违规组件打回重写 |
| RULE-036 | 代码生成后必须过组件组合校验（嵌套深度、primary 数量、token 一致性） | `component-validator.py --full-check` | 手动执行（钩子未安装，见 §门禁现状） |

---

## RULE-034：页面模板匹配（强制）

### 规则内容

生成前端页面时（v1.2.0，ADR-006）：

1. **识别页面类型**：从用户意图中识别页面属于哪一类（list_page / detail_page / form_page / settings_page / dashboard_page / error_page）
2. **参考模板**：查询 `rules/page-templates.yaml` 对应模板，作为结构与组件选择的**指导**
3. **直接生成**：按模板与项目设计系统生成实现，无需"先等待确认再生成"
4. **生成后校验**：由 RULE-036 统一校验嵌套、primary 数量、token 一致性等硬约束

### 页面类型识别指南

| 用户描述关键词 | 推断页面类型 |
|--------------|-------------|
| "列表"、"表格"、"数据展示"、"搜索" | list_page |
| "详情"、"查看"、"预览" | detail_page |
| "新增"、"编辑"、"创建"、"表单" | form_page |
| "设置"、"配置"、"偏好" | settings_page |
| "看板"、"仪表板"、"数据大屏" | dashboard_page |
| "错误"、"404"、"无权限" | error_page |

### 校验命令

```bash
# 校验页面类型匹配
python hooks/scripts/component-validator.py --validate-template --page-type list_page

# 校验候选组件组合是否符合模板（--validate-combination 并不存在，
# 组合校验复用 --validate-template 的 --components 参数）
python hooks/scripts/component-validator.py --validate-template \
  --page-type list_page \
  --components PageHeader,FilterBar,DataTable,Pagination,EmptyState
```

---

## RULE-035：组件元数据查询（强制）

### 规则内容

AI 在选择每个组件前，必须查询 `components/manifest.json` 获取：

1. **usage**：该组件的使用场景（何时用）
2. **forbidden**：该组件的禁止场景（何时禁用）
3. **depth_limit**：最大嵌套深度
4. **per_screen_limits**：每屏限制（如 max_primary_buttons: 1）
5. **examples**：正确/错误用法示例（AI 严格参照 `examples.correct` 生成，规避 `examples.incorrect`）

### 查询流程

```
选择组件 → 查 manifest.json → 验证 usage 匹配 → 检查 forbidden 不命中 → 确认 depth_limit → 确认 per_screen_limits → 参照 examples.correct 生成
```

### 示例

```yaml
# 选择 Button.primary 时的查询
component: Button
variant: primary
usage_check: ✅ "所有交互按钮的基础组件" — 匹配
forbidden_check: ✅ 不在禁止列表中
depth_limit: 1 — 符合
per_screen_limits: max_primary = 1 — 当前页面已用 0 个，允许
```

```yaml
# 选择 fly-arrow-button 时的查询（违规示例）
component: fly-arrow-button
usage_check: ⚠️ "C 端营销页的 CTA 按钮" — 但当前是 B 端后台列表页
forbidden_check: ✗ 命中 "B 端后台管理页的主操作按钮"
结果: 阻断，要求改用 Button.primary
```

---

## RULE-036：生成后组件校验（强制）

### 校验项清单

| 校验项 | 检查内容 | 违规处理 |
|--------|---------|---------|
| 组件名白名单 | 所有组件名必须在 manifest.json 中 | 打回重生成 |
| 嵌套深度 | JSX 树深度 ≤ 组件 depth_limit | 要求扁平化重构 |
| Primary 按钮数量 | 每页面 primary variant ≤ 1 | 要求改为 secondary |
| Forbidden 组合 | 不得出现 forbidden 中定义的组合 | 打回重生成 |
| Token 一致性 | 颜色/间距必须使用 design token，禁止裸 hex（error） | 要求替换为 token |
| Token 层级 | 组件只允许引用 semantic/component 层 token，禁止 primitive 直用 | 要求改用组件令牌 |
| 图标库单例 | 同项目只使用 1 个图标库 | 要求统一 |
| 图表库单例 | 同页面只使用 1 个图表库 | 要求统一 |
| 空/错/载三态 | 页面必须包含 empty/loading/error 状态 | 要求补全 |
| 文案规范 | 按钮/标题/空态等文案遵循 `content-guidelines.yaml` 长度与动词规范 | 要求改写文案 |

### 校验脚本

```bash
# 校验单个文件
python hooks/scripts/component-validator.py --check-components src/frontend/pages/OrderList.tsx

# 全量校验
python hooks/scripts/component-validator.py --full-check

# 输出 JSON 报告
python hooks/scripts/component-validator.py --full-check --output-report reports/component-validation.json
```

### 退出码

| 退出码 | 含义 |
|-------|------|
| 0 | 全部校验通过 |
| 1 | 校验失败（需修复） |
| 2 | 脚本执行错误 |

### 自动化测试

`tests/test_component_validator.py` 提供 24 个单元测试，覆盖 AST 深度/计数/forbidden、RULE-034 模板匹配、RULE-035 元数据、RULE-036 负面用例与 hex 校验。运行：

```bash
pytest tests/test_component_validator.py -v
```

> 说明：被测脚本文件名 `component-validator.py` 含连字符，无法直接 import，测试用 `runpy.run_path` 加载。

### pre-commit 集成（当前未启用）

`.pre-commit-config.yaml` 中已有 `component-validator` 钩子模板，但四仓均未执行 `pre-commit install`（无 `.git/hooks/pre-commit`），且 `portal` 的钩子为 `stages: [manual]`、`files` 指向已不存在的 `demo/frontend/src/`。**当前不构成提交前阻断**，以 `rules/cicd-rules.md §门禁现状` 为准。

- 仅对变更的 `.tsx/.ts` 文件执行（`types_or: [tsx, ts]`）
- 触发命令：`python hooks/scripts/component-validator.py --check-components <file>`
- 校验失败退出码 1；在已安装钩子的仓内才阻断提交，未安装时需手动执行

### 跨文件一致性检查

`--cross-file-check <dir>` 对目录下所有 `.tsx/.ts` 按页面类型分组，检测同类型页面间的**组合漂移**：

```bash
python hooks/scripts/component-validator.py --cross-file-check src/frontend/pages
python hooks/scripts/component-validator.py --cross-file-check src/frontend/pages --output-report reports/cross-file-check.json
```

检测三类问题：
| 类型 | 严重度 | 示例 |
|------|--------|------|
| 主流组件缺失 | warning | 同类型列表页均含 `FilterBar`，个别页面缺失 |
| 孤立用法（漂移） | warning | `Modal` 仅出现在某一个列表页 |
| 模板禁止组件 | error | `list_page` 页面违规使用 `Modal` |

> **分组推断**：优先按 page-templates.yaml 的 `aliases` / 文件名词干（list/detail/form/dashboard…）；无法从文件名判断时，按组件组合特征兜底推断。唯一页面（组内 <2 个）不判定漂移。

---

## 与现有规则的集成

### 与 Schema-As-Code（RULE-030~033）的关系

- RULE-032（AI 生成代码前必须通过 Schema 校验）现在额外覆盖**前端组件组合校验**
- 新增 `components/manifest.json` 作为前端 Schema 契约文件
- `schema-gate.py` 扩展支持前端文件路径检测

### 与反模式（anti-patterns.md）的关系

- 新增"组件级反模式"章节，引用 RULE-034/035/036
- 禁止行为由人工判断升级为 hook 自动化阻断

### 与 coding-standards.md 的关系

- 前端组件规范新增"组件选型"小节，引用 page-templates.yaml
- 示例代码模板更新，展示符合RULE-034的页面结构

---

## 违规示例与修正

### 示例 1：Modal 嵌套 Modal

```tsx
// ❌ 违规：嵌套深度超限（RULE-036）
<Modal>
  <Modal>  {/* 嵌套 Modal，depth_limit=2，已超限 */}
    <Button variant="primary">确认</Button>
  </Modal>
</Modal>

// ✅ 修正：扁平化，使用 Drawer 替代内层 Modal
<Modal>
  <p>确认删除？</p>
  <Button variant="primary">确认</Button>
  <Button variant="secondary">取消</Button>
</Modal>
```

### 示例 2：多个 Primary 按钮

```tsx
// ❌ 违规：per_screen_limits.max_primary = 1（RULE-036）
<Button variant="primary">保存</Button>
<Button variant="primary">提交</Button>

// ✅ 修正：只有一个 primary，其余改为 secondary
<Button variant="primary">提交</Button>
<Button variant="secondary">保存草稿</Button>
```

### 示例 3：使用 forbidden 组件

```tsx
// ❌ 违规：fly-arrow-button 在 B 端后台禁用（RULE-035）
<FlyArrowButton>主要操作</FlyArrowButton>

// ✅ 修正：使用标准 Button
<Button variant="primary">主要操作</Button>
```

---

## ADR 记录要求

当需要突破 RULE-034/035/036 约束时，必须：

1. 在 `docs/decisions/` 下创建 ADR 文件
2. 说明突破原因、风险、替代方案
3. 获得人工审批后生效
4. 在 ADR 中记录临时豁免期限

```markdown
# ADR-NNN: 突破组件校验规则

## 背景
[为什么需要突破 RULE-034/035/036]

## 突破内容
- 规则：RULE-XXX
- 突破方式：[具体说明]
- 风险评估：[安全隐患/性能影响/可维护性]

## 审批
- 审批人：[姓名]
- 审批日期：[YYYY-MM-DD]
- 豁免期限：[YYYY-MM-DD]（最长 30 天）

## 后续行动
[如何回归合规]
```
