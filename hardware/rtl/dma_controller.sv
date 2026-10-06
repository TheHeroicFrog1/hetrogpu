// =============================================================================
// Module: dma_controller.sv
// Target: Gowin GW1NR-9 (Tang Nano 9K FPGA)
// Description: Direct Memory Access (DMA) Burst Controller.
// Architecture: Autonomous hardware bus master executing high-speed memory-to-memory
//               burst copies with single-cycle pipelined BRAM read-to-write alignment.
// Timing: Fully pipelined 1 word/cycle throughput with proper 1-cycle BRAM latency delay.
// =============================================================================

`timescale 1ns / 1ps

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

    typedef enum logic [1:0] {
        DMA_IDLE   = 2'd0,
        DMA_BURST  = 2'd1,
        DMA_FINISH = 2'd2
    } dma_state_t;

    dma_state_t state;

    logic [11:0] read_ptr;
    logic [11:0] write_ptr;
    logic [11:0] reads_remaining;
    logic [11:0] writes_remaining;

    // 1-Cycle Pipeline Delay Registers for Destination Address & Write Enable
    // Compensates for synchronous BRAM Port A read latency
    logic [11:0] dest_addr_pipe;
    logic        we_pipe;

    assign dma_read_addr  = read_ptr;
    assign dma_write_addr = dest_addr_pipe;
    assign dma_write_data = dma_read_data; // BRAM Port A read data directly feeds Port B write data
    assign dma_we         = we_pipe;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state            <= DMA_IDLE;
            busy             <= 1'b0;
            done             <= 1'b0;
            read_ptr         <= 12'd0;
            write_ptr        <= 12'd0;
            dest_addr_pipe   <= 12'd0;
            we_pipe          <= 1'b0;
            reads_remaining  <= 12'd0;
            writes_remaining <= 12'd0;
            total_dma_cycles <= 32'd0;
        end else begin
            case (state)
                DMA_IDLE: begin
                    done    <= 1'b0;
                    we_pipe <= 1'b0;
                    if (start && (transfer_length > 0)) begin
                        busy             <= 1'b1;
                        read_ptr         <= src_addr;
                        write_ptr        <= dest_addr;
                        reads_remaining  <= transfer_length;
                        writes_remaining <= transfer_length;
                        total_dma_cycles <= total_dma_cycles + 32'd1;
                        state            <= DMA_BURST;
                    end else begin
                        busy <= 1'b0;
                    end
                end

                DMA_BURST: begin
                    total_dma_cycles <= total_dma_cycles + 32'd1;

                    // Read Pipeline Stage: Issue read address
                    if (reads_remaining > 0) begin
                        read_ptr         <= read_ptr + 12'd1;
                        reads_remaining  <= reads_remaining - 12'd1;
                        dest_addr_pipe   <= write_ptr;
                        write_ptr        <= write_ptr + 12'd1;
                        we_pipe          <= 1'b1;
                    end else begin
                        we_pipe          <= 1'b0;
                    end

                    // Write Pipeline Stage: Account for BRAM 1-cycle latency
                    if (we_pipe) begin
                        writes_remaining <= writes_remaining - 12'd1;
                        if (writes_remaining == 12'd1) begin
                            // Final write completes on next clock edge
                            state <= DMA_FINISH;
                        end
                    end
                end

                DMA_FINISH: begin
                    total_dma_cycles <= total_dma_cycles + 32'd1;
                    we_pipe <= 1'b0;
                    done    <= 1'b1;
                    busy    <= 1'b0;
                    state   <= DMA_IDLE;
                end

                default: state <= DMA_IDLE;
            endcase
        end
    end

endmodule
