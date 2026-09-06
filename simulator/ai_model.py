# simulator/ai_model.py
"""
Quantized Neural Network running on HeteroGPU hardware:
- Layer 1: 4 Inputs -> 4 Hidden Neurons (Dense Linear: Matrix Engine)
- Activation: Parallel ReLU across 4 Neurons (SIMT Engine)
- Layer 2: 4 Hidden Neurons -> 2 Output Decisions (Dense Linear: Matrix Engine)
- Decision: Argmax (UP vs DOWN paddle control)
"""

class PongAIBrain:
    def __init__(self, gpu):
        self.gpu = gpu
        self._init_weights()
        self.load_weights_to_gpu()

    def _init_weights(self):
        # 4x4 Quantized weights for Layer 1
        # Features: [Ball_X, Ball_Y, Paddle_Y, Ball_DY]
        # Calibrated integer weights scaled by 32
        self.w1 = [
             10,  -5,   5,  -8,
            -20,  30, -25,  15,
             25, -30,  30, -15,
             -5,  15, -10,  20
        ]
        # 4x2 Quantized weights for Layer 2 (Output UP, Output DOWN)
        self.w2 = [
             35, -30,
            -40,  45,
             40, -35,
            -25,  30
        ]

    def load_weights_to_gpu(self):
        """Uses the DMA Engine to load neural network weights into BRAM."""
        self.gpu.run_dma_load(self.w1, dest_addr=self.gpu.AI_WEIGHTS_L1)
        self.gpu.run_dma_load(self.w2, dest_addr=self.gpu.AI_WEIGHTS_L2)

    def forward(self, ball_x, ball_y, paddle_y, ball_dy):
        """
        Executes a complete Heterogeneous AI Forward Inference Pass on hardware:
        1. DMA transfers inputs
        2. Matrix Engine computes GEMM Layer 1
        3. SIMT Engine executes parallel ReLU
        4. Matrix Engine computes GEMM Layer 2
        5. Returns decision (-1 = UP, 0 = STAY, 1 = DOWN)
        """
        # Step 1: DMA load input features into BRAM
        input_vector = [ball_x, ball_y, paddle_y, ball_dy]
        self.gpu.run_dma_load(input_vector, dest_addr=self.gpu.AI_INPUT_BUFFER)

        # Step 2: Matrix Engine computes Layer 1 (4 inputs -> 4 outputs)
        self.gpu.run_matrix_linear(
            in_addr=self.gpu.AI_INPUT_BUFFER,
            in_dim=4,
            weight_addr=self.gpu.AI_WEIGHTS_L1,
            out_dim=4,
            out_addr=self.gpu.AI_L1_ACTIVATIONS
        )

        # Step 3: SIMT Engine executes parallel ReLU activation across 4 PEs
        self.gpu.run_parallel_relu(
            base_addr=self.gpu.AI_L1_ACTIVATIONS,
            length=4
        )

        # Step 4: Matrix Engine computes Layer 2 (4 hidden -> 2 outputs)
        self.gpu.run_matrix_linear(
            in_addr=self.gpu.AI_L1_ACTIVATIONS,
            in_dim=4,
            weight_addr=self.gpu.AI_WEIGHTS_L2,
            out_dim=2,
            out_addr=self.gpu.AI_OUTPUT_BUFFER
        )

        # Step 5: Read decision from Output Buffer
        up_score_u16 = self.gpu.memory.read(self.gpu.AI_OUTPUT_BUFFER)
        down_score_u16 = self.gpu.memory.read(self.gpu.AI_OUTPUT_BUFFER + 1)

        # Convert back to signed
        up_score = up_score_u16 - 65536 if up_score_u16 >= 32768 else up_score_u16
        down_score = down_score_u16 - 65536 if down_score_u16 >= 32768 else down_score_u16

        # Decision
        if up_score > down_score:
            decision = -1  # Move paddle UP
        elif down_score > up_score:
            decision = 1   # Move paddle DOWN
        else:
            decision = 0   # Stay

        return decision, up_score, down_score


if __name__ == '__main__':
    from heterogpu import HeteroGPU
    gpu = HeteroGPU()
    brain = PongAIBrain(gpu)

    # Test Scenario: Ball is high (Y=5), Paddle is low (Y=20). AI should say UP (-1)!
    dec, up, down = brain.forward(ball_x=10, ball_y=5, paddle_y=20, ball_dy=-1)
    print(f"Scenario 1 (Ball above Paddle) -> Decision: {dec} (UpScore: {up}, DownScore: {down})")
    assert dec == -1, f"Expected -1 (UP), got {dec}"

    # Test Scenario: Ball is low (Y=25), Paddle is high (Y=5). AI should say DOWN (+1)!
    dec, up, down = brain.forward(ball_x=10, ball_y=25, paddle_y=5, ball_dy=1)
    print(f"Scenario 2 (Ball below Paddle) -> Decision: {dec} (UpScore: {up}, DownScore: {down})")
    assert dec == 1, f"Expected 1 (DOWN), got {dec}"

    print("\nHeterogeneous AI Neural Network successfully verified!")
    print("Telemetry:", gpu.get_telemetry())
