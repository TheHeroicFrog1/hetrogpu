@echo off
setlocal
cd /d "%~dp0\..\.."

where gtkwave >nul 2>nul
if %errorlevel% neq 0 (
    if exist "C:\iverilog\bin\gtkwave.exe" (
        set "PATH=%PATH%;C:\iverilog\bin"
    )
)

if not exist "hardware\sim\waves.vcd" (
    echo [INFO] waves.vcd not found. Running simulation first...
    call "hardware\sim\run_sim.bat"
)

echo [INFO] Launching GTKWave with pre-configured HeteroGPU signals...
start "" gtkwave hardware\sim\waves.vcd hardware\sim\waves.gtkw
