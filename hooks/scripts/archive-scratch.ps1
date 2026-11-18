<#
 archive-scratch.ps1 — 把 scratch 受管根按 RULE-053 §4 归档（归档不删除）
 ============================================================
 用法：
   powershell -ExecutionPolicy Bypass -File archive-scratch.ps1 -Root <scratch根绝对路径> [-ArchiveBase <归档父目录>]

 行为：
   1. 在 -ArchiveBase（默认 <RULES_ROOT>\archive）下建 scratch-quarantine-<YYYY-MM-DD>\
   2. Move-Item 把 <Root> 整体移入归档目录
   3. 写 MANIFEST.json（from→to）+ 归档 README.md（来源/为何归档/恢复方式）
   4. 从 managed-root-set.json 移除该条目（避免下次扫描报目录不存在）

 原则：归档而非删除（RULE-053 §4）；生成 MANIFEST 满足 §3 收尾节拍。
#>
param(
  [Parameter(Mandatory=$true)][string]$Root,
  [string]$ArchiveBase = ""
)
$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new()

# 规则根 = 本脚本所在目录的上一级（不依赖任何绝对路径，可随仓迁移）
$RulesRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if ([string]::IsNullOrWhiteSpace($ArchiveBase)) { $ArchiveBase = Join-Path $RulesRoot "archive" }

if (-not (Test-Path -LiteralPath $Root)) { Write-Error "Root 不存在：$Root"; exit 2 }
$Root = (Resolve-Path -LiteralPath $Root).Path
$stamp = (Get-Date).ToString('yyyy-MM-dd')
$archDir = Join-Path $ArchiveBase ("scratch-quarantine-" + $stamp)
$dest = Join-Path $archDir (Split-Path $Root -Leaf)

if (Test-Path -LiteralPath $dest) { Write-Error "归档目标已存在：$dest"; exit 2 }
New-Item -ItemType Directory -Path $archDir -Force | Out-Null

# 1. 整体移动
Move-Item -LiteralPath $Root -Destination $dest -Force
Write-Host "MOVED $Root -> $dest"

# 2. MANIFEST + README
$manifest = @([pscustomobject]@{ from = $Root; to = $dest; reason = "scratch TTL 到期归档（RULE-053 §4）"; date = $stamp })
$manifest | ConvertTo-Json -Depth 4 | Out-File (Join-Path $archDir 'MANIFEST.json') -Encoding utf8

@("# scratch 归档：$stamp", "",
  "> 来源：$Root（受管根 kind=scratch，TTL 到期）",
  "> 处置：RULE-053 §4 归档而非删除；按 MANIFEST.json from→to 反向移动可恢复。",
  "> 同批已从 managed-root-set.json 移除该条目。"
) | Out-File (Join-Path $archDir 'README.md') -Encoding utf8

# 3. 从 MRS 移除该条目
$mrsPath = Join-Path $RulesRoot "hooks\configs\managed-root-set.json"
if (Test-Path $mrsPath) {
  $mrs = Get-Content $mrsPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $mrs.roots = @($mrs.roots | Where-Object { (Resolve-Path -LiteralPath $_.path -ErrorAction SilentlyContinue).Path -ne $Root -and $_.path -ne $Root })
  $mrs | ConvertTo-Json -Depth 10 | Out-File $mrsPath -Encoding utf8
  Write-Host "MRS 已移除条目：$Root"
}

Write-Host "归档完成：$archDir"
