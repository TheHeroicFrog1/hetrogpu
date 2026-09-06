# Simple Block RAM (BRAM) model for our GPU
# Default size is 4096 16-bit words (8 KB)

class Memory:
    def __init__(self, size_words=4096):
        self.size_words = size_words
        # 16-bit memory array, starts zeroed out
        self.data = [0] * size_words

    def read(self, address):
        if 0 <= address < self.size_words:
            return self.data[address]
        raise IndexError(f"Memory read out of range: {address} (max is {self.size_words - 1})")

    def write(self, address, value):
        if 0 <= address < self.size_words:
            # force 16-bit unsigned
            self.data[address] = value & 0xFFFF
        else:
            raise IndexError(f"Memory write out of range: {address} (max is {self.size_words - 1})")

    def dump(self, start=0, end=16):
        return self.data[start:end]


if __name__ == '__main__':
    mem = Memory(size_words=256)
    mem.write(10, 65535)
    mem.write(11, 42)
    assert mem.read(10) == 65535
    assert mem.read(11) == 42
    print("Memory tests passed!")
