---
slot: 08
slug: code-health
title: 代码健康图（提交热力 / PR 流转 / 覆盖率 / 长期分支）
decision: 评审加人 / 技术债排期 / 分支收口（拍板人：工程负责人）
cadence: weekly
owner: 待指派
status: deferred
reason: 骨架由 RULE-054 建立，尚未取数；占住槽位，防止日后另起一张重复图
revisit: 2026-11-30
---
# 08 代码健康图（提交热力 / PR 流转 / 覆盖率 / 长期分支）

## 决策
评审加人 / 技术债排期 / 分支收口（拍板人：工程负责人）

## 读数
（deferred：未取数。转 active 前先在 thresholds.md 补齐本图指标口径与数据源，再逐条填表；口径变更要在「变化」段留 delta。）

| 周 | 提交数 | PR 数 | 平均评审等待 | 平均合并时长 | 覆盖率 | 存活>14天分支 | 灯 |
|---|---|---|---|---|---|---|---|

## 图
本图唯一的渲染位（表格即图，或同名 `<id>-<slug>.render.html`）。禁止另存副本，历史交给 git。

## 变化
- 2026-11-01 建立骨架（deferred，无读数）

## 取数
- 数据源：git log + forge API 派生（如 `git log --since=7.week` 与 PR 列表）；长期分支清单来自分支回收工具。
- 负责人：待指派
- last_updated: 未更新
