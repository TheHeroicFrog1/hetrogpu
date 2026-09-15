# HeteroGPU Memory Bank

## Project Overview
- **Name:** HeteroGPU (Heterogeneous GPU Architecture)
- **Path:** `C:\Users\aadit\HeteroGPU`
- **Goal:** Design and evaluate a 16-bit heterogeneous GPU architecture combining a 4-core SIMT engine with a specialized 2x2 AI/Matrix engine (Systolic Array) and a DMA engine, targeting budget FPGAs (Sipeed Tang Nano 9K/20K).
- **Phases:**
  1. Software Model / Instruction Set Simulator (Python) [COMPLETED]
  2. Neural Network & AI Forward Pass Engine [COMPLETED]
  3. Real-Time Hardware Telemetry HUD & Game Demo [COMPLETED]
  4. Academic Benchmark Suite & Viva Defense Guide [COMPLETED]
  5. Hardware Description (SystemVerilog RTL) & Simulation [COMPLETED]
  6. Physical Synthesis & Bitstream Generation (Tang Nano 9K / Gowin EDA) [NEXT PHASE]

## Current Architecture Components
1. **`processing_element.py`**:
   - 16-bit word width, 8 general-purpose registers (R0-R7).
   - Enforces 16-bit modular arithmetic (`& 0xFFFF`).
   - Supports `ADD`, `SUB`, `MUL`, `AND`, `OR`, `XOR`, `LOAD`, `STORE`, `NOP`.
   - **AI Instructions:** Added `RELU` (activation), `CMP_GT` (comparison), `MAX`, and signed 16-bit conversion.
2. **`memory.py`**:
   - Simulates FPGA Block RAM (BRAM) of 4096 16-bit words (8 KB).
   - Address 0-1023: 32x32 Framebuffer.
   - Address 1100-1115: Layer 1 AI Weights.
   - Address 1120-1127: Layer 2 AI Weights.
   - Address 1130-1133: AI Input State Buffer.
   - Address 1140-1143: Hidden Layer Activations.
   - Address 1150-1151: Output Decision Scores.
   - Address 1200-2223: DMA Animated Sprite Buffer.
3. **`simt_engine.py`**:
   - 4-core parallel Processing Element array.
   - Supports `LOAD_PARALLEL`, `STORE_PARALLEL`, arithmetic broadcast, and `parallel_relu`.
   - Parallel ReLU executes 4 activations simultaneously in just 5 clock cycles.
4. **`matrix_engine.py`**:
   - Specialized 2x2 MAC (Multiply-Accumulate) unit for AI workloads.
   - Supports 2x2 Systolic Array execution in 4 cycles and general tiled dense linear layers ($Y = X \times W$).
5. **`dma_engine.py`**:
   - Dedicated burst memory transfer engine with cycle tracking (1 setup cycle + $N$ word cycles).
6. **`heterogpu.py`**:
   - Top-level SoC controller combining Memory, SIMT, Matrix Engine, DMA, and real-time hardware cycle telemetry.
7. **`ai_model.py`**:
   - Quantized 2-layer MLP neural network running entirely on the heterogeneous engines.
   - Inputs: Ball (X, Y), Paddle Y, Ball Velocity. Output: UP / DOWN decision.
8. **`game_demo.py`**:
   - Interactive multi-mode Pygame showcase with side-by-side display and real-time Hardware Telemetry HUD.
   - Supports 4 live interactive modes switched via keyboard (`[1..4]`, `[TAB]`, `[SPACE]`) or on-screen tabs:
     - Mode 1: AI Acceleration (Neural Network Pong).
     - Mode 2: SIMT 4-Core Wave Shader (~95% SIMT utilization).
     - Mode 3: DMA Burst Streaming (zero core overhead, cores 100% idle).
     - Mode 4: The Showdown (live toggle with `[S]` between 110-cycle homogeneous SIMT and 34-cycle HeteroGPU).
9. **`benchmark.py`**:
   - Academic benchmark suite measuring authentic clock cycles. Demonstrates **5.75x hardware speedup** (92 SIMT cycles vs 16 Matrix Engine cycles) for 4x4 GEMM over fully simulated SIMT baseline.
10. **`run_demo.py`**:
   - Dedicated simulator launcher inside `python_test_simulator/` (`py python_test_simulator/run_demo.py`, `--bench`, `--graph`).
11. **`generate_graphs.py`**:
   - Automated Matplotlib script generating publication-quality 300 DPI evaluation charts saved to `python_test_simulator/results/heterogpu_evaluation_results.png` (2x2 test-by-test card layout with explicit Test 1-4 titles, speedup badges, and plain-English takeaways).
12. **`.gitignore`**:
   - Protects personal files (`VIVA_DEFENSE_GUIDE.md`, `CODE_EXPLAINED.md`, `*viva*`, `*defense*`, `notes/`, `personal/`), Python cache artifacts, and hardware simulation files (`*.vcd`, `*.vvp`, `heterogpu_sim`) from git tracking.
13. **`VIVA_DEFENSE_GUIDE.md`**:
   - Comprehensive cheatsheet with 30-second elevator pitch, speedup tables, deep dive on what each core does and how it was implemented (SIMT, 2x2 Systolic Array, DMA), live demo instructions, and anticipated viva Q&A (kept local, uncommitted to remote).
14. **`CODE_EXPLAINED.md`**:
   - Comprehensive guide detailing every Python file, class, method, and loop (`for`, `while`) with hardware timing rationale, parameter definitions for Tang Nano 9K FPGA, and an authenticity audit proving 100% genuine execution with zero fake components (kept local, uncommitted to remote).
15. **Git Repository Status**:
   - Repository synced and pushed cleanly to remote origin `https://github.com/TheHeroicFrog1/hetrogpu.git` on branch `main` (commit `700b64a`).
16. **AI Neural Network Calibration**:
   - Calibrated $W_1$ and $W_2$ weights in `ai_model.py` for trajectory prediction and anti-oscillation tracking.
   - Verified 100.0% intercept rate across 1,000 continuous frames (21 hits, 0 misses).
17. **Academic References & Literature**:
   - Curated bibliography in `REFERENCES.md` covering Google TPU (ISCA 2017), Kung & Leiserson (1979), NVIDIA Volta Tensor Core (IEEE Micro 2018), and open-source GitHub FPGA GPUs (`tiny-gpu`, `smol-gpu`, `Gemmini`, `FPGA-SystolicArray`).
18. **Package Structure & Directory Layout**:
   - Clean, professional root structure: all Phase 1 Python architectural simulation modules, benchmarks, graphs, and the single `run_demo.py` launcher are organized inside `python_test_simulator/`.
   - Unified `hardware/` subfolder houses all Phase 2 SystemVerilog hardware modules (`hardware/rtl/`), verification testbenches (`hardware/sim/`), and Tang Nano 9K FPGA constraints (`hardware/fpga/`).
   - Configured `.vscode/settings.json` with `python.analysis.extraPaths: ["./python_test_simulator"]` and defensive `sys.path` fallbacks to resolve VS Code Pylance static analysis diagnostics cleanly.
19. **Reality Audit & Physical SIMT Simulation**:
   - Replaced analytical benchmark estimates with actual instruction-by-instruction execution routines in `SIMTEngine` (`execute_gemm_4x4()` and `execute_copy()`).
   - All timing benchmarks are 100% physically simulated in software register-transfer logic.
20. **Hardware Terminology & Plain-English Annotations**:
   - Enriched all simulator modules (`processing_element.py`, `memory.py`, `simt_engine.py`, `matrix_engine.py`, `dma_engine.py`, `heterogpu.py`, `ai_model.py`, `benchmark.py`) with student-style plain English hardware annotations.
   - Clearly documents VLSI concepts (word masking, two's complement, GPR register files, BRAM boundaries, SIMT instruction broadcast, 2D systolic dataflow, DMA bus arbitration, fixed-point scaling).
21. **Phase 2: Synthesizable SystemVerilog RTL Implementation & Testbench**:
   - Authored synthesizable SystemVerilog modules in `hardware/rtl/` matching Python Golden Model 1-to-1:
     - `hardware/rtl/pe_core.sv`: 16-bit ALU (ADD, SUB, MUL, RELU sign-bit zeroing, CMP_GT, MAX) + 8-word GPR file (R0-R7).
     - `hardware/rtl/simt_engine.sv`: 4-lane parallel SIMT array with lockstep instruction broadcast and parallel memory vector access.
     - `hardware/rtl/systolic_array_2x2.sv`: 2x2 Tensor Processing Unit with 4 physical DSP MAC cells (Kung & Leiserson dataflow, 4 clock cycles).
     - `hardware/rtl/dma_controller.sv`: Dedicated hardware burst memory controller ($1 + N$ cycles).
     - `hardware/rtl/bram_memory.sv`: 4096-word dual-port synchronous Block RAM (8 KB) synthesizable to Gowin BSRAM.
     - `hardware/rtl/heterogpu_top.sv`: Top-level SoC interconnecting all compute cores, memory arbiter, and cycle telemetry.
   - Created verification testbench `hardware/sim/tb_heterogpu.sv` with 27 MHz clock generator and waveform dumping (`hardware/sim/waves.vcd`).
   - Added `hardware/sim/filelist.f` for cross-platform EDA compilation and one-click scripts `hardware/sim/run_sim.ps1` and `hardware/sim/run_sim.bat`.
   - Verified simulation output: all 3 testbenches passed (ReLU clamp, 4-cycle Systolic Array, 9-cycle DMA burst).
   - Created physical FPGA pin constraints `hardware/fpga/tangnano9k/tangnano9k.cst` and timing constraints `tangnano9k.sdc` for Sipeed Tang Nano 9K (Gowin GW1NR-9).
   - Added `C:\iverilog\bin` permanently to user Windows `PATH` environment variable.
   - Resolved WaveTrace VS Code extension startup error by initializing `config.wavetrace.json` in VS Code globalStorage.

## Key Empirical Results
- **GEMM 4x4 Matrix Multiply:** 92 cycles (SIMT baseline: scalar broadcast, parallel load, parallel mul, parallel add, parallel store) vs **16 cycles (HeteroGPU AI Engine)** = **5.75x Hardware Speedup**.
- **Memory Block Copy (64 words):** 80 cycles (SIMT load/store chunks) vs **65 cycles (DMA)** = **1.23x speedup with 100% compute cores freed**.
- **End-to-End AI Forward Pass:** **34 Clock Cycles total** (70.6% Matrix Engine, 14.7% SIMT activations, 14.7% DMA transfers).
- **RTL Hardware Telemetry:** Total RTL verification cycle count: 15 cycles (PE ReLU: 2 cycles, Systolic GEMM: 4 cycles, DMA 8-word burst: 9 cycles).
