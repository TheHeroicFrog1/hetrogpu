# HeteroGPU: A 16-Bit Heterogeneous GPU Architecture with SIMT, Systolic Tensor Core & DMA

[![Language: SystemVerilog](https://img.shields.io/badge/Language-SystemVerilog-blue.svg)](rtl/)
[![Model: Python 3.10](https://img.shields.io/badge/Golden_Model-Python_3.10-green.svg)](python_test_simulator/)
[![Target FPGA: Tang Nano 9K](https://img.shields.io/badge/FPGA-Sipeed_Tang_Nano_9K-orange.svg)](fpga/tangnano9k/)
[![GEMM Speedup: 5.75x](https://img.shields.io/badge/Hardware_Speedup-5.75x-brightgreen.svg)](#benchmarks--empirical-results)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**HeteroGPU** is a synthesized, 16-bit heterogeneous GPU architecture designed for budget, resource-constrained FPGAs (specifically the **Sipeed Tang Nano 9K / Gowin GW1NR-9**). It integrates a 4-lane SIMT vector engine, a 2x2 Systolic Array tensor engine, and an autonomous DMA burst controller over a shared 8 KB Block RAM (BRAM).

---

## 🏛️ Microarchitecture Overview

```
                         ┌──────────────────────────────────────────────┐
                         │               Host / Arbiter Bus             │
                         └──────┬──────────────┬──────────────┬─────────┘
                                │              │              │
             ┌──────────────────┘              │              └──────────────────┐
             ▼                                 ▼                                 ▼
   ┌───────────────────┐             ┌───────────────────┐             ┌───────────────────┐
   │    SIMT Engine    │             │  2x2 AI Systolic  │             │   DMA Controller  │
   │  4 Parallel Lanes │             │    Matrix Core    │             │  Burst Mover Bus  │
   │ (PE0,PE1,PE2,PE3) │             │  (4 DSP MAC Units)│             │ (Zero Core Stall) │
   │  R0-R7 GPR Files  │             │  4 Clock Cycles   │             │   1 + N Cycles    │
   └─────────┬─────────┘             └─────────┬─────────┘             └─────────┬─────────┘
             │                                 │                                 │
             └──────────────────┐              │              ┌──────────────────┘
                                ▼              ▼              ▼
                         ┌──────────────────────────────────────────────┐
                         │       Synchronous Dual-Port Block RAM        │
                         │    4096 Words x 16-Bit = 8 Kilobytes (KB)    │
                         ├──────────────────────────────────────────────┤
                         │ Address 0-1023    : 32x32 Video Framebuffer  │
                         │ Address 1100-1115 : Layer 1 Weights (4x4)    │
                         │ Address 1120-1127 : Layer 2 Weights (4x2)    │
                         │ Address 1130-1133 : Sensor Inputs [X,Y,Py,Dy]│
                         │ Address 1140-1143 : Hidden Activations (H0-3)│
                         │ Address 1150-1151 : Output Action Logits     │
                         └──────────────────────────────────────────────┘
```

---

## 📊 Benchmarks & Empirical Results

Evaluated against the Python Architectural Golden Model and SystemVerilog RTL:

| Benchmark Workload | Standard SIMT Baseline | HeteroGPU Specialized Core | Hardware Speedup | Hardware Advantage |
|---|---|---|---|---|
| **4x4 GEMM (Matrix Multiply)** | 92 clock cycles | **16 clock cycles** | **5.75x FASTER** | Dedicated 2D Systolic streaming eliminates loop/broadcast overhead |
| **64-Word Memory Block Copy** | 80 clock cycles | **65 clock cycles** | **1.23x FASTER** | Autonomous DMA burst transfer; **compute cores are 100% free** |
| **End-to-End AI Forward Pass** | 110 clock cycles | **34 clock cycles** | **3.24x FASTER** | Smooth 60+ FPS real-time trajectory interception |

### Workload Breakdown in 34 Clock Cycles:
* **70.6% (24 cycles):** Dense matrix multiplications (Layer 1 + Layer 2) on 2x2 Systolic Array.
* **14.7% (5 cycles):** Parallel non-linear ReLU activation across 4 SIMT cores.
* **14.7% (5 cycles):** Sensor input staging via hardware DMA.

---

## 📁 Repository Structure

```text
HeteroGPU/
│
├── python_test_simulator/          # Phase 1: Python Architectural Golden Model & Visualizer
│   ├── processing_element.py       # 16-bit ALU & R0-R7 GPR model
│   ├── memory.py                   # 4096-word BRAM model with bounds checking
│   ├── simt_engine.py              # 4-core parallel instruction broadcast
│   ├── matrix_engine.py            # 2x2 Systolic Array MAC engine
│   ├── dma_engine.py               # Cycle-accurate DMA burst mover
│   ├── heterogpu.py                # Top-level SoC controller & telemetry
│   ├── ai_model.py                 # Quantized 2-layer MLP neural network policy
│   ├── game_demo.py                # Interactive 4-mode Pygame HUD showcase
│   ├── benchmark.py                # Academic cycle benchmark suite
│   ├── generate_graphs.py          # Automated 300 DPI publication chart generator
│   └── run_demo.py                 # Unified simulator launcher
│
├── rtl/                            # Phase 2: Synthesizable SystemVerilog RTL
│   ├── pe_core.sv                  # 16-bit execution lane with GPR file
│   ├── simt_engine.sv              # 4-lane SIMT array with vector load/store
│   ├── systolic_array_2x2.sv       # 2x2 Tensor Processing Unit (4 DSP blocks)
│   ├── dma_controller.sv           # Hardware burst memory controller
│   ├── bram_memory.sv              # 8 KB dual-port Block RAM (Gowin BSRAM)
│   └── heterogpu_top.sv            # Top-level SoC interconnect & arbiter
│
├── sim/                            # Verification Testbenches
│   └── tb_heterogpu.sv             # RTL verification testbench against Golden Model
│
├── fpga/                           # Phase 3: Physical FPGA Synthesis Constraints
│   └── tangnano9k/
│       ├── tangnano9k.cst          # Physical pin constraints (HDMI, clock, buttons)
│       └── tangnano9k.sdc          # 27 MHz timing constraints
│
├── REFERENCES.md                   # Curated bibliography (TPU, Volta, Kung & Leiserson)
└── PROJECT_SUMMARY.md              # Project specifications & scope
```

---

## 🚀 Quickstart Guide

### 1. Run the Python Simulator & Interactive HUD
Requirements: Python 3.8+ and Pygame (`pip install pygame matplotlib numpy`).

```powershell
# Launch interactive 4-mode Pygame visualizer
py python_test_simulator/run_demo.py

# Run academic cycle benchmark suite
py python_test_simulator/run_demo.py --bench

# Generate publication-quality 300 DPI graphs
py python_test_simulator/run_demo.py --graph
```

### 2. Verify SystemVerilog RTL in Simulation
Simulate with any standard Verilog simulator (Icarus Verilog, ModelSim, Verilator):

```bash
# Compile and run testbench with Icarus Verilog
iverilog -g2012 -o sim/heterogpu_sim rtl/*.sv sim/tb_heterogpu.sv
vvp sim/heterogpu_sim

# View waveform traces in GTKWave
gtkwave sim/waves.vcd
```

### 3. Synthesize for Sipeed Tang Nano 9K
1. Open **Gowin EDA (v1.9.9+)**.
2. Create project targeting device **GW1NR-LV9QN88PC6/I5**.
3. Add all SystemVerilog files from `rtl/`.
4. Add physical constraints from `fpga/tangnano9k/tangnano9k.cst` and `tangnano9k.sdc`.
5. Run **Place & Route** to generate the `.fs` bitstream.

---

## 🎯 Target FPGA Budget (Tang Nano 9K / Gowin GW1NR-9)

| FPGA Resource | Tang Nano 9K Capacity | HeteroGPU Budget | Utilization |
|---|---|---|---|
| **LUT4 Logic** | 8,640 | ~2,850 LUTs | **33.0%** |
| **Registers (FFs)** | 6,480 | ~1,200 FFs | **18.5%** |
| **DSP Blocks (MULT18x18)** | 20 | 4 DSPs | **20.0%** |
| **Block RAM (BSRAM)** | 26 blocks (468 Kbits) | 4 to 5 blocks (65.5 Kbits / 8 KB) | **19.2%** |

---

## 📚 Academic References & Literature
* **Jouppi et al. (ISCA 2017):** *In-Datacenter Performance Analysis of a Tensor Processing Unit (TPU).*
* **Kung & Leiserson (1979):** *Systolic Arrays (for VLSI).*
* **Choquette et al. (IEEE Micro 2018):** *Volta: The First GPU Architecture with Tensor Cores.*
* Full citations available in [REFERENCES.md](REFERENCES.md).
