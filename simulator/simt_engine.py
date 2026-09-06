# 4-core SIMT execution engine
# Broadcasts one instruction to all 4 PEs at the same time

from processing_element import ProcessingElement

class SIMTEngine:
    def __init__(self, num_cores=4):
        self.num_cores = num_cores
        # instantiate our 4 processing elements
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
            cycles = 2  # 2 cycles for memory read bus transaction

        # all PEs store to contiguous memory: base_addr + pe_id
        elif opcode == 'STORE_PARALLEL':
            rs1 = instruction.get('rs1')
            base_address = instruction.get('base_address')
            for pe in self.pes:
                val_to_store = pe.execute({'opcode': 'STORE', 'rs1': rs1})
                addr = base_address + pe.pe_id
                memory.write(addr, val_to_store)
            cycles = 2  # 2 cycles for memory write

        # normal ALU broadcast instruction
        else:
            for pe in self.pes:
                pe.execute(instruction)
            cycles = 1  # 1 cycle parallel ALU op

        self.total_cycles += cycles
        return cycles

    def parallel_relu(self, memory, base_addr, length=4):
        # runs relu on a vector using all 4 PEs in parallel
        cycles = 0
        for i in range(0, length, self.num_cores):
            chunk_base = base_addr + i
            # load vector into R1 across PEs
            c1 = self.execute({'opcode': 'LOAD_PARALLEL', 'rd': 1, 'base_address': chunk_base}, memory)
            # R2 = max(0, R1) in parallel
            c2 = self.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1}, memory)
            # write back to memory
            c3 = self.execute({'opcode': 'STORE_PARALLEL', 'rs1': 2, 'base_address': chunk_base}, memory)
            cycles += (c1 + c2 + c3)
        return cycles

    def dump_state(self):
        for pe in self.pes:
            print(pe)


if __name__ == '__main__':
    from memory import Memory
    mem = Memory(size_words=512)
    simt = SIMTEngine(num_cores=4)

    # test parallel relu: should zero out negative numbers
    test_vals = [15, -25, 50, -100]
    for i, v in enumerate(test_vals):
        mem.write(100 + i, v)

    cyc = simt.parallel_relu(mem, base_addr=100, length=4)
    res = [simt.pes[i]._to_signed(mem.read(100 + i)) for i in range(4)]
    assert res == [15, 0, 50, 0]
    print(f"SIMT parallel ReLU passed in {cyc} cycles!")
