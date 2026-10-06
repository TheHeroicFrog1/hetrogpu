// =============================================================================
// Module: systolic_array_2x2.sv
// Target: Gowin GW1NR-9 (Tang Nano 9K FPGA)
// Description: True 2x2 2D Systolic Array AI Matrix Engine (Tensor Processing Unit).
// Architecture: 2D mesh of 4 physical Multiply-Accumulate (MAC) processing elements.
// Dataflow: Kung & Leiserson (1979) systolic flow (inputs stream horizontally,
//           weights stream vertically). Completes a 2x2 GEMM in 4 clock cycles!
// Hardware: Synthesizes to 4 physical FPGA DSP blocks (Tang Nano 9K has 20 DSPs).
// =============================================================================

`timescale 1ns / 1ps

// -----------------------------------------------------------------------------
// Submodule: Processing Element (PE) MAC Unit
// Contains a 16x16 signed multiplier, a 32-bit accumulator, and forwarding registers.
// -----------------------------------------------------------------------------
module systolic_pe (
    input  logic               clk,
    input  logic               rst_n,
    input  logic               clear_acc,
    input  logic               enable_mac,
    input  logic signed [15:0] a_in,
    input  logic signed [15:0] b_in,
    output logic signed [15:0] a_out,
    output logic signed [15:0] b_out,
    output logic signed [31:0] acc_out
);

    logic signed [31:0] acc;
    logic signed [15:0] a_reg, b_reg;

    assign acc_out = acc;
    assign a_out   = a_reg;
    assign b_out   = b_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc   <= 32'sd0;
            a_reg <= 16'sd0;
            b_reg <= 16'sd0;
        end else begin
            if (clear_acc) begin
                acc <= 32'sd0;
            end else if (enable_mac) begin
                acc <= acc + (a_in * b_in);
            end

            // Forward data along systolic dimensions on clock edge
            a_reg <= a_in;
            b_reg <= b_in;
        end
    end

endmodule


// -----------------------------------------------------------------------------
// Top 2x2 Systolic Array Mesh
// -----------------------------------------------------------------------------
module systolic_array_2x2 (
    input  logic               clk,
    input  logic               rst_n,

    // Control & Command Interface
    input  logic               start,
    output logic               done,
    output logic               busy,

    // Matrix Input Ports (16-bit Signed Values)
    // Matrix A: [a00, a01; a10, a11]
    input  logic signed [15:0] a00,
    input  logic signed [15:0] a01,
    input  logic signed [15:0] a10,
    input  logic signed [15:0] a11,

    // Matrix B: [b00, b01; b10, b11]
    input  logic signed [15:0] b00,
    input  logic signed [15:0] b01,
    input  logic signed [15:0] b10,
    input  logic signed [15:0] b11,

    // Scaled Matrix Output: C = (A * B) >>> 5 (Fixed-point scaling matching golden model)
    output logic signed [15:0] c00,
    output logic signed [15:0] c01,
    output logic signed [15:0] c10,
    output logic signed [15:0] c11,

    // Hardware Telemetry
    output logic [31:0]        total_ai_cycles
);

    // 4-cycle state machine
    typedef enum logic [2:0] {
        IDLE    = 3'd0,
        CYCLE_1 = 3'd1, // Inject skewed inputs: PE00 receives A00, B00
        CYCLE_2 = 3'd2, // PE00: A01, B10; PE01: A00, B01; PE10: A10, B00
        CYCLE_3 = 3'd3, // PE01: A01, B11; PE10: A11, B10; PE11: A10, B01
        CYCLE_4 = 3'd4, // PE11: A11, B11 (final MAC completes)
        LATCH   = 3'd5  // Latch outputs with uniform fixed-point scaling
    } state_t;

    state_t state;

    // PE Interconnect Wires
    logic clear_all, en_mac00, en_mac01, en_mac10, en_mac11;
    logic signed [15:0] pe00_a_in, pe00_b_in, pe00_a_out, pe00_b_out;
    logic signed [15:0] pe01_a_in, pe01_b_in, pe01_a_out, pe01_b_out;
    logic signed [15:0] pe10_a_in, pe10_b_in, pe10_a_out, pe10_b_out;
    logic signed [15:0] pe11_a_in, pe11_b_in, pe11_a_out, pe11_b_out;

    logic signed [31:0] acc00, acc01, acc10, acc11;

    // -------------------------------------------------------------------------
    // Instantiate the 4 Physical MAC Processing Elements in 2D Mesh
    // -------------------------------------------------------------------------
    // PE [0,0]
    systolic_pe pe_00 (
        .clk        (clk),
        .rst_n      (rst_n),
        .clear_acc  (clear_all),
        .enable_mac (en_mac00),
        .a_in       (pe00_a_in),
        .b_in       (pe00_b_in),
        .a_out      (pe00_a_out),
        .b_out      (pe00_b_out),
        .acc_out    (acc00)
    );

    // PE [0,1] - Receives activation horizontally from PE [0,0]
    systolic_pe pe_01 (
        .clk        (clk),
        .rst_n      (rst_n),
        .clear_acc  (clear_all),
        .enable_mac (en_mac01),
        .a_in       (pe01_a_in),
        .b_in       (pe01_b_in),
        .a_out      (pe01_a_out),
        .b_out      (pe01_b_out),
        .acc_out    (acc01)
    );

    // PE [1,0] - Receives weight vertically from PE [0,0]
    systolic_pe pe_10 (
        .clk        (clk),
        .rst_n      (rst_n),
        .clear_acc  (clear_all),
        .enable_mac (en_mac10),
        .a_in       (pe10_a_in),
        .b_in       (pe10_b_in),
        .a_out      (pe10_a_out),
        .b_out      (pe10_b_out),
        .acc_out    (acc10)
    );

    // PE [1,1] - Receives activation from PE [1,0] and weight from PE [0,1]
    systolic_pe pe_11 (
        .clk        (clk),
        .rst_n      (rst_n),
        .clear_acc  (clear_all),
        .enable_mac (en_mac11),
        .a_in       (pe11_a_in),
        .b_in       (pe11_b_in),
        .a_out      (pe11_a_out),
        .b_out      (pe11_b_out),
        .acc_out    (acc11)
    );

    // -------------------------------------------------------------------------
    // Systolic Skewing & Interconnect Multiplexing
    // -------------------------------------------------------------------------
    always_comb begin
        // Defaults
        clear_all = 1'b0;
        en_mac00  = 1'b0;
        en_mac01  = 1'b0;
        en_mac10  = 1'b0;
        en_mac11  = 1'b0;

        pe00_a_in = 16'sd0;
        pe00_b_in = 16'sd0;
        pe01_a_in = pe00_a_out; // Horizontal stream
        pe01_b_in = 16'sd0;
        pe10_a_in = 16'sd0;
        pe10_b_in = pe00_b_out; // Vertical stream
        pe11_a_in = pe10_a_out;
        pe11_b_in = pe01_b_out;

        case (state)
            CYCLE_1: begin
                // Wavefront 1: PE00 receives (A00, B00)
                en_mac00  = 1'b1;
                pe00_a_in = a00;
                pe00_b_in = b00;
            end

            CYCLE_2: begin
                // Wavefront 2:
                // PE00 receives (A01, B10) -> finishes C00!
                // PE01 receives forwarded A00 from PE00, external B01
                // PE10 receives external A10, forwarded B00 from PE00
                en_mac00  = 1'b1;
                en_mac01  = 1'b1;
                en_mac10  = 1'b1;
                pe00_a_in = a01;
                pe00_b_in = b10;
                pe01_b_in = b01;
                pe10_a_in = a10;
            end

            CYCLE_3: begin
                // Wavefront 3:
                // PE01 receives forwarded A01 from PE00, external B11 -> finishes C01!
                // PE10 receives external A11, forwarded B10 from PE00 -> finishes C10!
                // PE11 receives forwarded A10 from PE10, forwarded B01 from PE01
                en_mac01  = 1'b1;
                en_mac10  = 1'b1;
                en_mac11  = 1'b1;
                pe00_a_in = a01;
                pe00_b_in = b10;
                pe01_b_in = b11;
                pe10_a_in = a11;
            end

            CYCLE_4: begin
                // Wavefront 4:
                // PE11 receives forwarded A11 from PE10, forwarded B11 from PE01 -> finishes C11!
                en_mac11  = 1'b1;
                pe10_a_in = a11;
                pe01_b_in = b11;
            end

            default: ;
        endcase
    end

    // -------------------------------------------------------------------------
    // Systolic FSM & Cycle Telemetry
    // -------------------------------------------------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state           <= IDLE;
            busy            <= 1'b0;
            done            <= 1'b0;
            total_ai_cycles <= 32'd0;
            c00             <= 16'sd0;
            c01             <= 16'sd0;
            c10             <= 16'sd0;
            c11             <= 16'sd0;
        end else begin
            case (state)
                IDLE: begin
                    done <= 1'b0;
                    if (start) begin
                        busy            <= 1'b1;
                        total_ai_cycles <= total_ai_cycles + 32'd1;
                        state           <= CYCLE_1;
                    end else begin
                        busy <= 1'b0;
                    end
                end

                CYCLE_1: begin
                    total_ai_cycles <= total_ai_cycles + 32'd1;
                    state           <= CYCLE_2;
                end

                CYCLE_2: begin
                    total_ai_cycles <= total_ai_cycles + 32'd1;
                    state           <= CYCLE_3;
                end

                CYCLE_3: begin
                    total_ai_cycles <= total_ai_cycles + 32'd1;
                    state           <= CYCLE_4;
                end

                CYCLE_4: begin
                    total_ai_cycles <= total_ai_cycles + 32'd1;
                    state           <= LATCH;
                end

                LATCH: begin
                    // Latch all 4 accumulators with identical arithmetic shift right (>>> 5)
                    c00   <= acc00 >>> 5;
                    c01   <= acc01 >>> 5;
                    c10   <= acc10 >>> 5;
                    c11   <= acc11 >>> 5;
                    done  <= 1'b1;
                    busy  <= 1'b0;
                    state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
