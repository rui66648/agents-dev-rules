# run-gates.ps1 — verification skill: deterministic gate runner with evidence collection
# Runs test / lint / typecheck / build gates, captures full output as evidence,
# and exits 1 if any gate failed (build is skipped when earlier gates failed).
#
# Usage (adapt commands to the project's stack):
#   powershell -File run-gates.ps1 -TestCmd "pytest --tb=short -q" -LintCmd "ruff check ." -BuildCmd "pnpm build"
#   powershell -File run-gates.ps1 -TestCmd "npm test -- --run" -LintCmd "npm run typecheck" -BuildCmd "npm run build"
#
# Rules:
#   - Do not modify gate semantics; only override commands via parameters.
#   - Evidence logs are written under .verify-evidence/<timestamp>/ relative to the caller's working directory.

param(
    [string]$TestCmd = "",
    [string]$LintCmd = "",
    [string]$TypecheckCmd = "",
    [string]$BuildCmd = "",
    [string]$EvidenceDir = ".verify-evidence"
)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = Join-Path $EvidenceDir $timestamp
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Invoke-Gate {
    param(
        [string]$Name,
        [string]$Command
    )

    if ([string]::IsNullOrWhiteSpace($Command)) {
        Write-Host "[SKIP] $Name - no command provided" -ForegroundColor Yellow
        return $true
    }

    $safeName = $Name -replace '[^a-zA-Z0-9_-]', '_'
    $logFile = Join-Path $logDir "$safeName.log"

    Write-Host ""
    Write-Host "[RUN ] $Name :: $Command" -ForegroundColor Cyan

    # Route all output streams to the evidence log AND console
    & cmd.exe /c "$Command > `"$logFile`" 2>&1"
    $exitCode = $LASTEXITCODE

    Get-Content $logFile -Encoding UTF8 | ForEach-Object { Write-Host "  $_" }

    if ($exitCode -ne 0) {
        Write-Host "[FAIL] $Name (exit=$exitCode) - evidence: $logFile" -ForegroundColor Red
        return $false
    }

    Write-Host "[PASS] $Name - evidence: $logFile" -ForegroundColor Green
    return $true
}

Write-Host "=== Verification Gates ==="
Write-Host "Evidence dir: $logDir"

$overall = $true

if (-not (Invoke-Gate -Name "test" -Command $TestCmd)) { $overall = $false }
if (-not (Invoke-Gate -Name "lint" -Command $LintCmd)) { $overall = $false }
if (-not (Invoke-Gate -Name "typecheck" -Command $TypecheckCmd)) { $overall = $false }

# Build runs last: most expensive, only worth running if earlier gates passed
if ($overall -and -not (Invoke-Gate -Name "build" -Command $BuildCmd)) { $overall = $false }

Write-Host ""
if ($overall) {
    Write-Host "=== RESULT: ALL GATES PASSED ===" -ForegroundColor Green
    Write-Host "Attach the following evidence to the verification report:"
    Get-ChildItem $logDir -Filter *.log | ForEach-Object { Write-Host "  - $($_.FullName)" }
    exit 0
} else {
    Write-Host "=== RESULT: GATES FAILED - fix before claiming completion ===" -ForegroundColor Red
    exit 1
}
