# ==============================================================================
# Direct Memory Access (DMA) Burst Controller
# Architecture: Hardware Bus Master that executes bulk BRAM block copies.
# Motivation: Offloads memory transfers from SIMT and Matrix engines so compute units
#             experience zero stall cycles and remain 100% available for execution.
# ==============================================================================

class DMAEngine:
    def __init__(self, name="DMA_0"):
        self.name = name
        self.total_cycles = 0  # Global cycle counter for memory transfer benchmarking

    def transfer(self, memory, src_addr, dest_addr, length):
        # ----------------------------------------------------------------------
        # Hardware DMA Burst Transfer:
        # Latency Equation: T_dma = 1 (Bus Arbitration / Setup) + N (Burst Word Cycles)
        # For 64 words: 1 + 64 = 65 clock cycles (vs. 80 cycles with SIMT polling).
        # ----------------------------------------------------------------------
        
        # Read phase: Auto-incrementing source address pointer streaming into internal FIFO
        buffer = []
        for i in range(length):
            buffer.append(memory.read(src_addr + i))

        # Write phase: Auto-incrementing destination address pointer flushing to BRAM
        for i in range(length):
            memory.write(dest_addr + i, buffer[i])

        cycles = 1 + length  # 1 setup cycle + 1 cycle per 16-bit word
        self.total_cycles += cycles
        return cycles

    def load_host_data(self, memory, host_data, dest_addr):
        # ----------------------------------------------------------------------
        # Host CPU to GPU BRAM Interface (Simulates PCIe / SPI / UART staging):
        # Direct loading of neural network weights or sensor states into GPU memory.
        # ----------------------------------------------------------------------
        length = len(host_data)
        for i, val in enumerate(host_data):
            memory.write(dest_addr + i, val & 0xFFFF)
        cycles = 1 + length
        self.total_cycles += cycles
        return cycles


if __name__ == '__main__':
    from memory import Memory
    mem = Memory(size_words=256)
    dma = DMAEngine()

    # Write initial data to source address
    for i in range(8):
        mem.write(10 + i, (i + 1) * 10)

    # Perform 8-word DMA burst copy (should take 1 + 8 = 9 cycles)
    cyc = dma.transfer(mem, src_addr=10, dest_addr=50, length=8)
    assert mem.dump(10, 18) == mem.dump(50, 58)
    assert cyc == 9
    print(f"DMA transfer test passed in {cyc} cycles!")
