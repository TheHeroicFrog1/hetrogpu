# ==============================================================================
# 16-Bit Processing Element (PE) Core
# Architecture: Single-lane execution unit with dedicated General Purpose Registers (GPRs).
# Hardware Target: Gowin GW1NR-9 (Tang Nano 9K FPGA).
# ==============================================================================

class ProcessingElement:
    def __init__(self, pe_id, num_registers=8):
        self.pe_id = pe_id
        # Register File: R0 to R7 (8 general-purpose registers, each 16-bit wide)
        self.registers = [0] * num_registers

    def _to_16bit(self, val):
        # Hardware Word Masking:
        # FPGAs have fixed 16-bit wire buses. In Python, numbers can grow infinitely,
        # so doing '& 0xFFFF' simulates natural hardware overflow and register truncation.
        return val & 0xFFFF

    def _to_signed(self, val):
        # Two's Complement Conversion:
        # Converts 16-bit unsigned hardware value (0 to 65535) into signed int (-32768 to 32767).
        # Essential for negative coordinates, velocity, and neural network weights.
        u16 = val & 0xFFFF
        return u16 - 65536 if u16 >= 32768 else u16

    def execute(self, instruction, external_data=None):
        # Instruction Decoder & ALU Execution Unit
        opcode = instruction.get('opcode')

        # NOP: No Operation (pipeline bubble / idle clock cycle)
        if opcode == 'NOP':
            return None

        # Instruction register field decoding: Destination (rd), Sources (rs1, rs2)
        rd = instruction.get('rd')
        rs1 = instruction.get('rs1')
        rs2 = instruction.get('rs2')
        use_imm = instruction.get('imm', False)  # Immediate operand flag (constant from instruction)

        # Memory Load Operation:
        # Writes external BRAM data or immediate constant into target register R[rd]
        if opcode == 'LOAD':
            val = external_data if external_data is not None else (rs2 if use_imm else 0)
            self.registers[rd] = self._to_16bit(val)
            return None

        # Memory Store Operation:
        # Reads R[rs1] to drive the data bus out to BRAM
        elif opcode == 'STORE':
            return self.registers[rs1]

        # Fetch register operand values from Register File
        val1 = self.registers[rs1] if rs1 is not None else 0
        val2 = rs2 if use_imm else (self.registers[rs2] if rs2 is not None else 0)

        # Decode as signed integers for arithmetic operations
        s_val1 = self._to_signed(val1)
        s_val2 = self._to_signed(val2)

        # ----------------------------------------------------------------------
        # Arithmetic Logic Unit (ALU) Operations:
        # ----------------------------------------------------------------------
        if opcode == 'ADD':
            # 16-bit integer addition
            self.registers[rd] = self._to_16bit(val1 + val2)
        elif opcode == 'SUB':
            # 16-bit subtraction with two's complement borrow
            self.registers[rd] = self._to_16bit(val1 - val2)
        elif opcode == 'MUL':
            # 16-bit signed multiplication (maps directly to FPGA DSP block)
            self.registers[rd] = self._to_16bit(s_val1 * s_val2)
        elif opcode == 'AND':
            # Bitwise logical AND (bitmasking)
            self.registers[rd] = self._to_16bit(val1 & val2)
        elif opcode == 'OR':
            # Bitwise logical OR
            self.registers[rd] = self._to_16bit(val1 | val2)
        elif opcode == 'XOR':
            # Bitwise logical XOR (inversion / parity)
            self.registers[rd] = self._to_16bit(val1 ^ val2)

        # ----------------------------------------------------------------------
        # Specialized AI Activation & Hardware Comparison Instructions:
        # ----------------------------------------------------------------------
        elif opcode == 'RELU':
            # Rectified Linear Unit: ReLU(x) = max(0, x)
            # In hardware, this is a simple 1-cycle sign-bit multiplexer (if bit 15 == 1 then 0 else x)
            self.registers[rd] = self._to_16bit(max(0, s_val1))
        elif opcode == 'CMP_GT':
            # Magnitude Comparator: outputs 1 if rs1 > rs2, else 0 (used for argmax decision)
            self.registers[rd] = 1 if s_val1 > s_val2 else 0
        elif opcode == 'MAX':
            # Hardware Maximum selector
            self.registers[rd] = self._to_16bit(max(s_val1, s_val2))
        else:
            raise ValueError(f"PE {self.pe_id}: unknown opcode {opcode}")

        return None

    def __repr__(self):
        return f"PE{self.pe_id}(regs={self.registers})"


if __name__ == '__main__':
    # Self-test bench for single PE
    pe = ProcessingElement(pe_id=0)

    # Test ReLU hardware activation on negative value (-15 -> 0)
    pe.execute({'opcode': 'LOAD', 'rd': 1, 'rs2': -15, 'imm': True})
    pe.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1})
    assert pe.registers[2] == 0

    # Test ReLU on positive value (42 -> 42)
    pe.execute({'opcode': 'LOAD', 'rd': 1, 'rs2': 42, 'imm': True})
    pe.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1})
    assert pe.registers[2] == 42

    print("PE tests passed!")
