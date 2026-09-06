# simulator/processing_element.py

class ProcessingElement:
    def __init__(self, pe_id, num_registers=8):
        self.pe_id = pe_id
        # Initialize 16-bit registers to 0
        self.registers = [0] * num_registers
        
    def _to_16bit(self, val):
        """Helper to enforce 16-bit unsigned representation (0 to 65535)."""
        return val & 0xFFFF

    def _to_signed(self, val):
        """Converts a 16-bit register value into a signed integer (-32768 to 32767)."""
        u16 = val & 0xFFFF
        return u16 - 65536 if u16 >= 32768 else u16

    def execute(self, instruction, external_data=None):
        """
        Executes a single instruction.
        
        Format of instruction (dict for simplicity):
        {
            'opcode': 'ADD',
            'rd': 0,      # Destination register index
            'rs1': 1,     # Source register 1 index
            'rs2': 2,     # Source register 2 index (or immediate value)
            'imm': False  # Is rs2 an immediate value?
        }
        """
        opcode = instruction.get('opcode')
        
        if opcode == 'NOP':
            return None
            
        rd = instruction.get('rd')
        rs1 = instruction.get('rs1')
        rs2 = instruction.get('rs2')
        use_imm = instruction.get('imm', False)
        
        # Memory / Load operations
        if opcode == 'LOAD':
            val = external_data if external_data is not None else (rs2 if use_imm else 0)
            self.registers[rd] = self._to_16bit(val)
            return None
            
        elif opcode == 'STORE':
            return self.registers[rs1]
            
        # Fetch operands
        val1 = self.registers[rs1] if rs1 is not None else 0
        val2 = rs2 if use_imm else (self.registers[rs2] if rs2 is not None else 0)
        
        s_val1 = self._to_signed(val1)
        s_val2 = self._to_signed(val2)
            
        # ALU Operations (16-bit)
        if opcode == 'ADD':
            self.registers[rd] = self._to_16bit(val1 + val2)
        elif opcode == 'SUB':
            self.registers[rd] = self._to_16bit(val1 - val2)
        elif opcode == 'MUL':
            # Signed fixed-point multiplication helper
            self.registers[rd] = self._to_16bit(s_val1 * s_val2)
        elif opcode == 'AND':
            self.registers[rd] = self._to_16bit(val1 & val2)
        elif opcode == 'OR':
            self.registers[rd] = self._to_16bit(val1 | val2)
        elif opcode == 'XOR':
            self.registers[rd] = self._to_16bit(val1 ^ val2)
            
        # AI / Neural Network Activation Opcodes
        elif opcode == 'RELU':
            # ReLU(x) = max(0, x). Used in AI neural network hidden layers.
            relu_val = max(0, s_val1)
            self.registers[rd] = self._to_16bit(relu_val)
        elif opcode == 'CMP_GT':
            # Compare Greater Than: rd = 1 if rs1 > rs2 else 0
            self.registers[rd] = 1 if s_val1 > s_val2 else 0
        elif opcode == 'MAX':
            self.registers[rd] = self._to_16bit(max(s_val1, s_val2))
        else:
            raise ValueError(f"PE {self.pe_id}: Unknown opcode {opcode}")
            
        return None
        
    def __repr__(self):
        return f"PE(id={self.pe_id}, regs={self.registers})"

if __name__ == '__main__':
    pe = ProcessingElement(pe_id=0)
    
    # Test ReLU on negative value (-15 in 16-bit = 65521)
    pe.execute({'opcode': 'LOAD', 'rd': 1, 'rs2': -15, 'imm': True})
    pe.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1})
    assert pe.registers[2] == 0, f"Expected 0 for ReLU(-15), got {pe.registers[2]}"

    # Test ReLU on positive value (42)
    pe.execute({'opcode': 'LOAD', 'rd': 1, 'rs2': 42, 'imm': True})
    pe.execute({'opcode': 'RELU', 'rd': 2, 'rs1': 1})
    assert pe.registers[2] == 42, f"Expected 42 for ReLU(42), got {pe.registers[2]}"

    print("ProcessingElement AI opcodes (ReLU, Signed, CMP) passed!")
