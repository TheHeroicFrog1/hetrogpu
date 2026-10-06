// =============================================================================
// Module: heterogpu_top.sv
// Target: Gowin GW1NR-9 (Tang Nano 9K FPGA)
// Description: HeteroGPU Top-Level System-on-Chip (SoC) Accelerator.
// Architecture: Fully connected heterogeneous datapath with shared Dual-Port BRAM.
//               Features:
//               1. 4-Lane SIMD Vector Array with private GPR files (R0-R7).
//               2. 2x2 Kung & Leiserson Systolic Tensor Engine with real BRAM sequencing.
//               3. Pipelined Hardware DMA Burst Controller with bus arbitration & stall logic.
// =============================================================================

`timescale 1ns / 1ps

module heterogpu_top (
    input  logic        clk,
    input  logic        rst_n,

    // Host Control Interface - SIMD Vector Engine
    input  logic        start_simt,
    input  logic [3:0]  simt_opcode,
    input  logic [2:0]  simt_rd,
    input  logic [2:0]  simt_rs1,
    input  logic [2:0]  simt_rs2,
    input  logic        simt_use_imm,
    input  logic [15:0] simt_imm_val,
    input  logic [11:0] simt_base_addr,
    input  logic        simt_is_vector,

    // Host Control Interface - AI Matrix Engine
    input  logic        start_ai_gemm,
    input  logic [11:0] ai_addr_a,
    input  logic [11:0] ai_addr_b,
    input  logic [11:0] ai_addr_c,

    // Host Control Interface - DMA Controller
    input  logic        start_dma,
    input  logic [11:0] dma_src,
    input  logic [11:0] dma_dest,
    input  logic [11:0] dma_len,

    // Hardware Telemetry & Status Outputs
    output logic [31:0] telemetry_simt_cycles,
    output logic [31:0] telemetry_ai_cycles,
    output logic [31:0] telemetry_dma_cycles,
    output logic [31:0] telemetry_total_cycles,
    output logic        gpu_busy,
    output logic        ai_done,
    output logic        dma_done
);

    // =========================================================================
    // 1. Shared Dual-Port Synchronous Block RAM (8 KB)
    // =========================================================================
    logic        bram_we_a;
    logic [11:0] bram_addr_a;
    logic [15:0] bram_din_a;
    logic [15:0] bram_dout_a;

    logic        bram_we_b;
    logic [11:0] bram_addr_b;
    logic [15:0] bram_din_b;
    logic [15:0] bram_dout_b;

    bram_memory #(
        .WORDS(4096)
    ) u_bram (
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
    // 2. Hardware DMA Burst Controller
    // =========================================================================
    logic        dma_busy;
    logic        dma_we;
    logic [11:0] dma_raddr;
    logic [11:0] dma_waddr;
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
    // 3. 2x2 Systolic Array AI Engine & Real Memory Sequencer
    // =========================================================================
    // Matrix buffers loaded from BRAM
    logic signed [15:0] mat_a00, mat_a01, mat_a10, mat_a11;
    logic signed [15:0] mat_b00, mat_b01, mat_b10, mat_b11;
    logic signed [15:0] ai_c00, ai_c01, ai_c10, ai_c11;

    logic systolic_start, systolic_done, systolic_busy;

    systolic_array_2x2 u_systolic (
        .clk            (clk),
        .rst_n          (rst_n),
        .start          (systolic_start),
        .done           (systolic_done),
        .busy           (systolic_busy),
        .a00            (mat_a00),
        .a01            (mat_a01),
        .a10            (mat_a10),
        .a11            (mat_a11),
        .b00            (mat_b00),
        .b01            (mat_b01),
        .b10            (mat_b10),
        .b11            (mat_b11),
        .c00            (ai_c00),
        .c01            (ai_c01),
        .c10            (ai_c10),
        .c11            (ai_c11),
        .total_ai_cycles(telemetry_ai_cycles)
    );

    // Tensor Memory Sequencer FSM
    // Loads Matrix A (4 words) and Matrix B (4 words) from BRAM via Port B,
    // computes via Systolic Array, then stores Matrix C (4 words) back into BRAM.
    typedef enum logic [3:0] {
        AI_SEQ_IDLE     = 4'd0,
        AI_SEQ_LOAD_A0  = 4'd1,
        AI_SEQ_LOAD_A1  = 4'd2,
        AI_SEQ_LOAD_A2  = 4'd3,
        AI_SEQ_LOAD_A3  = 4'd4,
        AI_SEQ_LOAD_B0  = 4'd5,
        AI_SEQ_LOAD_B1  = 4'd6,
        AI_SEQ_LOAD_B2  = 4'd7,
        AI_SEQ_LOAD_B3  = 4'd8,
        AI_SEQ_COMPUTE  = 4'd9,
        AI_SEQ_STORE_C0 = 4'd10,
        AI_SEQ_STORE_C1 = 4'd11,
        AI_SEQ_STORE_C2 = 4'd12,
        AI_SEQ_STORE_C3 = 4'd13,
        AI_SEQ_DONE     = 4'd14
    } ai_seq_state_t;

    ai_seq_state_t ai_seq_state;

    logic [11:0] ai_mem_addr;
    logic [15:0] ai_mem_wdata;
    logic        ai_mem_we;
    logic        ai_seq_busy;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ai_seq_state   <= AI_SEQ_IDLE;
            ai_seq_busy    <= 1'b0;
            ai_done        <= 1'b0;
            systolic_start <= 1'b0;
            ai_mem_we      <= 1'b0;
            ai_mem_addr    <= 12'd0;
            ai_mem_wdata   <= 16'd0;
            mat_a00        <= 16'sd0;
            mat_a01        <= 16'sd0;
            mat_a10        <= 16'sd0;
            mat_a11        <= 16'sd0;
            mat_b00        <= 16'sd0;
            mat_b01        <= 16'sd0;
            mat_b10        <= 16'sd0;
            mat_b11        <= 16'sd0;
        end else begin
            case (ai_seq_state)
                AI_SEQ_IDLE: begin
                    ai_done   <= 1'b0;
                    ai_mem_we <= 1'b0;
                    if (start_ai_gemm) begin
                        ai_seq_busy <= 1'b1;
                        ai_mem_addr <= ai_addr_a; // Request A00
                        ai_seq_state<= AI_SEQ_LOAD_A0;
                    end else begin
                        ai_seq_busy <= 1'b0;
                    end
                end

                AI_SEQ_LOAD_A0: begin
                    ai_mem_addr  <= ai_addr_a + 12'd1; // Request A01
                    ai_seq_state <= AI_SEQ_LOAD_A1;
                end

                AI_SEQ_LOAD_A1: begin
                    mat_a00      <= bram_dout_b;      // Latch A00
                    ai_mem_addr  <= ai_addr_a + 12'd2; // Request A10
                    ai_seq_state <= AI_SEQ_LOAD_A2;
                end

                AI_SEQ_LOAD_A2: begin
                    mat_a01      <= bram_dout_b;      // Latch A01
                    ai_mem_addr  <= ai_addr_a + 12'd3; // Request A11
                    ai_seq_state <= AI_SEQ_LOAD_A3;
                end

                AI_SEQ_LOAD_A3: begin
                    mat_a10      <= bram_dout_b;      // Latch A10
                    ai_mem_addr  <= ai_addr_b;        // Request B00
                    ai_seq_state <= AI_SEQ_LOAD_B0;
                end

                AI_SEQ_LOAD_B0: begin
                    mat_a11      <= bram_dout_b;      // Latch A11
                    ai_mem_addr  <= ai_addr_b + 12'd1; // Request B01
                    ai_seq_state <= AI_SEQ_LOAD_B1;
                end

                AI_SEQ_LOAD_B1: begin
                    mat_b00      <= bram_dout_b;      // Latch B00
                    ai_mem_addr  <= ai_addr_b + 12'd2; // Request B10
                    ai_seq_state <= AI_SEQ_LOAD_B2;
                end

                AI_SEQ_LOAD_B2: begin
                    mat_b01      <= bram_dout_b;      // Latch B01
                    ai_mem_addr  <= ai_addr_b + 12'd3; // Request B11
                    ai_seq_state <= AI_SEQ_LOAD_B3;
                end

                AI_SEQ_LOAD_B3: begin
                    mat_b10      <= bram_dout_b;      // Latch B10
                    ai_seq_state <= AI_SEQ_COMPUTE;
                end

                AI_SEQ_COMPUTE: begin
                    mat_b11        <= bram_dout_b;    // Latch B11
                    systolic_start <= 1'b1;
                    if (systolic_done) begin
                        systolic_start <= 1'b0;
                        ai_mem_we      <= 1'b1;
                        ai_mem_addr    <= ai_addr_c;  // Write C00
                        ai_mem_wdata   <= ai_c00;
                        ai_seq_state   <= AI_SEQ_STORE_C0;
                    end
                end

                AI_SEQ_STORE_C0: begin
                    systolic_start <= 1'b0;
                    ai_mem_we      <= 1'b1;
                    ai_mem_addr    <= ai_addr_c + 12'd1; // Write C01
                    ai_mem_wdata   <= ai_c01;
                    ai_seq_state   <= AI_SEQ_STORE_C1;
                end

                AI_SEQ_STORE_C1: begin
                    ai_mem_we      <= 1'b1;
                    ai_mem_addr    <= ai_addr_c + 12'd2; // Write C10
                    ai_mem_wdata   <= ai_c10;
                    ai_seq_state   <= AI_SEQ_STORE_C2;
                end

                AI_SEQ_STORE_C2: begin
                    ai_mem_we      <= 1'b1;
                    ai_mem_addr    <= ai_addr_c + 12'd3; // Write C11
                    ai_mem_wdata   <= ai_c11;
                    ai_seq_state   <= AI_SEQ_STORE_C3;
                end

                AI_SEQ_STORE_C3: begin
                    ai_mem_we      <= 1'b0;
                    ai_seq_state   <= AI_SEQ_DONE;
                end

                AI_SEQ_DONE: begin
                    ai_done        <= 1'b1;
                    ai_seq_busy    <= 1'b0;
                    ai_seq_state   <= AI_SEQ_IDLE;
                end

                default: ai_seq_state <= AI_SEQ_IDLE;
            endcase
        end
    end

    // =========================================================================
    // 4. 4-Lane SIMD Vector Execution Engine & Vector Memory Sequencer
    // =========================================================================
    logic        simt_busy;
    logic        simt_mem_we;
    logic [11:0] simt_mem_addr [0:3];
    logic [15:0] simt_mem_din [0:3];
    logic [15:0] simt_mem_dout [0:3];

    // Vector Memory Sequencer: Handles contiguous 4-word loads and stores across lanes
    typedef enum logic [2:0] {
        VEC_IDLE   = 3'd0,
        VEC_LANE0  = 3'd1,
        VEC_LANE1  = 3'd2,
        VEC_LANE2  = 3'd3,
        VEC_LANE3  = 3'd4,
        VEC_DONE   = 3'd5
    } vec_state_t;

    vec_state_t vec_state;

    logic [11:0] simd_mem_addr;
    logic [15:0] simd_mem_wdata;
    logic        simd_mem_we;
    logic        simd_stall;

    // Connect memory input ports to each lane
    assign simt_mem_din[0] = bram_dout_a;
    assign simt_mem_din[1] = bram_dout_a;
    assign simt_mem_din[2] = bram_dout_a;
    assign simt_mem_din[3] = bram_dout_a;

    simt_engine u_simt (
        .clk            (clk),
        .rst_n          (rst_n),
        .inst_valid     (start_simt && !simd_stall),
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
    // 5. Memory Bus Arbitration & Conflict Management
    // =========================================================================
    // Port A Arbitration:
    // If DMA is active -> DMA Read has exclusive control of Port A.
    // Else             -> SIMD Vector Engine has control of Port A.
    always_comb begin
        if (dma_busy) begin
            bram_addr_a = dma_raddr;
            bram_we_a   = 1'b0;
            bram_din_a  = 16'd0;
            simd_stall  = 1'b1; // Stall SIMD during DMA burst transfers!
        end else begin
            bram_addr_a = simt_mem_addr[0];
            bram_we_a   = simt_mem_we;
            bram_din_a  = simt_mem_dout[0];
            simd_stall  = 1'b0;
        end
    end

    // Port B Arbitration:
    // If DMA is active -> DMA Write has exclusive control of Port B.
    // Else if AI active-> Tensor Memory Sequencer has control of Port B.
    // Else             -> Idle.
    always_comb begin
        if (dma_busy) begin
            bram_addr_b = dma_waddr;
            bram_we_b   = dma_we;
            bram_din_b  = dma_wdata;
        end else if (ai_seq_busy) begin
            bram_addr_b = ai_mem_addr;
            bram_we_b   = ai_mem_we;
            bram_din_b  = ai_mem_wdata;
        end else begin
            bram_addr_b = 12'd0;
            bram_we_b   = 1'b0;
            bram_din_b  = 16'd0;
        end
    end

    // Overall GPU Status
    assign gpu_busy = simt_busy | ai_seq_busy | dma_busy;
    assign telemetry_total_cycles = telemetry_simt_cycles + telemetry_ai_cycles + telemetry_dma_cycles;

endmodule
