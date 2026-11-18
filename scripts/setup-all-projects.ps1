# 批量配置开发流程规则到所有项目
# 在本目录 (<RULES_ROOT>) 执行
#
# 用法：
#   pwsh -File setup-all-projects.ps1 -Base <项目根目录> -Projects "proj-a,proj-b"

param(
    [string]$Base = "",
    [string]$Projects = ""
)

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($RULES_ROOT)) { $RULES_ROOT = Split-Path -Parent $SCRIPT_DIR }
if ([string]::IsNullOrWhiteSpace($Base)) { $Base = Split-Path -Parent $RULES_ROOT }
if ([string]::IsNullOrWhiteSpace($Projects)) {
    Write-Error "缺少 -Projects 参数：逗号分隔的项目目录名（相对 -Base）"
    exit 1
}

# 所有目标项目（由 -Projects 传入，逗号分隔）
$projects = @(
    $Projects -split ',' | Where-Object { $_.Trim() } | ForEach-Object {
        @{ name = $_.Trim(); desc = "目标项目" }
    }
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  批量配置开发流程规则" -ForegroundColor Cyan
Write-Host "  目标: $BASE" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($proj in $projects) {
    $path = Join-Path $BASE $proj.name
    $agPath = Join-Path $path "AGENTS.md"
    $techPath = Join-Path $path "tech-stack.md"

    if (-not (Test-Path $path)) {
        Write-Host "  [SKIP] $path 不存在" -ForegroundColor Gray
        continue
    }

    # 复制 AGENTS.md (仅当不存在或为旧版时)
    $sourceAgents = Join-Path $RULES_ROOT "AGENTS.md"
    if (Test-Path $agPath) {
        $existing = Get-Content $agPath -Raw
        if ($existing -match "开发流程规则.*v\d+\.\d+.*入口路由") {
            Write-Host "  [SKIP] $($proj.name) AGENTS.md 已是最新版" -ForegroundColor Gray
        } else {
            Copy-Item $sourceAgents $agPath -Force
            Write-Host "  [OK]   $($proj.name) AGENTS.md 已更新" -ForegroundColor Green
        }
    } else {
        # 创建项目特定的 AGENTS.md (引用共享规则)
        $content = @"
# AGENTS.md - $($_.name) ($($proj.desc))

> **版本**: v1.0.0 | **更新**: 2026-08-03
> 基于 `<RULES_ROOT>\AGENTS.md` 的共享规则体系

## 项目概述
$($proj.desc)

## 共享规则

> 本项目使用 `<RULES_ROOT>\AGENTS.md`（v3.2.0）作为通用构建规则入口。
> 本文件仅包含项目特定的技术栈、路径和约束，其余规则（工作流、架构、安全、测试等）统一引用共享规则。
>
> 共享规则位置：`<RULES_ROOT>\AGENTS.md`
> 详细规则目录：`<RULES_ROOT>\rules\`
> 技能定义目录：`<RULES_ROOT>\skills\`
> 子代理定义目录：`<RULES_ROOT>\agents\`

## 项目技术栈

见同级 `tech-stack.md`。

## 关键路径

- 详见 `tech-stack.md`

## 构建命令

详见 `tech-stack.md`
"@
        Set-Content -Path $agPath -Value $content -Encoding UTF8
        Write-Host "  [OK]   $($proj.name) AGENTS.md 已创建" -ForegroundColor Green
    }

    # 复制 tech-stack.md (仅当不存在时)
    $sourceTech = Join-Path $RULES_ROOT "tech-stack.md"
    if (-not (Test-Path $techPath)) {
        # 创建最小 tech-stack.md
        $techContent = @"
# tech-stack.md - $($_.name)

> **版本**: v1.0.0 | **更新**: 2026-08-03

\`\`\`yaml
project_name: "$($proj.name)"
project_type: "fullstack"
description: "$($proj.desc)"
\`\`\`

---

## 技术栈

详见共享规则模板: \`<RULES_ROOT>\tech-stack.md\`

## 构建命令

详见共享规则模板

## 编码规范

详见共享规则模板
"@
        Set-Content -Path $techPath -Value $techContent -Encoding UTF8
        Write-Host "  [OK]   $($proj.name) tech-stack.md 已创建 (引用共享模板)" -ForegroundColor Green
    } else {
        Write-Host "  [SKIP] $($proj.name) tech-stack.md 已存在" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  配置完成" -ForegroundColor Green
Write-Host "  规则源: $RULES_ROOT" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
