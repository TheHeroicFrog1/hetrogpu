# 2x2 Systolic Array / Matrix Engine for accelerating AI GEMM operations
# Sized as 2x2 so it easily fits within the DSP budget of a Tang Nano 9K FPGA

class MatrixEngine:
    def __init__(self, size=2):
        self.size = size
        self.total_cycles = 0

    def _to_16bit(self, val):
        return val & 0xFFFF

    def _to_signed(self, val):
        u16 = val & 0xFFFF
        return u16 - 65536 if u16 >= 32768 else u16

    def execute_mac_2x2(self, memory, addr_a, addr_b, addr_c):
        # 2x2 matrix multiplication: C = A * B
        # in hardware systolic array this takes 4 cycles to stream through
        A = [self._to_signed(memory.read(addr_a + i)) for i in range(4)]
        B = [self._to_signed(memory.read(addr_b + i)) for i in range(4)]

        C = [0] * 4
        C[0] = (A[0] * B[0]) + (A[1] * B[2])
        C[1] = (A[0] * B[1]) + (A[1] * B[3])
        C[2] = (A[2] * B[0]) + (A[3] * B[2])
        C[3] = (A[2] * B[1]) + (A[3] * B[3])

        for i in range(4):
            memory.write(addr_c + i, self._to_16bit(C[i]))

        cycles = 4
        self.total_cycles += cycles
        return [self._to_16bit(x) for x in C], cycles

    def dense_linear_layer(self, memory, in_addr, in_dim, weight_addr, out_dim, out_addr):
        # general vector-matrix multiply (Y = X * W) tiled using our 2x2 MAC array
        X = [self._to_signed(memory.read(in_addr + i)) for i in range(in_dim)]
        cycles = 0
        outputs = []

        for o in range(out_dim):
            dot_product = 0
            # pair inputs together for 2-way MAC
            for k in range(0, in_dim, 2):
                x0 = X[k]
                x1 = X[k + 1] if (k + 1) < in_dim else 0

                w0 = self._to_signed(memory.read(weight_addr + (k * out_dim) + o))
                w1 = self._to_signed(memory.read(weight_addr + ((k + 1) * out_dim) + o)) if (k + 1) < in_dim else 0

                dot_product += (x0 * w0) + (x1 * w1)
                cycles += 2

            # fixed-point scale factor (divide by 32) so outputs don't saturate 16-bit
            scaled = dot_product // 32
            out_16 = self._to_16bit(scaled)
            memory.write(out_addr + o, out_16)
            outputs.append(out_16)

        self.total_cycles += cycles
        return outputs, cycles


if __name__ == '__main__':
    from memory import Memory
    mem = Memory(size_words=256)
    engine = MatrixEngine(size=2)

    # test 2x2 identity multiplication
    mem.write(0, 1); mem.write(1, 0)
    mem.write(2, 0); mem.write(3, 1)

    mem.write(10, 5); mem.write(11, 10)
    mem.write(12, 15); mem.write(13, 20)

    res, cyc = engine.execute_mac_2x2(mem, addr_a=0, addr_b=10, addr_c=20)
    assert res == [5, 10, 15, 20]
    print(f"Matrix Engine 2x2 MAC test passed in {cyc} cycles!")
