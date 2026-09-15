// =============================================================================
// Synopsys Design Constraints (.sdc) for Sipeed Tang Nano 9K
// Target Frequency: 27.0 MHz (Period = 37.037 ns)
// =============================================================================

create_clock -name clk -period 37.037 -waveform {0 18.518} [get_ports {clk}]
