# ==============================================================================
# 2x2 Systolic Array AI Matrix Engine (Tensor Processing Core)
# Architecture: 2D mesh of 4 Multiply-Accumulate (MAC) processing elements.
# Dataflow: Kung & Leiserson (1979) systolic flow (inputs stream right, weights stream down).
# Hardware Target: Uses 4 hardware DSP blocks (Gowin GW1NR-9 has 20 DSPs, using only 20%).
# ==============================================================================

class MatrixEngine:
    def __init__(self, size=2):
        # 2x2 grid dimension (4 total physical MAC multiplier cells)
        self.size = size
        self.total_cycles = 0  # Global cycle accumulator for hardware performance profiling

    def _to_16bit(self, val):
        # Simulates 16-bit register truncation (& 0xFFFF)
        return val & 0xFFFF

    def _to_signed(self, val):
        # Converts 16-bit unsigned hardware value to signed integer
        u16 = val & 0xFFFF
        return u16 - 65536 if u16 >= 32768 else u16

    def execute_mac_2x2(self, memory, addr_a, addr_b, addr_c):
        # ----------------------------------------------------------------------
        # 2x2 Matrix Multiplication Kernel: C = A * B
        # In hardware, data flows rhythmically through the 2x2 mesh.
        # Latency: Exactly 4 clock cycles to stream inputs, multiply, and latch outputs.
        # ----------------------------------------------------------------------
        
        # Read 2x2 input matrices A and B from BRAM addresses
        A = [self._to_signed(memory.read(addr_a + i)) for i in range(4)]
        B = [self._to_signed(memory.read(addr_b + i)) for i in range(4)]

        # 4 parallel MAC units evaluate dot products simultaneously:
        # C[0,0] = A[0,0]*B[0,0] + A[0,1]*B[1,0]
        # C[0,1] = A[0,0]*B[0,1] + A[0,1]*B[1,1]
        # C[1,0] = A[1,0]*B[0,0] + A[1,1]*B[1,0]
        # C[1,1] = A[1,0]*B[0,1] + A[1,1]*B[1,1]
        C = [0] * 4
        C[0] = (A[0] * B[0]) + (A[1] * B[2])
        C[1] = (A[0] * B[1]) + (A[1] * B[3])
        C[2] = (A[2] * B[0]) + (A[3] * B[2])
        C[3] = (A[2] * B[1]) + (A[3] * B[3])

        # Write resulting 2x2 sub-matrix back to BRAM destination address
        for i in range(4):
            memory.write(addr_c + i, self._to_16bit(C[i]))

        cycles = 4  # Pure systolic pipeline flow takes 4 clock cycles
        self.total_cycles += cycles
        return [self._to_16bit(x) for x in C], cycles

    def dense_linear_layer(self, memory, in_addr, in_dim, weight_addr, out_dim, out_addr):
        # ----------------------------------------------------------------------
        # Fully Connected Neural Network Layer: Y = X * W
        # Tiled execution: Breaks arbitrary vector-matrix multiply into 2-way MAC steps.
        # ----------------------------------------------------------------------
        X = [self._to_signed(memory.read(in_addr + i)) for i in range(in_dim)]
        cycles = 0
        outputs = []

        # Iterate across each output neuron
        for o in range(out_dim):
            dot_product = 0
            
            # Pair inputs in chunks of 2 for dual-MAC hardware processing
            for k in range(0, in_dim, 2):
                x0 = X[k]
                x1 = X[k + 1] if (k + 1) < in_dim else 0

                w0 = self._to_signed(memory.read(weight_addr + (k * out_dim) + o))
                w1 = self._to_signed(memory.read(weight_addr + ((k + 1) * out_dim) + o)) if (k + 1) < in_dim else 0

                # Multiply-Accumulate step (2 cycles per paired dot product)
                dot_product += (x0 * w0) + (x1 * w1)
                cycles += 2

            # Fixed-Point Scaling:
            # We divide by 32 (arithmetic right-shift by 5 bits in Verilog: '>>> 5').
            # Prevents accumulated sum from overflowing the 16-bit integer boundary.
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

    # Test 2x2 Identity Matrix multiply: I * M = M
    mem.write(0, 1); mem.write(1, 0)
    mem.write(2, 0); mem.write(3, 1)

    mem.write(10, 5); mem.write(11, 10)
    mem.write(12, 15); mem.write(13, 20)

    res, cyc = engine.execute_mac_2x2(mem, addr_a=0, addr_b=10, addr_c=20)
    assert res == [5, 10, 15, 20]
    print(f"Matrix Engine 2x2 MAC test passed in {cyc} cycles!")
