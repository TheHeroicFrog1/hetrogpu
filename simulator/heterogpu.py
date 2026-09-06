# simulator/heterogpu.py
from memory import Memory
from processing_element import ProcessingElement
from simt_engine import SIMTEngine
from matrix_engine import MatrixEngine
from dma_engine import DMAEngine

class HeteroGPU:
    """
    HeteroGPU Top-Level SoC Architecture:
    - 2048 x 16-bit Shared BRAM
    - 4-Core SIMT Execution Array
    - 2x2 AI Matrix Engine (Systolic Array)
    - High-Bandwidth DMA Engine
    - Hardware Cycle Telemetry System
    """

    # Memory Address Map
    FRAMEBUFFER_BASE = 0      # 0 - 1023 (32x32 pixels)
    AI_WEIGHTS_L1    = 1100   # 1100 - 1115 (4x4 Layer 1 weights = 16 words)
    AI_WEIGHTS_L2    = 1120   # 1120 - 1127 (4x2 Layer 2 weights = 8 words)
    AI_INPUT_BUFFER  = 1130   # 1130 - 1133 (Input state = 4 words)
    AI_L1_ACTIVATIONS = 1140  # 1140 - 1143 (Hidden layer activations = 4 words)
    AI_OUTPUT_BUFFER = 1150   # 1150 - 1151 (Output decisions = 2 words)

    def __init__(self, memory_size=4096):
        self.memory = Memory(size_words=memory_size)
        self.simt = SIMTEngine(num_cores=4)
        self.matrix_engine = MatrixEngine(size=2)
        self.dma = DMAEngine(name="DMA_0")
        
        # Telemetry
        self.reset_telemetry()

    def reset_telemetry(self):
        self.simt_cycles = 0
        self.ai_cycles = 0
        self.dma_cycles = 0
        self.total_instructions = 0

    def run_simt(self, instruction):
        c = self.simt.execute(instruction, self.memory)
        self.simt_cycles += c
        self.total_instructions += 1
        return c

    def run_parallel_relu(self, base_addr, length=4):
        c = self.simt.parallel_relu(self.memory, base_addr, length)
        self.simt_cycles += c
        self.total_instructions += (length // 4) * 3
        return c

    def run_matrix_linear(self, in_addr, in_dim, weight_addr, out_dim, out_addr):
        res, c = self.matrix_engine.dense_linear_layer(
            self.memory, in_addr, in_dim, weight_addr, out_dim, out_addr
        )
        self.ai_cycles += c
        self.total_instructions += 1
        return res, c

    def run_dma_transfer(self, src_addr, dest_addr, length):
        c = self.dma.transfer(self.memory, src_addr, dest_addr, length)
        self.dma_cycles += c
        self.total_instructions += 1
        return c

    def run_dma_load(self, host_data, dest_addr):
        c = self.dma.load_host_data(self.memory, host_data, dest_addr)
        self.dma_cycles += c
        self.total_instructions += 1
        return c

    def get_telemetry(self):
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
    gpu = HeteroGPU()
    print("HeteroGPU SoC successfully initialized!")
    print(f"Memory: {gpu.memory.size_words} 16-bit words")
    print(f"SIMT Cores: {gpu.simt.num_cores}")
    print(f"AI Engine: {gpu.matrix_engine.size}x{gpu.matrix_engine.size} MAC Array")
