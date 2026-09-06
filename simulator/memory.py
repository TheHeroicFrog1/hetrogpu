# simulator/memory.py

class Memory:
    def __init__(self, size_words=1024):
        """
        Simulates FPGA Block RAM (Shared Memory).
        size_words: Number of 16-bit words in memory.
        """
        self.size_words = size_words
        # 16-bit memory, initialized to 0
        self.data = [0] * size_words
        
    def read(self, address):
        """Reads a 16-bit word from the given address."""
        if 0 <= address < self.size_words:
            return self.data[address]
        raise IndexError(f"Memory read out of bounds: {address}")
        
    def write(self, address, value):
        """Writes a 16-bit word to the given address."""
        if 0 <= address < self.size_words:
            # Enforce 16-bit unsigned limit
            self.data[address] = value & 0xFFFF
        else:
            raise IndexError(f"Memory write out of bounds: {address}")
            
    def dump(self, start=0, end=16):
        """Helper to print memory contents."""
        return self.data[start:end]

if __name__ == '__main__':
    mem = Memory(size_words=256)
    mem.write(10, 65535)
    mem.write(11, 42)
    print(f"Memory at addr 10: {mem.read(10)}")
    print(f"Memory at addr 11: {mem.read(11)}")
