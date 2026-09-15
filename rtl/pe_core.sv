// =============================================================================
// Module: pe_core.sv
// Target: Gowin GW1NR-9 (Tang Nano 9K FPGA)
// Description: 16-Bit Processing Element (PE) Core for HeteroGPU.
// Architecture: Single-lane execution unit with dedicated 8-word General Purpose
//               Register (GPR) File and 16-bit Two's Complement Integer ALU.
// =============================================================================

module pe_core (
    input  logic        clk,
    input  logic        rst_n,          // Active-low asynchronous reset

    // Instruction Interface
    input  logic [3:0]  opcode,         // ALU & Control Operation Code
    input  logic [2:0]  rd,             // Destination Register Index (R0 - R7)
    input  logic [2:0]  rs1,            // Source 1 Register Index (R0 - R7)
    input  logic [2:0]  rs2,            // Source 2 Register Index (R0 - R7)
    input  logic        use_imm,        // 1 = Use immediate operand, 0 = Use R[rs2]
    input  logic [15:0] imm_val,        // 16-bit Immediate Constant
    input  logic [15:0] ext_data_in,    // External Memory Read Bus (from BRAM)

    // Memory Write Interface
    output logic [15:0] data_out        // Data driven to BRAM during STORE
);

    // =========================================================================
    // Opcodes Definition (Mirrors Python Golden Model)
    // =========================================================================
    localparam OP_NOP    = 4'd0;
    localparam OP_LOAD   = 4'd1;
    localparam OP_STORE  = 4'd2;
    localparam OP_ADD    = 4'd3;
    localparam OP_SUB    = 4'd4;
    localparam OP_MUL    = 4'd5;
    localparam OP_AND    = 4'd6;
    localparam OP_OR     = 4'd7;
    localparam OP_XOR    = 4'd8;
    localparam OP_RELU   = 4'd9;
    localparam OP_CMP_GT = 4'd10;
    localparam OP_MAX    = 4'd11;

    // =========================================================================
    // Register File: 8 General-Purpose Registers (16-bit each)
    // Synthesizes to 128 D-type Flip-Flops on the FPGA
    // =========================================================================
    logic [15:0] registers [0:7];

    // Read Operands from Register File
    logic signed [15:0] op1;
    logic signed [15:0] op2;
    assign op1 = registers[rs1];
    assign op2 = use_imm ? imm_val : registers[rs2];

    // Data output port for STORE instructions (drives BRAM data bus)
    assign data_out = registers[rs1];

    // Multiplication intermediate product (32-bit signed DSP output)
    logic signed [31:0] mult_result;
    assign mult_result = op1 * op2;

    // =========================================================================
    // Synchronous Execution: Updates on positive clock edge
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Hardware reset: clear all 8 registers to 0
            for (int i = 0; i < 8; i++) begin
                registers[i] <= 16'h0000;
            end
        end else begin
            case (opcode)
                OP_NOP: begin
                    // Pipeline bubble / No operation
                end

                OP_LOAD: begin
                    // Load into R[rd] from external BRAM or immediate
                    registers[rd] <= use_imm ? imm_val : ext_data_in;
                end

                OP_STORE: begin
                    // Handled combinational on data_out bus
                end

                OP_ADD: begin
                    // 16-bit Integer Addition (natural hardware 16-bit overflow)
                    registers[rd] <= op1 + op2;
                end

                OP_SUB: begin
                    // 16-bit Integer Subtraction
                    registers[rd] <= op1 - op2;
                end

                OP_MUL: begin
                    // 16-bit Signed Multiplication (truncated to lower 16 bits)
                    registers[rd] <= mult_result[15:0];
                end

                OP_AND: begin
                    // Bitwise Logical AND
                    registers[rd] <= op1 & op2;
                end

                OP_OR: begin
                    // Bitwise Logical OR
                    registers[rd] <= op1 | op2;
                end

                OP_XOR: begin
                    // Bitwise Logical XOR
                    registers[rd] <= op1 ^ op2;
                end

                OP_RELU: begin
                    // Rectified Linear Unit: ReLU(x) = max(0, x)
                    // In hardware, if bit 15 (sign bit) is 1, value is negative -> clamp to 0!
                    registers[rd] <= (op1[15] == 1'b1) ? 16'h0000 : op1;
                end

                OP_CMP_GT: begin
                    // Magnitude Comparator: R[rd] = (op1 > op2) ? 1 : 0
                    registers[rd] <= (op1 > op2) ? 16'h0001 : 16'h0000;
                end

                OP_MAX: begin
                    // Maximum Selector: R[rd] = max(op1, op2)
                    registers[rd] <= (op1 > op2) ? op1 : op2;
                end

                default: begin
                    // Safe default: retain register state
                end
            endcase
        end
    end

endmodule
