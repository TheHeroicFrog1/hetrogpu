# simulator/simt_engine.py
from processing_element import ProcessingElement

class SIMTEngine:
    def __init__(self, num_cores=4):
        """
        Initializes the SIMT Engine with a set of Processing Elements.
        num_cores: The number of parallel workers (threads).
        """
        self.num_cores = num_cores
        self.pes = [ProcessingElement(pe_id=i) for i in range(num_cores)]
        self.total_cycles = 0

    def execute(self, instruction, memory):
        """
        Executes a SIMT instruction across all active PEs.
        Returns the number of clock cycles consumed.
        """
        opcode = instruction.get('opcode')
        cycles = 1

        if opcode == 'LOAD_PARALLEL':
            rd = instruction.get('rd')
            base_address = instruction.get('base_address')
            for pe in self.pes:
                addr = base_address + pe.pe_id
                val = memory.read(addr)
                pe.execute({'opcode': 'LOAD', 'rd': rd}, external_data=val)
            cycles = 2  # Memory bus transaction latency

        elif opcode == 'STORE_PARALLEL':
            rs1 = instruction.get('rs1')
            base_address = instruction.get('base_address')
            for pe in self.pes:
                val_to_store = pe.execute({'opcode': 'STORE', 'rs1': rs1})
                addr = base_address + pe.pe_id
                memory.write(addr, val_to_store)
            cycles = 2  # Memory write latency

        else:
            # Broadcast ALU instruction to all PEs simultaneously
            for pe in self.pes:
                pe.execute(instruction)
            cycles = 1  # 1 clock cycle parallel arithmetic

        self.total_cycles += cycles
        return cycles

    def parallel_relu(self, memory, base_addr, length=4):
        """
        Executes parallel activation function ReLU on 'length' memory words.
        Chunks across 4 PEs at a time.
        """
        cycles = 0
        for i in range(0, length, self.num_cores):
            chunk_base = base_addr + i
            # 1. Parallel Load into R1
            c1 = self.execute({'opcode': 'LOAD_PARALLEL', 'rd': 1, 'base_address': chunk_base}, memory)
            # 2. Parallel ReLU: R2 = max(0, R1) across all PEs
            c2 = self.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1}, memory)
            # 3. Parallel Store back to memory
            c3 = self.execute({'opcode': 'STORE_PARALLEL', 'rs1': 2, 'base_address': chunk_base}, memory)
            cycles += (c1 + c2 + c3)
        return cycles

    def dump_state(self):
        """Helper to print the state of all PEs."""
        for pe in self.pes:
            print(pe)


if __name__ == '__main__':
    from memory import Memory
    mem = Memory(size_words=1024)
    simt = SIMTEngine(num_cores=4)

    # Test parallel ReLU on positive and negative activations
    mem.write(100, 15)
    mem.write(101, -25)
    mem.write(102, 50)
    mem.write(103, -100)

    cyc = simt.parallel_relu(mem, base_addr=100, length=4)
    res = [simt.pes[i]._to_signed(mem.read(100 + i)) for i in range(4)]
    print(f"Parallel ReLU Results: {res}, Cycles: {cyc}")
    assert res == [15, 0, 50, 0]
    print("SIMT Engine parallel ReLU activation passed!")
