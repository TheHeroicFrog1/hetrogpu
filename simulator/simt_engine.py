# ==============================================================================
# 4-Lane SIMT (Single Instruction, Multiple Threads) Execution Engine
# Architecture: Lockstep execution across 4 parallel Processing Elements (PEs).
# Hardware Target: 4 lanes fit comfortably within Gowin FPGA LUT logic (under 3,000 LUTs).
# ==============================================================================

from processing_element import ProcessingElement

class SIMTEngine:
    def __init__(self, num_cores=4):
        # 4 SIMT hardware lanes (PE0, PE1, PE2, PE3)
        self.num_cores = num_cores
        self.pes = [ProcessingElement(pe_id=i) for i in range(num_cores)]
        self.total_cycles = 0  # Global cycle accumulator for hardware performance profiling

    def execute(self, instruction, memory):
        # Instruction Broadcast Unit: Sends one instruction to all 4 PEs simultaneously.
        opcode = instruction.get('opcode')
        cycles = 1

        # ----------------------------------------------------------------------
        # Parallel Vector Load (Contiguous memory coalescing):
        # Memory reads base_address + thread_id for each lane.
        # Takes 2 clock cycles in hardware (1 cycle address setup + 1 cycle BRAM data latch).
        # ----------------------------------------------------------------------
        if opcode == 'LOAD_PARALLEL':
            rd = instruction.get('rd')
            base_address = instruction.get('base_address')
            for pe in self.pes:
                addr = base_address + pe.pe_id
                val = memory.read(addr)
                pe.execute({'opcode': 'LOAD', 'rd': rd}, external_data=val)
            cycles = 2

        # ----------------------------------------------------------------------
        # Parallel Vector Store:
        # All 4 PEs write their internal R[rs1] registers to BRAM in parallel.
        # Takes 2 clock cycles (write enable + BRAM write latch).
        # ----------------------------------------------------------------------
        elif opcode == 'STORE_PARALLEL':
            rs1 = instruction.get('rs1')
            base_address = instruction.get('base_address')
            for pe in self.pes:
                val_to_store = pe.execute({'opcode': 'STORE', 'rs1': rs1})
                addr = base_address + pe.pe_id
                memory.write(addr, val_to_store)
            cycles = 2

        # ----------------------------------------------------------------------
        # Scalar Instruction Broadcast:
        # PEs execute the same arithmetic instruction in parallel lockstep (1 cycle).
        # ----------------------------------------------------------------------
        else:
            for pe in self.pes:
                pe.execute(instruction)
            cycles = 1

        self.total_cycles += cycles
        return cycles

    def parallel_relu(self, memory, base_addr, length=4):
        # Hardware Activation Routine:
        # Evaluates 4 activations in parallel using SIMT lanes.
        # Timing: 2 cycles (LOAD_PARALLEL) + 1 cycle (RELU ALU) + 2 cycles (STORE_PARALLEL) = 5 cycles total!
        cycles = 0
        for i in range(0, length, self.num_cores):
            chunk_base = base_addr + i
            c1 = self.execute({'opcode': 'LOAD_PARALLEL', 'rd': 1, 'base_address': chunk_base}, memory)
            c2 = self.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1}, memory)
            c3 = self.execute({'opcode': 'STORE_PARALLEL', 'rs1': 2, 'base_address': chunk_base}, memory)
            cycles += (c1 + c2 + c3)
        return cycles

    def execute_gemm_4x4(self, memory, addr_a, addr_b, addr_c):
        # Full 4x4 General Matrix Multiply (GEMM) simulated directly on SIMT cores.
        # Formula: C[r, c] = Sum_k (A[r, k] * B[k, c])
        # Demonstrates why traditional GPUs are slow on AI: sequential broadcast bottleneck!
        # Total Hardware Cycles: 4 rows * (1 clear + 4 iterations * (1 + 2 + 1 + 1) + 2 store) = 92 cycles.
        cycles = 0
        for r in range(4):
            # Step 1: Clear accumulator register R3 to 0 (1 cycle)
            cycles += self.execute({'opcode': 'LOAD', 'rd': 3, 'rs2': 0, 'imm': True}, memory)
            
            # Step 2: Loop across inner dimension k (4 iterations)
            for k in range(4):
                a_val = memory.read(addr_a + (r * 4) + k)
                # Broadcast scalar element A[r, k] into register R1 across all 4 PEs (1 cycle)
                cycles += self.execute({'opcode': 'LOAD', 'rd': 1, 'rs2': a_val, 'imm': True}, memory)
                # Coalesced parallel load of row k from matrix B into register R2 (2 cycles)
                cycles += self.execute({'opcode': 'LOAD_PARALLEL', 'rd': 2, 'base_address': addr_b + (k * 4)}, memory)
                # Parallel Multiply: R4 = R1 * R2 across all 4 PEs in DSP blocks (1 cycle)
                cycles += self.execute({'opcode': 'MUL', 'rd': 4, 'rs1': 1, 'rs2': 2}, memory)
                # Parallel Accumulate: R3 += R4 (1 cycle)
                cycles += self.execute({'opcode': 'ADD', 'rd': 3, 'rs1': 3, 'rs2': 4}, memory)
                
            # Step 3: Write out row r of matrix C from R3 back to BRAM (2 cycles)
            cycles += self.execute({'opcode': 'STORE_PARALLEL', 'rs1': 3, 'base_address': addr_c + (r * 4)}, memory)
        return cycles

    def execute_copy(self, memory, src_addr, dest_addr, length):
        # Software-driven Block Memory Copy (CPU/GPU core polling method).
        # Each 4-word chunk takes 2 (load) + 2 (store) + 1 (loop branch & pointer increment) = 5 cycles.
        # For 64 words: (64 / 4) * 5 = 80 cycles.
        cycles = 0
        for chunk in range(0, length, self.num_cores):
            cycles += self.execute({'opcode': 'LOAD_PARALLEL', 'rd': 1, 'base_address': src_addr + chunk}, memory)
            cycles += self.execute({'opcode': 'STORE_PARALLEL', 'rs1': 1, 'base_address': dest_addr + chunk}, memory)
            cycles += 1  # Branch instruction and address pointer increment latency
        return cycles

    def dump_state(self):
        # Prints current register files for all 4 PEs
        for pe in self.pes:
            print(pe)


if __name__ == '__main__':
    from memory import Memory
    mem = Memory(size_words=512)
    simt = SIMTEngine(num_cores=4)

    # Initialize test vector with positive and negative numbers
    test_vals = [15, -25, 50, -100]
    for i, v in enumerate(test_vals):
        mem.write(100 + i, v)

    # Execute parallel ReLU activation across the 4 PEs
    cyc = simt.parallel_relu(mem, base_addr=100, length=4)
    res = [simt.pes[i]._to_signed(mem.read(100 + i)) for i in range(4)]
    assert res == [15, 0, 50, 0]
    print(f"SIMT tests passed in {cyc} cycles!")
