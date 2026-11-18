# 插件清单标准 (Plugin Manifest Standard) v1.0.0

> **生成时间**: 2026-08-15
> **落实规则**: RULE-042（插件组装优先）、RULE-043（插件清单合规）
> **参考架构**: DeepSeek Harness "一切皆插件" + Cordis 插件内核
> **目标**: 让技能/规则/命令/Agent 具备统一的插件接口，实现配置驱动组合、可插拔、可组合

---

## 一、核心理念

**一切皆插件（Everything is a Plugin）**：技能、规则、命令、Agent 都是能力单元（插件），
通过统一的 **插件清单（Plugin Manifest）** 声明自身接口，由 **组合配置（cordis.yaml）**
决定启用/禁用，由 **注册表（registry.yaml）** 提供发现能力。

```
插件 = 能力单元（技能/规则/命令/Agent）
清单 = 能力单元的接口声明（frontmatter）
组合 = 通过配置组装插件（cordis.yaml）
注册 = 插件目录与发现（registry.yaml）
```

## 二、插件清单字段（frontmatter 扩展）

所有插件在 frontmatter 中声明以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 插件唯一标识（kebab-case） |
| `version` | string | ✅ | 语义化版本（vX.Y.Z） |
| `type` | enum | ✅ | `skill` \| `rule` \| `command` \| `agent` |
| `enabled` | boolean | ❌ | 默认启用状态（默认 `true`） |
| `mode` | array | ❌ | 所属运行时模式（默认 `[standard]`） |
| `interface` | object | ❌ | 接口契约（inputs/outputs） |
| `config` | object | ❌ | 插件级配置（默认值） |
| `depends_on` | array | ❌ | 前置依赖插件 ID |
| `composes` | array | ❌ | 可组合的下游插件 ID |

### 2.1 技能插件（type: skill）

```yaml
---
name: brainstorming
version: v1.3.0
type: skill
enabled: true
mode: [standard, creator]
interface:
  inputs: [topic, constraints]
  outputs: [design_doc, hotl_contract]
config:
  research: true
depends_on: []
composes: [system-design]
---
```

### 2.2 规则插件（type: rule）

```yaml
---
name: open-source-first
version: v2.0.0
type: rule
rule_id: [RULE-017, RULE-018, RULE-019, RULE-042]
level: 铁律
enabled: true
mode: [standard, creator]
enforcement: L1-L5 评估 + ADR 记录
---
```

### 2.3 命令插件（type: command）

```yaml
---
name: brainstorm
version: v1.0.0
type: command
enabled: true
mode: [standard, creator]
maps_to: skills/brainstorming
triggers: [头脑风暴, 需求分析, 方案探索]
---
```

### 2.4 Agent 插件（type: agent）

```yaml
---
name: architect
version: v1.2.0
type: agent
enabled: true
mode: [standard, creator]
owns: [project-initiation, brainstorming, system-design, writing-plans]
---
```

## 三、接口契约（interface）

`interface` 定义插件的输入/输出，是插件可组合性的基础：

```yaml
interface:
  inputs:
    - name: topic
      type: string
      required: true
      description: 需求主题
  outputs:
    - name: design_doc
      type: file
      description: 结构化设计文档
```

> **组合规则**：插件 A 的 `outputs` 与插件 B 的 `inputs` 匹配时，A 可组合到 B（`composes`）。

## 四、运行时模式（mode）

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `standard` | 全量插件 | 日常开发 |
| `minimal` | 仅核心插件 | 快速任务 / 基准测试 |
| `creator` | 全量 + 运行时检查 | 创建自定义 Agent |

插件通过 `mode` 声明所属模式；`presets/` 目录定义各模式的默认插件集。

## 五、合规要求（RULE-043）

1. **必填字段**：`name`、`version`、`type` 必须声明
2. **唯一标识**：`name` 全局唯一，禁止重复
3. **依赖声明**：`depends_on` 引用的插件必须存在于注册表
4. **组合声明**：`composes` 引用的插件必须存在于注册表
5. **模式合法**：`mode` 取值必须为 `standard` / `minimal` / `creator`
6. **校验执行**：由 `hooks/scripts/plugin-validator.py` 确定性校验，违反阻断提交

## 六、校验与执行

```bash
# 校验全部插件清单
python hooks/scripts/plugin-validator.py --check-all

# 校验单个插件
python hooks/scripts/plugin-validator.py --check skills/brainstorming/SKILL.md

# 校验注册表一致性
python hooks/scripts/plugin-validator.py --check-registry
```

## 七、与现有格式的兼容

- 现有 `depends_on` / `composes` 字段**保留**，作为插件依赖声明
- 新增字段均为**可选**（除 `name`/`version`/`type`），不破坏现有解析
- 未声明 `type` 的旧文件按类型目录推断（`skills/` → skill，`rules/` → rule）
