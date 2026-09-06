# 2-layer MLP neural network for pong tracking
# Layer 1: 4 inputs -> 4 hidden (evaluated on 2x2 matrix engine + SIMT ReLU)
# Layer 2: 4 hidden -> 2 output actions (evaluated on 2x2 matrix engine)

class PongAIBrain:
    def __init__(self, gpu):
        self.gpu = gpu
        self._init_weights()
        self.load_weights_to_gpu()

    def _init_weights(self):
        # 4x4 integer weights for Layer 1
        # inputs: [ball_x, ball_y, paddle_y, ball_dy]
        self.w1 = [
             10,  -5,   5,  -8,
            -20,  30, -25,  15,
             25, -30,  30, -15,
             -5,  15, -10,  20
        ]
        # 4x2 integer weights for Layer 2: output scores for [UP, DOWN]
        self.w2 = [
             35, -30,
            -40,  45,
             40, -35,
            -25,  30
        ]

    def load_weights_to_gpu(self):
        # use DMA to copy weights into BRAM
        self.gpu.run_dma_load(self.w1, dest_addr=self.gpu.AI_WEIGHTS_L1)
        self.gpu.run_dma_load(self.w2, dest_addr=self.gpu.AI_WEIGHTS_L2)

    def forward(self, ball_x, ball_y, paddle_y, ball_dy):
        # 1. DMA moves sensor inputs into input buffer
        input_features = [ball_x, ball_y, paddle_y, ball_dy]
        self.gpu.run_dma_load(input_features, dest_addr=self.gpu.AI_INPUT_BUFFER)

        # 2. Layer 1: Matrix Engine computes W1 * X
        self.gpu.run_matrix_linear(
            in_addr=self.gpu.AI_INPUT_BUFFER,
            in_dim=4,
            weight_addr=self.gpu.AI_WEIGHTS_L1,
            out_dim=4,
            out_addr=self.gpu.AI_L1_ACTIVATIONS
        )

        # 3. Layer 1 Activation: SIMT cores run parallel ReLU in 5 cycles
        self.gpu.run_parallel_relu(
            base_addr=self.gpu.AI_L1_ACTIVATIONS,
            length=4
        )

        # 4. Layer 2: Matrix Engine computes W2 * H
        self.gpu.run_matrix_linear(
            in_addr=self.gpu.AI_L1_ACTIVATIONS,
            in_dim=4,
            weight_addr=self.gpu.AI_WEIGHTS_L2,
            out_dim=2,
            out_addr=self.gpu.AI_OUTPUT_BUFFER
        )

        # 5. Read output scores from BRAM and pick action
        up_u16 = self.gpu.memory.read(self.gpu.AI_OUTPUT_BUFFER)
        down_u16 = self.gpu.memory.read(self.gpu.AI_OUTPUT_BUFFER + 1)

        # convert 16-bit unsigned to signed
        up_score = up_u16 - 65536 if up_u16 >= 32768 else up_u16
        down_score = down_u16 - 65536 if down_u16 >= 32768 else down_u16

        # simple argmax
        if up_score > down_score:
            decision = -1  # move paddle up
        elif down_score > up_score:
            decision = 1   # move paddle down
        else:
            decision = 0   # stay

        return decision, up_score, down_score


if __name__ == '__main__':
    from heterogpu import HeteroGPU
    gpu = HeteroGPU()
    brain = PongAIBrain(gpu)

    # quick test: ball above paddle -> should output UP (-1)
    act1, u1, d1 = brain.forward(10, 5, 20, -1)
    assert act1 == -1

    # ball below paddle -> should output DOWN (1)
    act2, u2, d2 = brain.forward(10, 25, 5, 1)
    assert act2 == 1

    print("AI forward pass test passed!")
    print("Telemetry:", gpu.get_telemetry())
