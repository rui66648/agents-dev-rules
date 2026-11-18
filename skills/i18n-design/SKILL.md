---
name: i18n-design
version: v1.1.0
type: skill
enabled: true
mode: [standard, creator]
description: "在 ui-design 完成后、frontend-component 编码前进行国际化方案设计 — 多语言、翻译 Key 规范、多时区、多货币、RTL 布局、本地化格式。触发词: 国际化、i18n、多语言、多时区、翻译、本地化、RTL、locale、l10n。"
updated: 2026-09-11
depends_on: [system-design]
composes: [frontend-component]
---

# i18n Design

## 负责代理

`ui-designer` — 国际化设计由 UI 设计师代理负责，覆盖多语言、多时区、RTL 布局，确保多语言方案完整。

## 何时使用

- 需要为产品**规划多语言支持**时
- 需要设计**翻译文件结构**和**Key 命名规范**时
- 需要处理**多时区、多货币、多度量单位**时
- 需要支持**RTL（Right-to-Left）语言**（如阿拉伯语、希伯来语）时
- 需要选择**翻译管理平台**和**翻译工作流**时
- 需要定义**本地化格式**（日期、数字、货币、排序）时
- `ui-design` 完成后，`frontend-component` 编码前，需要国际化设计参考时

**触发关键词**: "国际化"、"i18n"、"多语言"、"多时区"、"翻译"、"本地化"、"RTL"、"locale"、"l10n"

## 与其他技能的关系

```text
brainstorming → system-design → api-design
                     ↓              ↓
                  ui-design ←──────┘
                     ↓
               i18n-design（本技能）
                     ↓
            frontend-component（编码）
```

> **衔接规则**:
> - `i18n-design` 依赖 `ui-design` 的页面设计 — 通过页面清单确定需要翻译的文本范围
> - `i18n-design` 与 `api-design` 部分交叉 — 语言切换接口、用户语言偏好存储等需协调
> - `frontend-component` 编码时以 `i18n-design` 输出的翻译 Key 规范和 RTL 适配方案为依据
> - 国际化方案不影响核心业务逻辑，但 UI 层的每个组件都必须遵循翻译 Key 引用规则

## 执行流程（骨架）

> 各 Phase 的详细模板、表格与代码见文末参考文档，按需加载。

### Phase 1: 语言与区域规划

- 基于 BCP 47（`语言-区域`）列出语言清单，按 P0-P3 分级并标注覆盖范围与书写方向
- 默认语言 + 回退链（如 `zh-CN` → `en-US`）+ 检测优先级（URL 路径 > 用户偏好 > Cookie > Accept-Language > 兜底）
- 语言切换方式选型：URL 路径切换（推荐，SEO 友好）；切换后停留当前页、更新 `<html lang>`

详细模板（语言清单基线、检测优先级、切换方式对比）→ [references/language-translation.md](references/language-translation.md) Phase 1。

### Phase 2: 翻译方案设计

- 文件格式选型：JSON（前端推荐）/ YAML / ICU MessageFormat
- Key 命名规范：模块前缀 + 点号层级 + 语义化（`project.list.title`）；公共文本归 `common.`，错误归 `common.error.`
- 插值 `{count}` 与复数（ICU plural）
- 翻译管理平台选型 + 工作流（机器翻译初填 → 人工校对 → CI 覆盖率检查 100%）

详细模板（JSON 结构示例、Key 反例、平台对比、工作流）→ [references/language-translation.md](references/language-translation.md) Phase 2。

### Phase 3: 时区与日期设计

- 核心原则：**全链路 UTC 存储**（DB / API / 日志），仅展示层转用户时区
- 时区获取优先级：用户设置 > 浏览器 `Intl` > 服务端兜底
- 格式化用原生 `Intl.DateTimeFormat`；相对时间用 dayjs relativeTime

详细模板 → [references/locale-ui-adaptation.md](references/locale-ui-adaptation.md) Phase 3。

### Phase 4: 货币与数字格式

- 金额以**最小单位整数**存储，API 标注 ISO 4217 货币代码，前端 `Intl.NumberFormat` 格式化
- 数字/百分比/文件大小/大数缩写规范；度量单位按区域（公制/英制）
- 排序规则 Collation 按语言（拼音/字母/五十音/韩文）

详细模板 → [references/locale-ui-adaptation.md](references/locale-ui-adaptation.md) Phase 4。

### Phase 5: UI 适配设计

- RTL：CSS 逻辑属性（`margin-inline-start` 等），禁止硬编码 `left`/`right`；Tailwind 用 `ps-4`/`ms-auto`/`text-start`
- 文字膨胀预留（中→德 180%、中→英 150%），溢出策略按场景（按钮换行/表头省略号/短版 Key）
- 字体栈按语言切换（`:root[lang=...]` CSS 变量），阿拉伯语需加大字号行高

详细模板 → [references/locale-ui-adaptation.md](references/locale-ui-adaptation.md) Phase 5。

### Phase 6: 输出 i18n-design.md

保存到 `docs/i18n-design.md`，章节结构模板 → [references/locale-ui-adaptation.md](references/locale-ui-adaptation.md) Phase 6。

## 参考文档（一层深，按需加载）

| 文档 | 内容 | 何时读 |
|------|------|--------|
| [references/language-translation.md](references/language-translation.md) | 语言清单、检测/切换策略、文件格式、Key 规范、插值复数、翻译工作流 | 执行 Phase 1-2 时 |
| [references/locale-ui-adaptation.md](references/locale-ui-adaptation.md) | 时区日期、货币数字、RTL、文字溢出、字体、输出结构 | 执行 Phase 3-6 时 |

## 国际化检查清单

**语言覆盖**:
- [ ] 所有 P0 语言翻译覆盖率 100%
- [ ] 所有 P1 语言翻译覆盖率 100%
- [ ] 不存在硬编码的用户可见文本字符串
- [ ] 所有翻译 Key 已定义且有回退值

**日期时间**:
- [ ] 所有日期时间统一以 UTC 存储
- [ ] 前端展示时已按用户时区转换
- [ ] 相对时间显示正确

**货币**:
- [ ] 所有货币金额标注 ISO 4217 代码
- [ ] 金额以最小单位（分）存储为整数
- [ ] 前端格式化正确（千分位、小数位）

**RTL 适配**:
- [ ] CSS 使用逻辑属性，无硬编码 `left`/`right`
- [ ] 所有页面在 RTL 语言下布局正确
- [ ] 图标方向在 RTL 下正确镜像
- [ ] 输入框文本在 RTL 下右对齐

**UI 适配**:
- [ ] 按钮文字有足够空间容纳膨胀后的文本
- [ ] 长文本有省略号 + Tooltip 处理
- [ ] 各语言字体正确加载
- [ ] 关键页面在目标语言下截图验证

**功能验证**:
- [ ] 语言切换后停留在当前页面
- [ ] 语言偏好持久化（刷新页面不丢失）
- [ ] URL 中包含语言信息（SEO 友好）
- [ ] 搜索引擎能正确索引各语言版本

## 硬性规则

- **所有用户可见文本必须通过翻译 Key 引用** — 代码中不得出现硬编码的中文/英文/任何语言字符串
- **日期时间必须统一存储 UTC** — 数据库、API、日志统一 UTC，仅展示层做时区转换
- **货币必须标注 ISO 4217 代码** — API 响应中货币字段必须附带 `currency` 代码
- **金额以最小单位存储为整数** — 避免浮点精度问题，存储分为单位
- **支持 RTL 时必须测试所有页面** — 不允许只适配部分页面
- **CSS 禁止硬编码 `left`/`right`** — 必须使用 `start`/`end` 逻辑属性
- **翻译 Key 必须有回退值** — 无法找到翻译时显示回退语言，不允许空白
- **语言切换后保持当前页面上下文** — 不允许跳回首页
- **翻译文件必须纳入版本控制** — 与代码同步提交，同版本发布
- **不允许 Key 缺失上线** — CI 必须检查翻译覆盖率，低于 100% 禁止合并

## 反模式

- **硬编码文本字符串** — `const title = "我的项目"` 必须改为 `t('project.list.title')`
- **使用字符串拼接构造翻译 Key** — `t('page.' + pageName + '.title')` 导致 Key 不可追踪
- **在 CSS 中硬编码 `left`/`right`** — 必须使用 `inset-inline-start`/`inset-inline-end` 或 Tailwind 的 `start-`/`end-` 工具类
- **翻译 Key 使用中文命名** — `"项目列表标题": "Project List"` 不可追踪，应使用 `"project.list.title": "Project List"`
- **每个语言文件结构不同** — 所有语言的 JSON 文件必须保持完全相同的 Key 结构，否则会导致 Key 缺失
- **忽略 RTL 适配** — 仅支持 LTR 语言，不支持 RTL 语言，导致中东市场无法进入
- **翻译文本不考虑长度膨胀** — 德语/俄语翻译可能比中文长 80%，不预留空间导致 UI 溢出
- **日期时间存储为本地时间** — 存储 `2026-07-24 16:30:00+08:00` 而非 `2026-07-24T08:30:00Z`，导致跨时区展示混乱
- **货币不标注代码** — 只返回 `price: 9.99` 无法判断是 USD 还是 EUR
- **只设翻译不设回退** — Key 缺失时页面显示空白，用户体验极差
