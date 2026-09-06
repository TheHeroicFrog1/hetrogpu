# simulator/matrix_engine.py

class MatrixEngine:
    def __init__(self, size=2):
        """
        Simulates a Hardware Systolic Array / AI Matrix Engine.
        size: Dimension of the physical MAC grid (2 for a 2x2 systolic unit).
        """
        self.size = size
        self.total_cycles = 0

    def _to_16bit(self, val):
        return val & 0xFFFF

    def _to_signed(self, val):
        u16 = val & 0xFFFF
        return u16 - 65536 if u16 >= 32768 else u16

    def execute_mac_2x2(self, memory, addr_a, addr_b, addr_c):
        """
        Core hardware operation: multiplies two 2x2 matrices stored in memory.
        Takes 4 clock cycles on a 2x2 systolic array.
        """
        # Fetch Matrix A (2x2)
        A = [self._to_signed(memory.read(addr_a + i)) for i in range(4)]
        # Fetch Matrix B (2x2)
        B = [self._to_signed(memory.read(addr_b + i)) for i in range(4)]

        # 4 parallel MAC units
        C = [0] * 4
        C[0] = (A[0] * B[0]) + (A[1] * B[2])
        C[1] = (A[0] * B[1]) + (A[1] * B[3])
        C[2] = (A[2] * B[0]) + (A[3] * B[2])
        C[3] = (A[2] * B[1]) + (A[3] * B[3])

        for i in range(4):
            memory.write(addr_c + i, self._to_16bit(C[i]))

        cycles = 4  # 2x2 systolic array streaming pipeline
        self.total_cycles += cycles
        return [self._to_16bit(x) for x in C], cycles

    def dense_linear_layer(self, memory, in_addr, in_dim, weight_addr, out_dim, out_addr):
        """
        Hardware-accelerated Neural Network Linear Layer: Y = X * W
        Tiles arbitrarily sized vector-matrix multiplications across the 2x2 MAC array.
        """
        X = [self._to_signed(memory.read(in_addr + i)) for i in range(in_dim)]
        cycles = 0
        outputs = []

        for o in range(out_dim):
            dot_product = 0
            # Tile through input dimensions in steps of 2 (hardware MAC pair)
            for k in range(0, in_dim, 2):
                x0 = X[k]
                x1 = X[k + 1] if (k + 1) < in_dim else 0

                w0 = self._to_signed(memory.read(weight_addr + (k * out_dim) + o))
                w1 = self._to_signed(memory.read(weight_addr + ((k + 1) * out_dim) + o)) if (k + 1) < in_dim else 0

                # 2-way MAC unit execution
                dot_product += (x0 * w0) + (x1 * w1)
                cycles += 2  # Systolic throughput: 2 cycles per pair

            # Scaled down to prevent overflow in 16-bit integer quantization
            scaled = dot_product // 32
            out_16 = self._to_16bit(scaled)
            memory.write(out_addr + o, out_16)
            outputs.append(out_16)

        self.total_cycles += cycles
        return outputs, cycles


if __name__ == '__main__':
    from memory import Memory
    mem = Memory(size_words=1024)
    ai_engine = MatrixEngine(size=2)

    # Test 2x2 MAC
    mem.write(10, 2); mem.write(11, -1)
    mem.write(12, 1); mem.write(13, 3)

    mem.write(20, 1); mem.write(21, 2)
    mem.write(22, 3); mem.write(23, 4)

    res, cyc = ai_engine.execute_mac_2x2(mem, addr_a=10, addr_b=20, addr_c=30)
    print(f"2x2 MAC Output: {res}, Cycles: {cyc}")
    print("Matrix Engine enhanced for deep learning inference!")
