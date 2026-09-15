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

iverilog -g2012 -o hardware/sim/heterogpu_sim `
    hardware/rtl/bram_memory.sv `
    hardware/rtl/pe_core.sv `
    hardware/rtl/simt_engine.sv `
    hardware/rtl/systolic_array_2x2.sv `
    hardware/rtl/dma_controller.sv `
    hardware/rtl/heterogpu_top.sv `
    hardware/sim/tb_heterogpu.sv

if ($LASTEXITCODE -ne 0) {
    Write-Host "Compilation failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`nRunning Simulation..." -ForegroundColor Cyan
vvp hardware/sim/heterogpu_sim

Write-Host "`nSimulation complete! Waveforms saved to: hardware/sim/waves.vcd" -ForegroundColor Green
Write-Host "To open waveforms in GTKWave, execute:" -ForegroundColor Yellow
Write-Host "  gtkwave hardware/sim/waves.vcd" -ForegroundColor White
