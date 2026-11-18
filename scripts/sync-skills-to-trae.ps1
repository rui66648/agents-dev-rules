# 同步技能真源 skills/ -> .trae/skills（TRAE 自动加载副本）
# 依据 AGENTS.md「前端组件规则唯一真源声明」与 .trae/USAGE.md 真源声明：
#   - 唯一真源：skills/   - 部署副本：.trae/skills/（TRAE 自动识别）
# 修改技能后运行本脚本，禁止直接编辑 .trae/skills/。
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $root "skills"
$dst = Join-Path $root ".trae\skills"
if (-not (Test-Path $src)) { throw "skills/ 不存在: $src" }
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
Copy-Item $src $dst -Recurse -Force
$n = (Get-ChildItem $dst -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
Write-Host "已同步 skills/ -> .trae/skills（$n 个技能）"
