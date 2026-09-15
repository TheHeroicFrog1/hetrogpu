// =============================================================================
// Module: simt_engine.sv
// Target: Gowin GW1NR-9 (Tang Nano 9K FPGA)
// Description: 4-Lane SIMT (Single Instruction, Multiple Threads) Execution Engine.
// Architecture: Lockstep instruction broadcast across 4 parallel Processing Elements.
//               Supports parallel vector loads and stores with contiguous address mapping.
// =============================================================================

module simt_engine (
    input  logic        clk,
    input  logic        rst_n,

    // Instruction Broadcast Bus
    input  logic        inst_valid,
    input  logic [3:0]  opcode,
    input  logic [2:0]  rd,
    input  logic [2:0]  rs1,
    input  logic [2:0]  rs2,
    input  logic        use_imm,
    input  logic [15:0] imm_val,
    input  logic [11:0] base_address,   // Memory address offset for parallel vector ops
    input  logic        is_parallel_mem,// 1 = Vector memory op (base + thread_id)

    // Memory Read Interface (From BRAM)
    input  logic [15:0] mem_data_in [0:3],

    // Memory Write Interface (To BRAM)
    output logic        mem_we,
    output logic [11:0] mem_addr [0:3],
    output logic [15:0] mem_data_out [0:3],

    // Status & Telemetry
    output logic        busy,
    output logic [31:0] simt_cycles
);

    localparam OP_LOAD  = 4'd1;
    localparam OP_STORE = 4'd2;

    // Direct connections to the 4 Processing Element instances
    logic [15:0] pe_ext_data [0:3];
    logic [15:0] pe_data_out [0:3];

    // =========================================================================
    // 4 Parallel Processing Elements (PE0 - PE3)
    // =========================================================================
    genvar i;
    generate
        for (i = 0; i < 4; i++) begin : gen_pes
            // Memory Address Assignment: base_address + lane_id
            assign mem_addr[i] = base_address + i[11:0];

            // Memory Read Routing: Each PE gets contiguous word from BRAM
            assign pe_ext_data[i] = mem_data_in[i];

            // Memory Write Routing: Write data driven directly from PE register output
            assign mem_data_out[i] = pe_data_out[i];

            pe_core u_pe (
                .clk         (clk),
                .rst_n       (rst_n),
                .opcode      (inst_valid ? opcode : 4'd0),
                .rd          (rd),
                .rs1         (rs1),
                .rs2         (rs2),
                .use_imm     (use_imm),
                .imm_val     (imm_val),
                .ext_data_in (pe_ext_data[i]),
                .data_out    (pe_data_out[i])
            );
        end
    endgenerate

    // Memory Write Enable is asserted during STORE or STORE_PARALLEL
    assign mem_we = inst_valid && (opcode == OP_STORE);

    // =========================================================================
    // Execution Timing & Cycle Telemetry Counter
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            simt_cycles <= 32'd0;
            busy        <= 1'b0;
        end else if (inst_valid) begin
            // Parallel memory operations take 2 clock cycles, scalar ALU takes 1 cycle
            if (is_parallel_mem) begin
                simt_cycles <= simt_cycles + 32'd2;
            end else begin
                simt_cycles <= simt_cycles + 32'd1;
            end
        end
    end

endmodule
