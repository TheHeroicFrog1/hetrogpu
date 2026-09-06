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

## Current Status (Phase 1: Python Simulator)
Location: `simulator/`
- [x] `processing_element.py`: 16-bit ALU (ADD, SUB, MUL, AND, OR, XOR, LOAD, STORE) with 8 registers (R0-R7).
- [x] `memory.py`: 16-bit shared memory model simulating FPGA Block RAM.
- [x] `simt_engine.py`: 4-core parallel SIMT execution engine with `LOAD_PARALLEL`, `STORE_PARALLEL`, and broadcast arithmetic. Verified with vector addition test workload `[5, 10, 15, 20] + [1, 2, 3, 4] = [6, 12, 18, 24]`.
- [ ] `matrix_engine.py`: 2x2 MAC grid.
- [ ] `dma_engine.py`: Block memory transfer engine.
- [ ] `controller.py`: Workload dispatcher / scheduler.
- [ ] 2D Display / Pygame demo framebuffer.

---

## Conversation ID Reference
- Conversation ID: `bd568dfc-0c97-4ebb-b7bf-3d6a809e4779`
