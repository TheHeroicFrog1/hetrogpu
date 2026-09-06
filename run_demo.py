# Launcher script for the HeteroGPU demo and benchmarks
# Usage:
#   py run_demo.py         (opens interactive 4-mode game/shader demo)
#   py run_demo.py --bench (runs terminal benchmark suite)
#   py run_demo.py --graph (generates and opens matplotlib graphs)

import sys
import os

# add simulator folder to path
sim_path = os.path.join(os.path.dirname(__file__), "simulator")
sys.path.insert(0, sim_path)

if __name__ == '__main__':
    args = sys.argv[1:]

    # benchmark mode
    if args and args[0] in ("--bench", "-b", "--benchmark"):
        import benchmark
        print("Running HeteroGPU benchmarks...")
        benchmark.benchmark_matrix_multiplication()
        benchmark.benchmark_dma_transfer()
        benchmark.benchmark_ai_inference()

    # plot graphs mode
    elif args and args[0] in ("--graph", "-g", "--graphs"):
        import generate_graphs
        print("Plotting benchmark graphs...")
        img_path = generate_graphs.generate_all_plots()
        os.system(f'start "" "{img_path}"')

    # default: interactive pygame showcase
    else:
        import game_demo
        print("Starting HeteroGPU demo window...")
        demo = game_demo.HeteroGPUMultiDemo()
        demo.run()
