// =============================================================================
// Testbench: tb_heterogpu.sv
// Target: Icarus Verilog / ModelSim / Verilator / Gowin Simulation
// Description: Strict Self-Checking Verification Testbench for HeteroGPU SoC.
//              Features real memory initialization, golden matrix multiplication
//              checking, DMA pipeline bounds assertion, and PE ALU verification.
// =============================================================================

`timescale 1ns / 1ps

module tb_heterogpu;

    // 27 MHz Clock Generation (Tang Nano 9K onboard oscillator: ~37.04 ns period)
    logic clk;
    logic rst_n;

    initial begin
        clk = 0;
        forever #18.5 clk = ~clk; // 27 MHz clock
    end

    // Top-Level SoC Signals
    logic        start_simt;
    logic [3:0]  simt_opcode;
    logic [2:0]  simt_rd;
    logic [2:0]  simt_rs1;
    logic [2:0]  simt_rs2;
    logic        simt_use_imm;
    logic [15:0] simt_imm_val;
    logic [11:0] simt_base_addr;
    logic        simt_is_vector;

    logic        start_ai_gemm;
    logic [11:0] ai_addr_a;
    logic [11:0] ai_addr_b;
    logic [11:0] ai_addr_c;

    logic        start_dma;
    logic [11:0] dma_src;
    logic [11:0] dma_dest;
    logic [11:0] dma_len;

    logic [31:0] tel_simt;
    logic [31:0] tel_ai;
    logic [31:0] tel_dma;
    logic [31:0] tel_total;
    logic        gpu_busy;
    logic        ai_done;
    logic        dma_done;

    // Instantiate Top-Level HeteroGPU SoC
    heterogpu_top uut (
        .clk                   (clk),
        .rst_n                 (rst_n),
        .start_simt            (start_simt),
        .simt_opcode           (simt_opcode),
        .simt_rd               (simt_rd),
        .simt_rs1              (simt_rs1),
        .simt_rs2              (simt_rs2),
        .simt_use_imm          (simt_use_imm),
        .simt_imm_val          (simt_imm_val),
        .simt_base_addr        (simt_base_addr),
        .simt_is_vector        (simt_is_vector),
        .start_ai_gemm         (start_ai_gemm),
        .ai_addr_a             (ai_addr_a),
        .ai_addr_b             (ai_addr_b),
        .ai_addr_c             (ai_addr_c),
        .start_dma             (start_dma),
        .dma_src               (dma_src),
        .dma_dest              (dma_dest),
        .dma_len               (dma_len),
        .telemetry_simt_cycles (tel_simt),
        .telemetry_ai_cycles   (tel_ai),
        .telemetry_dma_cycles  (tel_dma),
        .telemetry_total_cycles(tel_total),
        .gpu_busy              (gpu_busy),
        .ai_done               (ai_done),
        .dma_done              (dma_done)
    );

    // =========================================================================
    // Self-Checking Test Sequence
    // =========================================================================
    integer i;

    initial begin
        // Setup VCD Waveform Dump for GTKWave / WaveTrace
        $dumpfile("hardware/sim/waves.vcd");
        $dumpvars(0, tb_heterogpu);

        $display("\n=================================================================");
        $display("   HeteroGPU Silicon Verification Suite (Self-Checking Assertions)");
        $display("=================================================================");

        // Reset system
        rst_n          = 0;
        start_simt     = 0;
        simt_opcode    = 0;
        simt_rd        = 0;
        simt_rs1       = 0;
        simt_rs2       = 0;
        simt_use_imm   = 0;
        simt_imm_val   = 0;
        simt_base_addr = 0;
        simt_is_vector = 0;
        start_ai_gemm  = 0;
        ai_addr_a      = 0;
        ai_addr_b      = 0;
        ai_addr_c      = 0;
        start_dma      = 0;
        dma_src        = 0;
        dma_dest       = 0;
        dma_len        = 0;

        #100;
        rst_n = 1;
        #40;

        // ---------------------------------------------------------------------
        // Test 1: PE Core ALU & ReLU Sign-Bit Clamping Assertion
        // ---------------------------------------------------------------------
        $display("\n[Test 1] Testing PE Core Instructions (LOAD, RELU)...");

        // Step 1A: Load negative number -15 (0xFFF1) into R1
        @(posedge clk);
        start_simt   = 1;
        simt_opcode  = 4'd1;        // OP_LOAD
        simt_rd      = 3'd1;        // R1
        simt_use_imm = 1;
        simt_imm_val = 16'hFFF1;    // -15 in two's complement

        @(posedge clk);
        // Step 1B: Execute ReLU on R1 into R2 (Negative must clamp to 0)
        simt_opcode  = 4'd9;        // OP_RELU
        simt_rd      = 3'd2;        // R2
        simt_rs1     = 3'd1;        // R1
        simt_use_imm = 0;

        @(posedge clk);
        // Step 1C: Load positive number +42 (0x002A) into R1
        simt_opcode  = 4'd1;        // OP_LOAD
        simt_rd      = 3'd1;        // R1
        simt_use_imm = 1;
        simt_imm_val = 16'h002A;    // +42

        @(posedge clk);
        // Step 1D: Execute ReLU on positive R1 into R3 (Positive must pass through unchanged)
        simt_opcode  = 4'd9;        // OP_RELU
        simt_rd      = 3'd3;        // R3
        simt_rs1     = 3'd1;        // R1
        simt_use_imm = 0;

        @(posedge clk);
        start_simt   = 0;
        #20;

        // Rigorous Self-Checking Assertions for PE
        if (uut.u_simt.gen_pes[0].u_pe.registers[2] !== 16'h0000) begin
            $display("[FATAL ERROR] Test 1 Failed: ReLU did not clamp negative value to 0! Got: %h",
                     uut.u_simt.gen_pes[0].u_pe.registers[2]);
            $fatal(1);
        end

        if (uut.u_simt.gen_pes[0].u_pe.registers[3] !== 16'h002A) begin
            $display("[FATAL ERROR] Test 1 Failed: ReLU altered positive value! Expected 0x002A, Got: %h",
                     uut.u_simt.gen_pes[0].u_pe.registers[3]);
            $fatal(1);
        end

        $display("  -> [ASSERTION PASSED] PE Core ReLU clamped negative to 0 and preserved positive 42!");

        // ---------------------------------------------------------------------
        // Test 2: Real 2x2 Systolic Array GEMM from BRAM Memory
        // ---------------------------------------------------------------------
        $display("\n[Test 2] Testing 2x2 Systolic GEMM with Real BRAM Load/Compute/Store...");

        // Initialize Matrix A at BRAM addresses 100..103 in Q5 fixed-point:
        // A = [32, 64; 96, 128]  (representing [1.0, 2.0; 3.0, 4.0])
        uut.u_bram.ram[100] = 16'sd32;
        uut.u_bram.ram[101] = 16'sd64;
        uut.u_bram.ram[102] = 16'sd96;
        uut.u_bram.ram[103] = 16'sd128;

        // Initialize Matrix B at BRAM addresses 110..113 in Q5 fixed-point:
        // B = [64, 32; 32, 64]  (representing [2.0, 1.0; 1.0, 2.0])
        uut.u_bram.ram[110] = 16'sd64;
        uut.u_bram.ram[111] = 16'sd32;
        uut.u_bram.ram[112] = 16'sd32;
        uut.u_bram.ram[113] = 16'sd64;

        // Clear destination BRAM addresses 120..123
        uut.u_bram.ram[120] = 16'sd0;
        uut.u_bram.ram[121] = 16'sd0;
        uut.u_bram.ram[122] = 16'sd0;
        uut.u_bram.ram[123] = 16'sd0;

        // Expected Mathematical Golden Results:
        // C00 = (32*64 + 64*32) >>> 5 = (2048 + 2048) >>> 5 = 4096 >>> 5 = 128 (4.0)
        // C01 = (32*32 + 64*64) >>> 5 = (1024 + 4096) >>> 5 = 5120 >>> 5 = 160 (5.0)
        // C10 = (96*64 + 128*32) >>> 5 = (6144 + 4096) >>> 5 = 10240 >>> 5 = 320 (10.0)
        // C11 = (96*32 + 128*64) >>> 5 = (3072 + 8192) >>> 5 = 11264 >>> 5 = 352 (11.0)

        @(posedge clk);
        start_ai_gemm = 1;
        ai_addr_a     = 12'd100;
        ai_addr_b     = 12'd110;
        ai_addr_c     = 12'd120;

        @(posedge clk);
        start_ai_gemm = 0;

        // Wait for real hardware sequencer and systolic array completion
        wait(ai_done == 1'b1);
        @(posedge clk);

        // Rigorous Self-Checking Output Matrix Assertions
        if (uut.u_bram.ram[120] !== 16'sd128) begin
            $display("[FATAL ERROR] Test 2 Failed: C00 mismatch! Expected 128, Got: %0d", uut.u_bram.ram[120]);
            $fatal(1);
        end
        if (uut.u_bram.ram[121] !== 16'sd160) begin
            $display("[FATAL ERROR] Test 2 Failed: C01 mismatch! Expected 160, Got: %0d", uut.u_bram.ram[121]);
            $fatal(1);
        end
        if (uut.u_bram.ram[122] !== 16'sd320) begin
            $display("[FATAL ERROR] Test 2 Failed: C10 mismatch! Expected 320, Got: %0d", uut.u_bram.ram[122]);
            $fatal(1);
        end
        if (uut.u_bram.ram[123] !== 16'sd352) begin
            $display("[FATAL ERROR] Test 2 Failed: C11 mismatch! Expected 352, Got: %0d", uut.u_bram.ram[123]);
            $fatal(1);
        end

        $display("  -> [ASSERTION PASSED] 2x2 Systolic Array GEMM verified in BRAM!");
        $display("     C = [[%0d, %0d], [%0d, %0d]] matches Golden Model exactly!",
                 uut.u_bram.ram[120], uut.u_bram.ram[121], uut.u_bram.ram[122], uut.u_bram.ram[123]);
        $display("     Active Systolic Array Core Cycles: %0d", tel_ai);

        // ---------------------------------------------------------------------
        // Test 3: Hardware DMA Burst Transfer with Bounds & Offset Assertions
        // ---------------------------------------------------------------------
        $display("\n[Test 3] Testing Pipelined Hardware DMA Burst Controller...");

        // Initialize Source Memory at addresses 300..307 with unique test vectors
        uut.u_bram.ram[300] = 16'hA001;
        uut.u_bram.ram[301] = 16'hB002;
        uut.u_bram.ram[302] = 16'hC003;
        uut.u_bram.ram[303] = 16'hD004;
        uut.u_bram.ram[304] = 16'hE005;
        uut.u_bram.ram[305] = 16'hF006;
        uut.u_bram.ram[306] = 16'h7007;
        uut.u_bram.ram[307] = 16'h8008;

        // Clear destination memory at 400..407
        for (i = 0; i < 8; i = i + 1) begin
            uut.u_bram.ram[400 + i] = 16'h0000;
        end

        // Set Sentinel guard words to catch off-by-one underflows or overflows
        uut.u_bram.ram[399] = 16'hBEEF; // Must remain 0xBEEF
        uut.u_bram.ram[408] = 16'hDEAD; // Must remain 0xDEAD

        @(posedge clk);
        start_dma = 1;
        dma_src   = 12'd300;
        dma_dest  = 12'd400;
        dma_len   = 12'd8;

        @(posedge clk);
        start_dma = 0;

        // Wait for DMA completion
        wait(dma_done == 1'b1);
        @(posedge clk);

        // Rigorous Self-Checking Assertions for DMA
        for (i = 0; i < 8; i = i + 1) begin
            if (uut.u_bram.ram[400 + i] !== uut.u_bram.ram[300 + i]) begin
                $display("[FATAL ERROR] Test 3 Failed: DMA word mismatch at index %0d! Expected %h, Got: %h",
                         i, uut.u_bram.ram[300 + i], uut.u_bram.ram[400 + i]);
                $fatal(1);
            end
        end

        // Assert guard words were NOT overwritten
        if (uut.u_bram.ram[399] !== 16'hBEEF) begin
            $display("[FATAL ERROR] Test 3 Failed: DMA underflow corrupted guard address 399!");
            $fatal(1);
        end
        if (uut.u_bram.ram[408] !== 16'hDEAD) begin
            $display("[FATAL ERROR] Test 3 Failed: DMA overflow corrupted guard address 408!");
            $fatal(1);
        end

        $display("  -> [ASSERTION PASSED] DMA 8-word burst verified! All 8 words match with zero offset.");
        $display("     Sentinel guards [399] and [408] intact (No buffer over/underflow).");
        $display("     DMA Burst Elapsed Cycles: %0d", tel_dma);

        // ---------------------------------------------------------------------
        // Final Summary
        // ---------------------------------------------------------------------
        #100;
        $display("\n=================================================================");
        $display("   ALL HARDWARE ASSERTIONS PASSED WITH 100%% SILICON ACCURACY!   ");
        $display("   Telemetry Total Cycles: %0d                                    ", tel_total);
        $display("=================================================================\n");

        $finish;
    end

endmodule
