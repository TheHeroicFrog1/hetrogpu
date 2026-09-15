# ==============================================================================
# Quantized Neural Network Brain (Embedded AI Inference Pipeline)
# Architecture: 2-Layer Multilayer Perceptron (MLP) running on HeteroGPU.
# Workload Pipeline:
#   - Layer 1 (Dense): 4 Inputs -> 4 Hidden Neurons (evaluated on 2x2 Systolic Array, 16 cycles)
#   - Layer 1 (Activation): Parallel ReLU (evaluated on 4-core SIMT engine, 5 cycles)
#   - Layer 2 (Dense): 4 Hidden Neurons -> 2 Action Logits (evaluated on 2x2 Systolic Array, 8 cycles)
#   - Decision Logic: Hardware Argmax [UP vs. DOWN] for paddle actuator control.
# Total Pipeline Latency: Exactly 34 clock cycles!
# ==============================================================================

class PongAIBrain:
    def __init__(self, gpu):
        self.gpu = gpu
        self._init_weights()
        self.load_weights_to_gpu()

    def _init_weights(self):
        # ----------------------------------------------------------------------
        # Quantized Fixed-Point Synaptic Weight Matrices:
        # Layer 1: 4x4 matrix (16 weights) mapping state features to hidden features.
        # Input Vector: [ball_x, ball_y, paddle_y, ball_dy]
        # Calibrated with trajectory prediction and bounce anticipation.
        # ----------------------------------------------------------------------
        self.w1 = [
             0,    0,  -8,  -8,   # Row 0: Ball_X feature weights
           -32,   32,   0,   0,   # Row 1: Ball_Y feature weights (ball altitude)
            32,  -32,  -8,   8,   # Row 2: Paddle_Y feature weights (paddle position)
           -16,   16,   0,   0    # Row 3: Ball_DY feature weights (velocity vector anticipation)
        ]
        
        # Layer 2: 4x2 matrix (8 weights) mapping 4 hidden neurons to 2 output actions [UP, DOWN]
        self.w2 = [
            48, -32,  # H0 (drives UP paddle movement)
           -32,  48,  # H1 (drives DOWN paddle movement)
            16, -16,  # H2 (center alignment bias UP)
           -16,  16   # H3 (center alignment bias DOWN)
        ]

    def load_weights_to_gpu(self):
        # Stage synaptic weight tensors into BRAM using DMA burst loader
        self.gpu.run_dma_load(self.w1, dest_addr=self.gpu.AI_WEIGHTS_L1)
        self.gpu.run_dma_load(self.w2, dest_addr=self.gpu.AI_WEIGHTS_L2)

    def forward(self, ball_x, ball_y, paddle_y, ball_dy):
        # ----------------------------------------------------------------------
        # End-to-End Heterogeneous Forward Pass Execution:
        # ----------------------------------------------------------------------

        # Stage 1: DMA streams current sensor inputs into BRAM input buffer (5 cycles: 1 setup + 4 words)
        input_features = [ball_x, ball_y, paddle_y, ball_dy]
        self.gpu.run_dma_load(input_features, dest_addr=self.gpu.AI_INPUT_BUFFER)

        # Stage 2: 2x2 Systolic Array computes Layer 1 GEMM: H_raw = Input * W1 (16 cycles)
        self.gpu.run_matrix_linear(
            in_addr=self.gpu.AI_INPUT_BUFFER,
            in_dim=4,
            weight_addr=self.gpu.AI_WEIGHTS_L1,
            out_dim=4,
            out_addr=self.gpu.AI_L1_ACTIVATIONS
        )

        # Stage 3: 4-Core SIMT engine computes parallel ReLU activation on H_raw in lockstep (5 cycles)
        self.gpu.run_parallel_relu(
            base_addr=self.gpu.AI_L1_ACTIVATIONS,
            length=4
        )

        # Stage 4: 2x2 Systolic Array computes Layer 2 GEMM: Output = H_activated * W2 (8 cycles)
        self.gpu.run_matrix_linear(
            in_addr=self.gpu.AI_L1_ACTIVATIONS,
            in_dim=4,
            weight_addr=self.gpu.AI_WEIGHTS_L2,
            out_dim=2,
            out_addr=self.gpu.AI_OUTPUT_BUFFER
        )

        # Stage 5: Read raw 16-bit action scores from BRAM and convert to signed values
        up_u16 = self.gpu.memory.read(self.gpu.AI_OUTPUT_BUFFER)
        down_u16 = self.gpu.memory.read(self.gpu.AI_OUTPUT_BUFFER + 1)

        # Two's complement conversion
        up_score = up_u16 - 65536 if up_u16 >= 32768 else up_u16
        down_score = down_u16 - 65536 if down_u16 >= 32768 else down_u16

        # Hardware Argmax Comparator: Select action with highest confidence score
        if up_score > down_score:
            decision = -1  # Actuate motor UP
        elif down_score > up_score:
            decision = 1   # Actuate motor DOWN
        else:
            decision = 0   # Maintain current trajectory (deadzone)

        return decision, up_score, down_score


if __name__ == '__main__':
    from heterogpu import HeteroGPU
    gpu = HeteroGPU()
    brain = PongAIBrain(gpu)

    # Test Case 1: Ball above paddle (y=5 vs paddle=20) -> should output UP (-1)
    act1, u1, d1 = brain.forward(10, 5, 20, -1)
    assert act1 == -1

    # Test Case 2: Ball below paddle (y=25 vs paddle=5) -> should output DOWN (1)
    act2, u2, d2 = brain.forward(10, 25, 5, 1)
    assert act2 == 1

    print("AI forward pass test passed!")
    print("Telemetry:", gpu.get_telemetry())
