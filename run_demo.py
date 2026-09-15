# Top-level launcher forwarding to python_test_simulator
# Usage:
#   py run_demo.py         (opens interactive 4-mode game/shader demo)
#   py run_demo.py --bench (runs terminal benchmark suite)
#   py run_demo.py --graph (generates and opens matplotlib graphs)

import sys
import os

sim_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "python_test_simulator")
if sim_path not in sys.path:
    sys.path.insert(0, sim_path)

if __name__ == '__main__':
    import run_demo as sim_launcher
    sim_launcher.main()

