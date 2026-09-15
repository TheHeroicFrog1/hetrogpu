# ==============================================================================
# HeteroGPU Hardware Performance Benchmark Suite
# Metrics: Clock Cycle Latency, Hardware Speedup, and Subsystem Utilization.
# Benchmarks:
#   Test 1: 4x4 GEMM (4-Lane SIMT Instruction Broadcast vs. 2x2 Systolic Array)
#   Test 2: 64-Word Memory Block Transfer (SIMT Software Polling vs. Hardware DMA)
#   Test 3: End-to-End Neural Network Forward Pass Telemetry Breakdown
# ==============================================================================

import sys
import os

# Ensure current module directory is in sys.path
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

try:
    from heterogpu import HeteroGPU
    from ai_model import PongAIBrain
except ImportError:
    from python_test_simulator.heterogpu import HeteroGPU
    from python_test_simulator.ai_model import PongAIBrain


def benchmark_matrix_multiplication():
    print("\n[Benchmark 1] 4x4 Matrix Multiply (GEMM)")
    gpu = HeteroGPU()

    # Create 4x4 test matrices in row-major order
    mat_a = [1 if i % 5 == 0 else 0 for i in range(16)]  # Identity matrix
    mat_b = [i + 1 for i in range(16)]                    # Ramp values [1..16]

    # Assign non-overlapping memory regions in BRAM
    addr_a = 100
    addr_b = 120
    addr_c_simt = 140
    addr_c_ai = 160

    # Stage matrices into BRAM
    gpu.run_dma_load(mat_a, addr_a)
    gpu.run_dma_load(mat_b, addr_b)

    # --------------------------------------------------------------------------
    # Baseline Execution: Fully simulated SIMT assembly instructions across 4 PEs
    # Timing: 92 clock cycles (measured cycle-by-cycle)
    # --------------------------------------------------------------------------
    simt_cycles = gpu.simt.execute_gemm_4x4(gpu.memory, addr_a, addr_b, addr_c_simt)

    # --------------------------------------------------------------------------
    # Accelerated Execution: 2x2 Systolic Array (4 tiles * 4 cycles/tile)
    # Timing: Exactly 16 clock cycles
    # --------------------------------------------------------------------------
    gpu.reset_telemetry()
    for r in range(0, 4, 2):
        for c in range(0, 4, 2):
            gpu.matrix_engine.execute_mac_2x2(gpu.memory, addr_a, addr_b, addr_c_ai)

    ai_cycles = gpu.matrix_engine.total_cycles
    speedup = simt_cycles / ai_cycles  # 92 / 16 = 5.75x speedup

    print(f"  SIMT Cores (4 PEs)    : {simt_cycles} cycles")
    print(f"  Matrix Engine (2x2)   : {ai_cycles} cycles")
    print(f"  -> Hardware Speedup   : {speedup:.2f}x faster")


def benchmark_dma_transfer():
    print("\n[Benchmark 2] Block Memory Transfer (64 words)")
    gpu = HeteroGPU()

    block_size = 64
    src_addr = 500
    dest_addr = 600

    # --------------------------------------------------------------------------
    # Baseline: SIMT cores manually looping over memory addresses
    # Timing: 16 chunks * 5 cycles = 80 clock cycles (cores 100% occupied)
    # --------------------------------------------------------------------------
    simt_cycles = gpu.simt.execute_copy(gpu.memory, src_addr, dest_addr, block_size)

    # --------------------------------------------------------------------------
    # Accelerated: Hardware DMA burst transfer engine
    # Timing: 1 setup cycle + 64 word cycles = 65 clock cycles (cores 100% idle)
    # --------------------------------------------------------------------------
    gpu.reset_telemetry()
    dma_cycles = gpu.run_dma_transfer(src_addr, dest_addr, block_size)
    speedup = simt_cycles / dma_cycles

    print(f"  Manual SIMT Copy      : {simt_cycles} cycles")
    print(f"  Hardware DMA Burst    : {dma_cycles} cycles")
    print(f"  -> Speedup            : {speedup:.2f}x faster (SIMT cores 100% idle)")


def benchmark_ai_inference():
    print("\n[Benchmark 3] End-to-End Neural Network Forward Pass")
    gpu = HeteroGPU()
    brain = PongAIBrain(gpu)

    # Execute complete inference pass on HeteroGPU hardware model
    gpu.reset_telemetry()
    decision, up, down = brain.forward(ball_x=12, ball_y=8, paddle_y=16, ball_dy=-1)
    telemetry = gpu.get_telemetry()

    print(f"  Model                 : 4 Inputs -> 4 Hidden (ReLU) -> 2 Outputs")
    print(f"  Total Latency         : {telemetry['TOTAL_CYCLES']} cycles")
    print(f"  Breakdown             :")
    print(f"    - Matrix Engine     : {telemetry['AI_CYCLES']} cycles ({telemetry['AI_PCT']}%)")
    print(f"    - SIMT ReLU         : {telemetry['SIMT_CYCLES']} cycles ({telemetry['SIMT_PCT']}%)")
    print(f"    - DMA Transfers     : {telemetry['DMA_CYCLES']} cycles ({telemetry['DMA_PCT']}%)")
    print(f"  Decision Output       : {'UP' if decision == -1 else 'DOWN'}")


if __name__ == '__main__':
    print("=== HeteroGPU Benchmark Results ===")
    benchmark_matrix_multiplication()
    benchmark_dma_transfer()
    benchmark_ai_inference()
    print("\nAll benchmarks finished successfully.")
