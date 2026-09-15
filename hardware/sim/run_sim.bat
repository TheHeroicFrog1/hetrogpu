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

iverilog -g2012 -o hardware/sim/heterogpu_sim -f hardware/sim/filelist.f
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
