// =============================================================================
// Module: bram_memory.sv
// Target: Gowin GW1NR-9 (Tang Nano 9K FPGA)
// Description: Dual-Port Synchronous Block RAM (BRAM) for HeteroGPU.
// Memory Size: 4096 Words x 16-Bit = 65,536 Bits = 8 Kilobytes (KB).
// Hardware: Synthesizes directly into 4 to 5 Gowin BSRAM primitives.
// =============================================================================

module bram_memory #(
    parameter WORDS = 4096
)(
    input  logic        clk,

    // -------------------------------------------------------------------------
    // Port A: Read / Write (Connected to SIMT Engine & DMA Read Bus)
    // -------------------------------------------------------------------------
    input  logic        we_a,
    input  logic [11:0] addr_a,
    input  logic [15:0] din_a,
    output logic [15:0] dout_a,

    // -------------------------------------------------------------------------
    // Port B: Read / Write (Connected to Matrix Engine, DMA Write & Display)
    // -------------------------------------------------------------------------
    input  logic        we_b,
    input  logic [11:0] addr_b,
    input  logic [15:0] din_b,
    output logic [15:0] dout_b
);

    // 4096 words of 16-bit memory array
    // Synthesizes to Gowin GW1NR-9 Block RAM (BSRAM) primitives
    (* syn_ramstyle = "block_ram" *) logic [15:0] ram [0:WORDS-1];

    // Port A Synchronous Access
    always_ff @(posedge clk) begin
        if (we_a) begin
            ram[addr_a] <= din_a;
        end
        dout_a <= ram[addr_a];
    end

    // Port B Synchronous Access
    always_ff @(posedge clk) begin
        if (we_b) begin
            ram[addr_b] <= din_b;
        end
        dout_b <= ram[addr_b];
    end

endmodule
