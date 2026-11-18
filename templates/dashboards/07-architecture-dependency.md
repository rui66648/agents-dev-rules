---
slot: 07
slug: architecture-dependency
title: 架构拓扑图 + 依赖关系图
decision: 拆分 / 合并 / 加隔离 / 排技术债（拍板人：架构负责人；变更影响面写进决策段）
cadence: quarterly
owner: 待指派
status: deferred
reason: 骨架由 RULE-054 建立，尚未取数；占住槽位，防止日后另起一张重复图
revisit: 2026-11-30
---
# 07 架构拓扑图 + 依赖关系图

## 决策
拆分 / 合并 / 加隔离 / 排技术债（拍板人：架构负责人；变更影响面写进决策段）

## 读数
（deferred：未取数。转 active 前先在 thresholds.md 补齐本图指标口径与数据源，再逐条填表；口径变更要在「变化」段留 delta。）

| ID | 组件 | 所属仓/面 | 依赖 | 被依赖 | 变更影响面 | 灯 |
|---|---|---|---|---|---|---|

## 图
本图唯一的渲染位（mermaid / ASCII / 同名 `<id>-<slug>.render.html`）。一份槽位只留一张，禁止另存带日期或 v2 的副本 —— 历史交给 git。

## 变化
- 2026-11-01 建立骨架（deferred，无读数）

## 取数
- 数据源：从代码派生优先：import 图 / 注册表 / 部署拓扑脚本，禁止画完之后与代码脱钩。
- 负责人：待指派
- last_updated: 未更新
