# ==============================================================================
# HeteroGPU RTL Simulation Runner (PowerShell)
# ==============================================================================

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

# Ensure iverilog is available in current process if PATH hasn't reloaded yet
if (-not (Get-Command "iverilog" -ErrorAction SilentlyContinue)) {
    if (Test-Path "C:\iverilog\bin\iverilog.exe") {
        $env:Path = "$env:Path;C:\iverilog\bin"
    }
}

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "   Compiling HeteroGPU RTL & Verification Suite       " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

iverilog -g2012 -o hardware/sim/heterogpu_sim -f hardware/sim/filelist.f

if ($LASTEXITCODE -ne 0) {
    Write-Host "Compilation failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`nRunning Simulation..." -ForegroundColor Cyan
vvp hardware/sim/heterogpu_sim

Write-Host "`nSimulation complete! Waveforms saved to: hardware/sim/waves.vcd" -ForegroundColor Green
Write-Host "To open waveforms in GTKWave, execute:" -ForegroundColor Yellow
Write-Host "  gtkwave hardware/sim/waves.vcd" -ForegroundColor White
