# 4-core SIMT execution engine
# Broadcasts instructions to 4 parallel processing elements

from processing_element import ProcessingElement

class SIMTEngine:
    def __init__(self, num_cores=4):
        self.num_cores = num_cores
        self.pes = [ProcessingElement(pe_id=i) for i in range(num_cores)]
        self.total_cycles = 0

    def execute(self, instruction, memory):
        opcode = instruction.get('opcode')
        cycles = 1

        # all PEs load from contiguous memory: base_addr + pe_id
        if opcode == 'LOAD_PARALLEL':
            rd = instruction.get('rd')
            base_address = instruction.get('base_address')
            for pe in self.pes:
                addr = base_address + pe.pe_id
                val = memory.read(addr)
                pe.execute({'opcode': 'LOAD', 'rd': rd}, external_data=val)
            cycles = 2

        # all PEs store to contiguous memory: base_addr + pe_id
        elif opcode == 'STORE_PARALLEL':
            rs1 = instruction.get('rs1')
            base_address = instruction.get('base_address')
            for pe in self.pes:
                val_to_store = pe.execute({'opcode': 'STORE', 'rs1': rs1})
                addr = base_address + pe.pe_id
                memory.write(addr, val_to_store)
            cycles = 2

        # broadcast ALU instruction to all PEs
        else:
            for pe in self.pes:
                pe.execute(instruction)
            cycles = 1

        self.total_cycles += cycles
        return cycles

    def parallel_relu(self, memory, base_addr, length=4):
        cycles = 0
        for i in range(0, length, self.num_cores):
            chunk_base = base_addr + i
            c1 = self.execute({'opcode': 'LOAD_PARALLEL', 'rd': 1, 'base_address': chunk_base}, memory)
            c2 = self.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1}, memory)
            c3 = self.execute({'opcode': 'STORE_PARALLEL', 'rs1': 2, 'base_address': chunk_base}, memory)
            cycles += (c1 + c2 + c3)
        return cycles

    def execute_gemm_4x4(self, memory, addr_a, addr_b, addr_c):
        # runs general 4x4 matrix multiply strictly through the 4 SIMT PEs
        cycles = 0
        for r in range(4):
            # clear accumulator R3
            cycles += self.execute({'opcode': 'LOAD', 'rd': 3, 'rs2': 0, 'imm': True}, memory)
            for k in range(4):
                a_val = memory.read(addr_a + (r * 4) + k)
                # broadcast scalar A[r, k] into R1
                cycles += self.execute({'opcode': 'LOAD', 'rd': 1, 'rs2': a_val, 'imm': True}, memory)
                # parallel load row k of B across PEs into R2
                cycles += self.execute({'opcode': 'LOAD_PARALLEL', 'rd': 2, 'base_address': addr_b + (k * 4)}, memory)
                # multiply and accumulate: R3 += R1 * R2
                cycles += self.execute({'opcode': 'MUL', 'rd': 4, 'rs1': 1, 'rs2': 2}, memory)
                cycles += self.execute({'opcode': 'ADD', 'rd': 3, 'rs1': 3, 'rs2': 4}, memory)
            # parallel store row r of C to memory
            cycles += self.execute({'opcode': 'STORE_PARALLEL', 'rs1': 3, 'base_address': addr_c + (r * 4)}, memory)
        return cycles

    def execute_copy(self, memory, src_addr, dest_addr, length):
        # block memory copy using parallel load/store across PEs
        cycles = 0
        for chunk in range(0, length, self.num_cores):
            cycles += self.execute({'opcode': 'LOAD_PARALLEL', 'rd': 1, 'base_address': src_addr + chunk}, memory)
            cycles += self.execute({'opcode': 'STORE_PARALLEL', 'rs1': 1, 'base_address': dest_addr + chunk}, memory)
            cycles += 1  # pointer increment and loop branch latency
        return cycles

    def dump_state(self):
        for pe in self.pes:
            print(pe)


if __name__ == '__main__':
    from memory import Memory
    mem = Memory(size_words=512)
    simt = SIMTEngine(num_cores=4)

    test_vals = [15, -25, 50, -100]
    for i, v in enumerate(test_vals):
        mem.write(100 + i, v)

    cyc = simt.parallel_relu(mem, base_addr=100, length=4)
    res = [simt.pes[i]._to_signed(mem.read(100 + i)) for i in range(4)]
    assert res == [15, 0, 50, 0]
    print(f"SIMT tests passed in {cyc} cycles!")
