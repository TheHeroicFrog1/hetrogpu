# HeteroGPU: Viva & Presentation Defense Guide

Use this cheatsheet when presenting to your professor tomorrow.

---

## 1. The 30-Second Elevator Pitch
> *"Sir/Ma'am, modern computing workloads are no longer purely sequential or purely parallel—they combine SIMT graphics, matrix-heavy neural networks, and massive memory transfers. Our project, **HeteroGPU**, investigates whether a heterogeneous architecture combining a **SIMT execution engine**, a **specialized systolic AI matrix engine**, and a **DMA engine** can dramatically out-perform a traditional homogeneous GPU on budget hardware."*

---

## 2. Key Numbers & Benchmarks to Quote

| Metric | SIMT Baseline | HeteroGPU Specialized | Improvement |
| :--- | :--- | :--- | :--- |
| **4x4 GEMM (Matrix Multiply)** | 96 Clock Cycles | **16 Clock Cycles** | **6.0x Speedup** |
| **Memory Block Transfer (64 words)** | 80 Clock Cycles | **65 Clock Cycles** | **1.23x Faster + 100% Core Offload** |
| **Neural Network Inference Pass** | ~110 Cycles | **34 Clock Cycles** | **3.2x Overall Speedup** |
| **Target Architecture** | 16-Bit Word Width | 4 SIMT PEs + 2x2 Systolic Array | Synthesizable on Tang Nano 9K |

---

## 3. How to Demonstrate It Live

### Option A: The Visual Showpiece (Game + Live Telemetry HUD)
In terminal:
```powershell
cd C:\Users\aadit\HeteroGPU
py run_demo.py
```
* **What to point at on screen:**
  1. **The Game Arena (Left):** The ball and paddle are being rendered directly to the 32x32 framebuffer by the **4-core SIMT engine**.
  2. **The Autonomous Paddle:** The paddle is controlled in real-time by a **quantized 2-layer neural network**.
  3. **The Live HUD (Right):** Show the real-time utilization bars. Point out how the **Matrix Engine handles GEMM (~70%)**, the **SIMT handles parallel ReLU activations (~15%)**, and the **DMA transfers inputs (~15%)**.

### Option B: The Academic Benchmark Table
In terminal:
```powershell
cd C:\Users\aadit\HeteroGPU
py run_demo.py --bench
```
* Shows the cycle-by-cycle proof of the **6.0x hardware speedup**.

---

## 4. Likely Viva Questions & Answers

### Q1: *"Why not just use the SIMT cores for matrix multiplication like normal GPUs do?"*
> **Answer:** *"A general SIMT core has to repeatedly fetch instructions, decode operands, and execute individual multiply and add instructions through general register files. Our 2x2 Matrix Engine is a **systolic array** where data streams directly between multiply-accumulate (MAC) units with zero instruction fetch overhead and high data reuse, achieving a **6x cycle reduction**."*

### Q2: *"Why is the DMA engine important in a GPU?"*
> **Answer:** *"Without DMA, our SIMT processing elements would spend clock cycles stalled on sequential memory loads and stores instead of doing math. The DMA engine provides burst transfers directly between host memory and BRAM over a shared bus, freeing 100% of compute cores."*

### Q3: *"How does this map to physical FPGA hardware?"*
> **Answer:** *"The entire architecture is designed with strict 16-bit word widths and a 2x2 MAC grid specifically to fit within the 8,640 LUT logic budget of a low-cost Gowin FPGA (Tang Nano 9K/20K), using Block RAM (BRAM) for memory and DSP slices for the MAC units."*
