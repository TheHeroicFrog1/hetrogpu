# ==============================================================================
# Unified GPU Memory Architecture (FPGA Block RAM / BRAM Model)
# Hardware Target: Gowin GW1NR-9 (Tang Nano 9K).
# Total Capacity: 4096 words x 16 bits = 65,536 bits = 8 Kilobytes (KB).
# Uses 4 to 5 primitive BSRAM blocks, leaving plenty of room for bitstream logic.
# ==============================================================================

class Memory:
    def __init__(self, size_words=4096):
        # Memory address space size in 16-bit words
        self.size_words = size_words
        # 16-bit synchronous memory array (initialized to 0 on FPGA reset)
        self.data = [0] * size_words

    def read(self, address):
        # Synchronous BRAM Read: Single clock cycle access
        # Address Range Check prevents memory corruption and bounds violations
        if 0 <= address < self.size_words:
            return self.data[address]
        raise IndexError(f"Hardware Memory Bus Error: Read address {address} out of bounds (0 - {self.size_words - 1})")

    def write(self, address, value):
        # Synchronous BRAM Write:
        # Applies 16-bit word mask (& 0xFFFF) to simulate data wire bus truncation
        if 0 <= address < self.size_words:
            self.data[address] = value & 0xFFFF
        else:
            raise IndexError(f"Hardware Memory Bus Error: Write address {address} out of bounds (0 - {self.size_words - 1})")

    def dump(self, start=0, end=16):
        # Debugging helper: inspects contiguous memory slices (useful for testbenches)
        return self.data[start:end]


if __name__ == '__main__':
    # Testbench for memory reads, writes, and 16-bit bus masking
    mem = Memory(size_words=256)
    mem.write(10, 65535)  # Max 16-bit unsigned (0xFFFF)
    mem.write(11, 42)
    assert mem.read(10) == 65535
    assert mem.read(11) == 42
    print("Memory tests passed!")
