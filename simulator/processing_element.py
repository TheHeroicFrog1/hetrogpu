# 16-bit Processing Element (PE) for SIMT core
# Supports basic integer ALU ops and ReLU activation for neural nets

class ProcessingElement:
    def __init__(self, pe_id, num_registers=8):
        self.pe_id = pe_id
        # R0 through R7 (16-bit words)
        self.registers = [0] * num_registers

    def _to_16bit(self, val):
        # clamp/wrap to 16-bit unsigned range (0 - 65535)
        return val & 0xFFFF

    def _to_signed(self, val):
        # convert unsigned 16-bit int to signed (-32768 to 32767)
        u16 = val & 0xFFFF
        return u16 - 65536 if u16 >= 32768 else u16

    def execute(self, instruction, external_data=None):
        opcode = instruction.get('opcode')

        if opcode == 'NOP':
            return None

        rd = instruction.get('rd')
        rs1 = instruction.get('rs1')
        rs2 = instruction.get('rs2')
        use_imm = instruction.get('imm', False)

        # load value from memory or immediate
        if opcode == 'LOAD':
            val = external_data if external_data is not None else (rs2 if use_imm else 0)
            self.registers[rd] = self._to_16bit(val)
            return None

        # store value out from register
        elif opcode == 'STORE':
            return self.registers[rs1]

        # read register operands
        val1 = self.registers[rs1] if rs1 is not None else 0
        val2 = rs2 if use_imm else (self.registers[rs2] if rs2 is not None else 0)

        s_val1 = self._to_signed(val1)
        s_val2 = self._to_signed(val2)

        # basic ALU instructions
        if opcode == 'ADD':
            self.registers[rd] = self._to_16bit(val1 + val2)
        elif opcode == 'SUB':
            self.registers[rd] = self._to_16bit(val1 - val2)
        elif opcode == 'MUL':
            self.registers[rd] = self._to_16bit(s_val1 * s_val2)
        elif opcode == 'AND':
            self.registers[rd] = self._to_16bit(val1 & val2)
        elif opcode == 'OR':
            self.registers[rd] = self._to_16bit(val1 | val2)
        elif opcode == 'XOR':
            self.registers[rd] = self._to_16bit(val1 ^ val2)

        # AI activation and comparison instructions
        elif opcode == 'RELU':
            # relu(x) = max(0, x)
            self.registers[rd] = self._to_16bit(max(0, s_val1))
        elif opcode == 'CMP_GT':
            self.registers[rd] = 1 if s_val1 > s_val2 else 0
        elif opcode == 'MAX':
            self.registers[rd] = self._to_16bit(max(s_val1, s_val2))
        else:
            raise ValueError(f"PE {self.pe_id}: unknown opcode {opcode}")

        return None

    def __repr__(self):
        return f"PE{self.pe_id}(regs={self.registers})"


if __name__ == '__main__':
    # quick sanity checks
    pe = ProcessingElement(pe_id=0)

    # test relu on negative and positive values
    pe.execute({'opcode': 'LOAD', 'rd': 1, 'rs2': -15, 'imm': True})
    pe.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1})
    assert pe.registers[2] == 0

    pe.execute({'opcode': 'LOAD', 'rd': 1, 'rs2': 42, 'imm': True})
    pe.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1})
    assert pe.registers[2] == 42

    print("PE tests passed!")
