# 项目初始化脚本 - 自动配置开发流程规则
#
# 使用方法：
#   .\init-project-rules.ps1 "C:\path\to\your-project"
#
# 或在项目根目录直接执行（自动识别当前目录）：
#   .\init-project-rules.ps1
#
# 要求：以管理员权限运行（用于创建 Junction 点）

param(
    [string]$TargetProject = "",
    [string]$RulesRoot = "",
    [switch]$NoAdmin,
    [switch]$DryRun
)

# 规则根：优先显式参数 > 环境变量 RULES_ROOT > 本脚本所在仓库根
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($RulesRoot)) { $RulesRoot = $env:RULES_ROOT }
if ([string]::IsNullOrWhiteSpace($RulesRoot)) { $RulesRoot = Split-Path -Parent $SCRIPT_DIR }
$RULES_ROOT = $RulesRoot

# 验证规则目录存在
if (-not (Test-Path $RULES_ROOT)) {
    Write-Error "规则目录不存在: $RULES_ROOT"
    exit 1
}

# 确定目标项目目录
if ($TargetProject -eq "") {
    $TargetProject = Get-Location
} else {
    $TargetProject = $TargetProject.Trim('"').Trim("'")
}

if (-not (Test-Path $TargetProject)) {
    Write-Error "项目目录不存在: $TargetProject"
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  开发流程规则配置工具 v1.0" -ForegroundColor Cyan
Write-Host "  目标项目: $TargetProject" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$Items = @(
    @{ Name = "AGENTS.md"; Type = "file"; Link = "stub" },      # v4.10.1：引用式存根（始终取共享规则最新版），不再复制冻结版本
    @{ Name = "tech-stack.md"; Type = "file"; Link = "copy" },  # 仅作初始模板，项目自行定制
    @{ Name = "rules"; Type = "directory"; Link = "junction" },
    @{ Name = "skills"; Type = "directory"; Link = "junction" },
    @{ Name = "agents"; Type = "directory"; Link = "junction" },
    @{ Name = "commands"; Type = "directory"; Link = "junction" },
    @{ Name = "hooks"; Type = "directory"; Link = "junction" }  # v4.10.1：部署确定性强制工具（pre-commit 可直接安装）
)

$Actions = @()

foreach ($Item in $Items) {
    $SourcePath = Join-Path $RULES_ROOT $Item.Name
    $TargetPath = Join-Path $TargetProject $Item.Name

    if ($Item.Link -eq "copy") {
        # 仅文件不存在时才复制
        if (-not (Test-Path $TargetPath) -or ($Item.Name -eq "AGENTS.md" -and -not (Test-Path $TargetPath))) {
            $Actions += "COPY $($Item.Name)"
        } else {
            Write-Host "  [SKIP] $($Item.Name) 已存在" -ForegroundColor Gray
        }
    } elseif ($Item.Link -eq "stub") {
        if (Test-Path $TargetPath) {
            Write-Host "  [SKIP] $($Item.Name) 已存在" -ForegroundColor Gray
        } else {
            $Actions += "STUB $($Item.Name)"
        }
    } elseif ($Item.Link -eq "junction") {
        if (Test-Path $TargetPath) {
            $Attrs = (Get-Item $TargetPath -Force).Attributes
            if ($Attrs -band [System.IO.FileAttributes]::ReparsePoint) {
                Write-Host "  [SKIP] $($Item.Name) 已是符号链接" -ForegroundColor Gray
                continue
            }
            Write-Host "  [SKIP] $($Item.Name) 已存在（非符号链接）" -ForegroundColor Yellow
        } else {
            $Actions += "JUNCTION $($Item.Name)"
        }
    }
}

Write-Host "待执行操作: $($Actions -join ', ')" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] 无实际操作，仅预览" -ForegroundColor Gray
    exit 0
}

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

foreach ($Action in $Actions) {
    $Parts = $Action -split " "
    $Op = $Parts[0]
    $Name = $Parts[1]
    $SourcePath = Join-Path $RULES_ROOT $Name
    $TargetPath = Join-Path $TargetProject $Name

    try {
        if ($Op -eq "STUB") {
            # v4.10.1：AGENTS.md 写引用式存根（始终取共享规则最新版），不复制冻结版本
            $projName = Split-Path -Leaf $TargetProject
            $stub = @"
# AGENTS.md - $projName

> 本项目使用 ``$RULES_ROOT\AGENTS.md``（始终取共享规则最新版）作为通用构建规则入口。
> 规则源目录：``$RULES_ROOT``（rules/ skills/ agents/ commands/ hooks/ 经 Junction 链接，修改共享规则根即全量生效）。
> 跨项目组件校验（可在本项目目录直接运行）：
>   python ``"$RULES_ROOT\hooks\scripts\component-validator.py``" --check-components <file>

## 项目概述
（由项目补充）

## 技术栈
见 tech-stack.md。
"@
            [System.IO.File]::WriteAllText($TargetPath, $stub, [System.Text.UTF8Encoding]::new($false))
            Write-Host "  [OK]   存根: $Name（引用共享规则最新版）" -ForegroundColor Green
        } elseif ($Op -eq "COPY") {
            Copy-Item -Path $SourcePath -Destination $TargetPath -Force
            Write-Host "  [OK]   复制: $Name" -ForegroundColor Green
        } elseif ($Op -eq "JUNCTION") {
            if (-not $isAdmin -and -not $NoAdmin) {
                Write-Host "  [WARN] 创建 Junction 需要管理员权限，请重新以管理员身份运行" -ForegroundColor Yellow
                Write-Host "         添加 --NoAdmin 参数将跳过 Junction 创建" -ForegroundColor Gray
                continue
            }
            cmd /c "mklink /J `"$TargetPath`" `"$SourcePath`"" 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK]   Junction: $Name" -ForegroundColor Green
            } else {
                Write-Host "  [FAIL] Junction 创建失败: $Name（需要管理员权限）" -ForegroundColor Red
                Write-Host "         请手动执行: mklink /J `"$TargetPath`" `"$SourcePath`"" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "  [FAIL] $Name : $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  配置完成" -ForegroundColor Green
Write-Host "  规则源: $RULES_ROOT" -ForegroundColor Gray
Write-Host "  更新规则: 修改 $RULES_ROOT 下的文件即可" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
