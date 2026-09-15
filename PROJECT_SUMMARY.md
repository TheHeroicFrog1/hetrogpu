# HeteroGPU — Heterogeneous GPU Architecture

## Overview
HeteroGPU is a heterogeneous GPU architecture combining SIMT processing cores with specialized AI/matrix and data-movement (DMA) engines for a 3rd-year VLSI mini-project (expanding to a 4th-year capstone).

### Key Architecture Components
1. **Controller / Scheduler**: Coordinates task distribution between SIMT, AI/Matrix, and DMA engines.
2. **SIMT Engine**: 4 parallel Processing Elements (PEs) executing SIMD/SIMT instructions across threads with parallel memory load/store.
3. **AI/Matrix Engine**: 2x2 Multiply-Accumulate (MAC) systolic array for accelerating tensor/matrix calculations.
4. **DMA Engine**: Offloads block memory transfers to prevent compute unit stalls.
5. **Shared Memory**: Simulates FPGA Block RAM (BRAM) using a 16-bit word addressable space.
6. **2D Graphics / Framebuffer**: Direct memory mapping for 2D retro gaming demonstration (Pong, Space Invaders).

---

## Hardware Target & Tradeoffs
- **Target Board**: Sipeed Tang Nano 9K / 20K (Gowin FPGA, ~8.6K to 20K LUTs).
- **Video Output**: On-board HDMI output.
- **Precision**: Strict 16-bit unsigned integer arithmetic (0 to 65535, with wraparound).
- **Scope Tradeoffs**:
  - Integer / fixed-point math only (no complex floating-point units).
  - 2D framebuffer rendering directly to memory (no 3D vertex/rasterization pipeline).
  - BRAM-based shared memory (no multi-level cache coherency protocols).

---

## Current Status (Phase 1: Python Test Simulator)
Location: `python_test_simulator/`
- [x] `processing_element.py`: 16-bit ALU (ADD, SUB, MUL, AND, OR, XOR, RELU, CMP_GT, MAX, LOAD, STORE) with 8 registers (R0-R7).
- [x] `memory.py`: 16-bit shared memory model simulating FPGA Block RAM (4096 words / 8 KB).
- [x] `simt_engine.py`: 4-core parallel SIMT execution engine with `LOAD_PARALLEL`, `STORE_PARALLEL`, broadcast arithmetic, and parallel ReLU.
- [x] `matrix_engine.py`: 2x2 Systolic Array MAC unit (4 cycles).
- [x] `dma_engine.py`: Block memory transfer burst engine (1 + N cycles).
- [x] `heterogpu.py`: Top-level SoC controller and cycle telemetry counters.
- [x] `ai_model.py`: Quantized 2-layer MLP neural network brain.
- [x] `game_demo.py`: Interactive 4-mode Pygame showcase with real-time HUD telemetry.
- [x] `benchmark.py`: Academic benchmarking suite (5.75x speedup measured).
- [x] `generate_graphs.py`: Automated 300 DPI Matplotlib evaluation charts.

---

## Conversation ID Reference
- Conversation ID: `bd568dfc-0c97-4ebb-b7bf-3d6a809e4779`
