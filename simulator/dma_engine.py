# Direct Memory Access (DMA) engine
# Handles fast burst copies between memory blocks so compute cores aren't stalled

class DMAEngine:
    def __init__(self, name="DMA_0"):
        self.name = name
        self.total_cycles = 0

    def transfer(self, memory, src_addr, dest_addr, length):
        # burst transfer: 1 setup cycle + 1 cycle per 16-bit word
        buffer = []
        for i in range(length):
            buffer.append(memory.read(src_addr + i))

        for i in range(length):
            memory.write(dest_addr + i, buffer[i])

        cycles = 1 + length
        self.total_cycles += cycles
        return cycles

    def load_host_data(self, memory, host_data, dest_addr):
        # simulates host CPU writing weights or inputs into GPU memory
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

    for i in range(8):
        mem.write(10 + i, (i + 1) * 10)

    cyc = dma.transfer(mem, src_addr=10, dest_addr=50, length=8)
    assert mem.dump(10, 18) == mem.dump(50, 58)
    print(f"DMA transfer test passed in {cyc} cycles!")
