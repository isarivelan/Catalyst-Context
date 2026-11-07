param(
    [switch]$DryRun,
    [switch]$RunJobs,
    [switch]$SeedInstances,
    [switch]$SkipModel
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$argList = @()
if ($DryRun) { $argList += "--dry-run" }
if ($RunJobs) { $argList += "--run-jobs" }
if ($SeedInstances) { $argList += "--seed-instances" }
if ($SkipModel) { $argList += "--skip-model" }

& $python (Join-Path $PSScriptRoot "deploy_cdf.py") @argList
exit $LASTEXITCODE
