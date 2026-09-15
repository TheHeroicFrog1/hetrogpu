# Launcher script for the HeteroGPU demo and benchmarks
# Usage:
#   py run_demo.py         (opens interactive 4-mode game/shader demo)
#   py run_demo.py --bench (runs terminal benchmark suite)
#   py run_demo.py --graph (generates and opens matplotlib graphs)

import sys
import os

# ensure python_test_simulator directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import benchmark
import game_demo
import generate_graphs

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    # benchmark mode
    if args and args[0] in ("--bench", "-b", "--benchmark"):
        print("Running HeteroGPU benchmarks...")
        benchmark.benchmark_matrix_multiplication()
        benchmark.benchmark_dma_transfer()
        benchmark.benchmark_ai_inference()

    # plot graphs mode
    elif args and args[0] in ("--graph", "-g", "--graphs"):
        print("Plotting benchmark graphs...")
        img_path = generate_graphs.generate_all_plots()
        os.system(f'start "" "{img_path}"')

    # default: interactive pygame showcase
    else:
        print("Starting HeteroGPU demo window...")
        demo = game_demo.HeteroGPUMultiDemo()
        demo.run()

if __name__ == '__main__':
    main()
