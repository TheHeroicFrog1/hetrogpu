# ==============================================================================
# HeteroGPU: Top-Level System-on-Chip (SoC) Controller
# Architecture: Heterogeneous accelerator integrating 3 hardware engines over shared BRAM:
#   1. 4-core SIMT Vector Engine (graphics shaders, general arithmetic, parallel ReLU)
#   2. 2x2 Systolic Array AI Engine (matrix multiplication / GEMM acceleration)
#   3. Direct Memory Access (DMA) Burst Controller (zero-core-overhead data movement)
# Memory Architecture: Memory-Mapped I/O (MMIO) with dedicated address segments.
# ==============================================================================

from memory import Memory
from processing_element import ProcessingElement
from simt_engine import SIMTEngine
from matrix_engine import MatrixEngine
from dma_engine import DMAEngine

class HeteroGPU:
    # --------------------------------------------------------------------------
    # Memory-Mapped I/O (MMIO) Address Map (Total Address Space: 4096 Words / 8 KB)
    # --------------------------------------------------------------------------
    FRAMEBUFFER_BASE  = 0     # Words 0 - 1023: 32x32 Video Framebuffer (1024 pixels)
    AI_WEIGHTS_L1     = 1100  # Words 1100 - 1115: 4x4 Layer 1 Synaptic Weights
    AI_WEIGHTS_L2     = 1120  # Words 1120 - 1127: 4x2 Layer 2 Synaptic Weights
    AI_INPUT_BUFFER   = 1130  # Words 1130 - 1133: Sensor State Input Vector [X, Y, Py, Dy]
    AI_L1_ACTIVATIONS = 1140  # Words 1140 - 1143: Hidden Layer Post-Activation Neurons (H0-H3)
    AI_OUTPUT_BUFFER  = 1150  # Words 1150 - 1151: Output Action Logits [UP, DOWN]

    def __init__(self, memory_size=4096):
        # 4096 words = 8 KB BRAM (synthesizable on Tang Nano 9K / Gowin GW1NR-9)
        self.memory = Memory(size_words=memory_size)
        self.simt = SIMTEngine(num_cores=4)
        self.matrix_engine = MatrixEngine(size=2)
        self.dma = DMAEngine(name="DMA_0")
        self.reset_telemetry()

    def reset_telemetry(self):
        # Clears hardware cycle profiling registers before executing a workload
        self.simt_cycles = 0
        self.ai_cycles = 0
        self.dma_cycles = 0
        self.total_instructions = 0

    def run_simt(self, instruction):
        # Dispatches instruction to 4-lane SIMT pipeline
        c = self.simt.execute(instruction, self.memory)
        self.simt_cycles += c
        self.total_instructions += 1
        return c

    def run_parallel_relu(self, base_addr, length=4):
        # Dispatches vectorized ReLU activation across SIMT cores (5 cycles for 4 elements)
        c = self.simt.parallel_relu(self.memory, base_addr, length)
        self.simt_cycles += c
        self.total_instructions += (length // 4) * 3
        return c

    def run_matrix_linear(self, in_addr, in_dim, weight_addr, out_dim, out_addr):
        # Dispatches fully connected neural network layer to 2x2 Systolic Array
        res, c = self.matrix_engine.dense_linear_layer(
            self.memory, in_addr, in_dim, weight_addr, out_dim, out_addr
        )
        self.ai_cycles += c
        self.total_instructions += 1
        return res, c

    def run_dma_transfer(self, src_addr, dest_addr, length):
        # Triggers autonomous DMA burst transfer across BRAM locations
        c = self.dma.transfer(self.memory, src_addr, dest_addr, length)
        self.dma_cycles += c
        self.total_instructions += 1
        return c

    def run_dma_load(self, host_data, dest_addr):
        # Simulates host interface streaming data directly into GPU BRAM
        c = self.dma.load_host_data(self.memory, host_data, dest_addr)
        self.dma_cycles += c
        self.total_instructions += 1
        return c

    def get_telemetry(self):
        # Hardware Telemetry: Returns cycle consumption and percentage breakdown per engine
        total = self.simt_cycles + self.ai_cycles + self.dma_cycles
        if total == 0:
            return {"SIMT": 0, "AI": 0, "DMA": 0, "TOTAL": 0}
        return {
            "SIMT_CYCLES": self.simt_cycles,
            "AI_CYCLES": self.ai_cycles,
            "DMA_CYCLES": self.dma_cycles,
            "TOTAL_CYCLES": total,
            "SIMT_PCT": round((self.simt_cycles / total) * 100, 1),
            "AI_PCT": round((self.ai_cycles / total) * 100, 1),
            "DMA_PCT": round((self.dma_cycles / total) * 100, 1),
        }


if __name__ == '__main__':
    # Verify top-level SoC instantiation
    gpu = HeteroGPU()
    print("HeteroGPU SoC initialized successfully!")
    print(f"BRAM: {gpu.memory.size_words} words (16-bit)")
    print(f"SIMT PEs: {gpu.simt.num_cores}")
    print(f"AI Unit: {gpu.matrix_engine.size}x{gpu.matrix_engine.size} systolic MAC array")
