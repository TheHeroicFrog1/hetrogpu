"""
HeteroGPU Unified Demonstration Launcher
Run this script to launch the full graphical demo or benchmark suite.
Usage:
    py run_demo.py         -> Launches Interactive AI Game Demo with Live Telemetry HUD
    py run_demo.py --bench -> Runs Architectural Benchmarks and Speedup Analysis
"""

import sys
import os

# Add simulator directory to Python path
sim_path = os.path.join(os.path.dirname(__file__), "simulator")
sys.path.insert(0, sim_path)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ("--bench", "-b", "--benchmark"):
        import benchmark
        print("Launching HeteroGPU Academic Benchmarks...\n")
        benchmark.benchmark_matrix_multiplication()
        benchmark.benchmark_dma_transfer()
        benchmark.benchmark_ai_inference()
    else:
        import game_demo
        print("Starting HeteroGPU Interactive Live Demonstration...")
        demo = game_demo.HeteroGPUDemo()
        demo.run()
