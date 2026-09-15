// =============================================================================
// Module: dma_controller.sv
// Target: Gowin GW1NR-9 (Tang Nano 9K FPGA)
// Description: Direct Memory Access (DMA) Burst Controller.
// Architecture: Autonomous hardware bus master executing high-speed memory-to-memory
//               burst copies without stalling SIMT or Matrix compute engines.
// Timing: T_dma = 1 (Setup/Bus Arbitration) + N (Burst Word Cycles).
// =============================================================================

module dma_controller (
    input  logic        clk,
    input  logic        rst_n,

    // Command Interface
    input  logic        start,
    input  logic [11:0] src_addr,
    input  logic [11:0] dest_addr,
    input  logic [11:0] transfer_length,
    output logic        busy,
    output logic        done,

    // Memory Master Read Bus (To BRAM Port A)
    output logic [11:0] dma_read_addr,
    input  logic [15:0] dma_read_data,

    // Memory Master Write Bus (To BRAM Port B)
    output logic        dma_we,
    output logic [11:0] dma_write_addr,
    output logic [15:0] dma_write_data,

    // Hardware Telemetry
    output logic [31:0] total_dma_cycles
);

    // DMA State Machine
    typedef enum logic [2:0] {
        DMA_IDLE       = 3'd0,
        DMA_SETUP      = 3'd1, // 1 cycle bus arbitration / address setup
        DMA_READ_BURST = 3'd2, // Auto-incrementing read pointer
        DMA_WRITE_BURST= 3'd3, // Auto-incrementing write pointer
        DMA_COMPLETE   = 3'd4
    } dma_state_t;

    dma_state_t state;

    logic [11:0] current_src;
    logic [11:0] current_dest;
    logic [11:0] words_left;

    assign dma_read_addr  = current_src;
    assign dma_write_addr = current_dest;
    assign dma_write_data = dma_read_data;

    // =========================================================================
    // DMA State Machine & Auto-Increment Counters
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state            <= DMA_IDLE;
            busy             <= 1'b0;
            done             <= 1'b0;
            dma_we           <= 1'b0;
            current_src      <= 12'd0;
            current_dest     <= 12'd0;
            words_left       <= 12'd0;
            total_dma_cycles <= 32'd0;
        end else begin
            case (state)
                DMA_IDLE: begin
                    done   <= 1'b0;
                    dma_we <= 1'b0;
                    if (start) begin
                        busy             <= 1'b1;
                        current_src      <= src_addr;
                        current_dest     <= dest_addr;
                        words_left       <= transfer_length;
                        total_dma_cycles <= total_dma_cycles + 32'd1; // 1 setup cycle
                        state            <= DMA_SETUP;
                    end else begin
                        busy <= 1'b0;
                    end
                end

                DMA_SETUP: begin
                    // 1 cycle bus arbitration
                    state <= DMA_READ_BURST;
                end

                DMA_READ_BURST: begin
                    // Streaming read and write in parallel burst
                    if (words_left > 0) begin
                        dma_we           <= 1'b1;
                        current_src      <= current_src + 12'd1;
                        current_dest     <= current_dest + 12'd1;
                        words_left       <= words_left - 12'd1;
                        total_dma_cycles <= total_dma_cycles + 32'd1; // 1 cycle per word
                    end else begin
                        dma_we <= 1'b0;
                        done   <= 1'b1;
                        busy   <= 1'b0;
                        state  <= DMA_COMPLETE;
                    end
                end

                DMA_COMPLETE: begin
                    done  <= 1'b0;
                    state <= DMA_IDLE;
                end

                default: state <= DMA_IDLE;
            endcase
        end
    end

endmodule
