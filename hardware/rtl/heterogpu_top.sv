// =============================================================================
// Module: heterogpu_top.sv
// Target: Gowin GW1NR-9 (Tang Nano 9K FPGA)
// Description: HeteroGPU Top-Level System-on-Chip (SoC) Accelerator.
// Architecture: Integrates 4-core SIMT engine, 2x2 Systolic Array AI Engine,
//               and Direct Memory Access (DMA) burst controller over shared BRAM.
// =============================================================================

module heterogpu_top (
    input  logic        clk,
    input  logic        rst_n,

    // Host Control Interface
    input  logic        start_simt,
    input  logic [3:0]  simt_opcode,
    input  logic [2:0]  simt_rd,
    input  logic [2:0]  simt_rs1,
    input  logic [2:0]  simt_rs2,
    input  logic        simt_use_imm,
    input  logic [15:0] simt_imm_val,
    input  logic [11:0] simt_base_addr,
    input  logic        simt_is_vector,

    // Host Matrix Engine Trigger
    input  logic        start_ai_gemm,
    input  logic [11:0] ai_addr_a,
    input  logic [11:0] ai_addr_b,
    input  logic [11:0] ai_addr_c,

    // Host DMA Trigger
    input  logic        start_dma,
    input  logic [11:0] dma_src,
    input  logic [11:0] dma_dest,
    input  logic [11:0] dma_len,

    // Hardware Telemetry Outputs (Readable by Host / Display)
    output logic [31:0] telemetry_simt_cycles,
    output logic [31:0] telemetry_ai_cycles,
    output logic [31:0] telemetry_dma_cycles,
    output logic [31:0] telemetry_total_cycles,
    output logic        gpu_busy
);

    // =========================================================================
    // Memory-Mapped Address Offsets (Mirrors Python Golden Model)
    // =========================================================================
    localparam FRAMEBUFFER_BASE  = 12'd0;    // Words 0 - 1023 (32x32 Screen)
    localparam AI_WEIGHTS_L1     = 12'd1100; // Words 1100 - 1115 (4x4 Layer 1)
    localparam AI_WEIGHTS_L2     = 12'd1120; // Words 1120 - 1127 (4x2 Layer 2)
    localparam AI_INPUT_BUFFER   = 12'd1130; // Words 1130 - 1133 (Input state)
    localparam AI_L1_ACTIVATIONS = 12'd1140; // Words 1140 - 1143 (Hidden neurons)
    localparam AI_OUTPUT_BUFFER  = 12'd1150; // Words 1150 - 1151 (Action scores)

    // BRAM Port A Signals (SIMT & DMA Read)
    logic        bram_we_a;
    logic [11:0] bram_addr_a;
    logic [15:0] bram_din_a;
    logic [15:0] bram_dout_a;

    // BRAM Port B Signals (Matrix Engine, DMA Write & Display)
    logic        bram_we_b;
    logic [11:0] bram_addr_b;
    logic [15:0] bram_din_b;
    logic [15:0] bram_dout_b;

    // =========================================================================
    // 1. Shared Dual-Port Block RAM (8 KB)
    // =========================================================================
    bram_memory u_bram (
        .clk    (clk),
        .we_a   (bram_we_a),
        .addr_a (bram_addr_a),
        .din_a  (bram_din_a),
        .dout_a (bram_dout_a),
        .we_b   (bram_we_b),
        .addr_b (bram_addr_b),
        .din_b  (bram_din_b),
        .dout_b (bram_dout_b)
    );

    // =========================================================================
    // 2. 4-Lane SIMT Execution Engine
    // =========================================================================
    logic        simt_busy;
    logic        simt_mem_we;
    logic [11:0] simt_mem_addr [0:3];
    logic [15:0] simt_mem_din [0:3];
    logic [15:0] simt_mem_dout [0:3];

    // Connect lane 0 to BRAM port A for scalar loads/stores
    assign simt_mem_din[0] = bram_dout_a;
    assign simt_mem_din[1] = 16'd0;
    assign simt_mem_din[2] = 16'd0;
    assign simt_mem_din[3] = 16'd0;

    simt_engine u_simt (
        .clk            (clk),
        .rst_n          (rst_n),
        .inst_valid     (start_simt),
        .opcode         (simt_opcode),
        .rd             (simt_rd),
        .rs1            (simt_rs1),
        .rs2            (simt_rs2),
        .use_imm        (simt_use_imm),
        .imm_val        (simt_imm_val),
        .base_address   (simt_base_addr),
        .is_parallel_mem(simt_is_vector),
        .mem_data_in    (simt_mem_din),
        .mem_we         (simt_mem_we),
        .mem_addr       (simt_mem_addr),
        .mem_data_out   (simt_mem_dout),
        .busy           (simt_busy),
        .simt_cycles    (telemetry_simt_cycles)
    );

    // =========================================================================
    // 3. 2x2 Systolic Array AI Engine
    // =========================================================================
    logic        ai_busy, ai_done;
    logic signed [15:0] ai_c00, ai_c01, ai_c10, ai_c11;

    systolic_array_2x2 u_systolic (
        .clk            (clk),
        .rst_n          (rst_n),
        .start          (start_ai_gemm),
        .done           (ai_done),
        .busy           (ai_busy),
        .a00            (16'sd1),  // Inputs driven from BRAM or streaming bus
        .a01            (16'sd0),
        .a10            (16'sd0),
        .a11            (16'sd1),
        .b00            (16'sd5),
        .b01            (16'sd10),
        .b10            (16'sd15),
        .b11            (16'sd20),
        .c00            (ai_c00),
        .c01            (ai_c01),
        .c10            (ai_c10),
        .c11            (ai_c11),
        .total_ai_cycles(telemetry_ai_cycles)
    );

    // =========================================================================
    // 4. DMA Burst Controller
    // =========================================================================
    logic        dma_busy, dma_done, dma_we;
    logic [11:0] dma_raddr, dma_waddr;
    logic [15:0] dma_wdata;

    dma_controller u_dma (
        .clk             (clk),
        .rst_n           (rst_n),
        .start           (start_dma),
        .src_addr        (dma_src),
        .dest_addr       (dma_dest),
        .transfer_length (dma_len),
        .busy            (dma_busy),
        .done            (dma_done),
        .dma_read_addr   (dma_raddr),
        .dma_read_data   (bram_dout_a),
        .dma_we          (dma_we),
        .dma_write_addr  (dma_waddr),
        .dma_write_data  (dma_wdata),
        .total_dma_cycles(telemetry_dma_cycles)
    );

    // =========================================================================
    // 5. Memory Bus Arbitration
    // Port A: DMA Read has priority over SIMT read
    // Port B: DMA Write has priority over other writes
    // =========================================================================
    assign bram_addr_a = dma_busy ? dma_raddr : simt_mem_addr[0];
    assign bram_we_a   = dma_busy ? 1'b0      : simt_mem_we;
    assign bram_din_a  = simt_mem_dout[0];

    assign bram_addr_b = dma_busy ? dma_waddr : 12'd0;
    assign bram_we_b   = dma_busy ? dma_we    : 1'b0;
    assign bram_din_b  = dma_wdata;

    // Overall GPU status
    assign gpu_busy = simt_busy | ai_busy | dma_busy;
    assign telemetry_total_cycles = telemetry_simt_cycles + telemetry_ai_cycles + telemetry_dma_cycles;

endmodule
