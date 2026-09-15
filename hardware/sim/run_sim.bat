@echo off
setlocal
cd /d "%~dp0\..\.."

where iverilog >nul 2>nul
if %errorlevel% neq 0 (
    if exist "C:\iverilog\bin\iverilog.exe" (
        set "PATH=%PATH%;C:\iverilog\bin"
    )
)

echo =======================================================
echo    Compiling HeteroGPU RTL ^& Verification Suite
echo =======================================================

iverilog -g2012 -o hardware/sim/heterogpu_sim hardware/rtl/bram_memory.sv hardware/rtl/pe_core.sv hardware/rtl/simt_engine.sv hardware/rtl/systolic_array_2x2.sv hardware/rtl/dma_controller.sv hardware/rtl/heterogpu_top.sv hardware/sim/tb_heterogpu.sv
if %errorlevel% neq 0 (
    echo [ERROR] RTL compilation failed!
    exit /b %errorlevel%
)

echo.
echo Running Simulation...
vvp hardware/sim/heterogpu_sim

echo.
echo Simulation complete! Waveforms saved to hardware/sim/waves.vcd
echo To open waveforms in GTKWave:
echo   gtkwave hardware/sim/waves.vcd
