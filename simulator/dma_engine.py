# simulator/dma_engine.py

class DMAEngine:
    def __init__(self, name="DMA_Engine"):
        """Simulates Direct Memory Access for fast block transfers."""
        self.name = name
        self.total_cycles = 0

    def transfer(self, memory, src_addr, dest_addr, length):
        """
        Copies 'length' words from src_addr to dest_addr independently.
        Hardware burst transfer: 1 setup cycle + 1 cycle per 16-bit word.
        """
        buffer = []
        # Burst Read
        for i in range(length):
            buffer.append(memory.read(src_addr + i))
            
        # Burst Write
        for i in range(length):
            memory.write(dest_addr + i, buffer[i])

        cycles = 1 + length  # 1 setup cycle + N word transfers
        self.total_cycles += cycles
        return cycles

    def load_host_data(self, memory, host_data, dest_addr):
        """Simulates host CPU transferring pre-trained AI weights or assets into GPU memory."""
        length = len(host_data)
        for i, val in enumerate(host_data):
            # Store as 16-bit unsigned
            u16 = val & 0xFFFF
            memory.write(dest_addr + i, u16)
        cycles = 1 + length
        self.total_cycles += cycles
        return cycles


if __name__ == '__main__':
    from memory import Memory
    mem = Memory(size_words=1024)
    dma = DMAEngine()

    for i in range(10):
        mem.write(50 + i, i * 10)

    cyc = dma.transfer(mem, src_addr=50, dest_addr=200, length=10)
    print(f"DMA Transfer complete in {cyc} cycles.")
    assert mem.dump(start=50, end=60) == mem.dump(start=200, end=210)
    print("DMA Engine Test Passed!")
