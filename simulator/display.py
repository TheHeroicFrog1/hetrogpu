# simulator/display.py
import pygame
import sys
import time
from memory import Memory
from simt_engine import SIMTEngine
from matrix_engine import MatrixEngine

class VirtualMonitor:
    def __init__(self, memory, fb_base_addr=0, width=32, height=32, scale=16):
        """
        Creates a virtual monitor that displays the GPU's framebuffer.
        width/height: Resolution of our mini-GPU (32x32).
        scale: Scale factor for desktop display (32x16 = 512x512 window).
        """
        self.memory = memory
        self.fb_base_addr = fb_base_addr
        self.width = width
        self.height = height
        self.scale = scale
        
        pygame.init()
        self.screen = pygame.display.set_mode((self.width * self.scale, self.height * self.scale))
        pygame.display.set_caption("HeteroGPU 32x32 Virtual Monitor (SIMT Rendered)")
        self.clock = pygame.time.Clock()
        
    def refresh(self):
        """Reads the GPU memory framebuffer and paints it onto the screen."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
                
        # Read the 32x32 framebuffer from GPU memory
        for y in range(self.height):
            for x in range(self.width):
                addr = self.fb_base_addr + (y * self.width) + x
                val = self.memory.read(addr)
                
                # Use bottom 8 bits for grayscale color
                c = val & 0xFF
                rect = (x * self.scale, y * self.scale, self.scale, self.scale)
                pygame.draw.rect(self.screen, (c, c, c), rect)
                
        pygame.display.flip()
        self.clock.tick(30)


def run_gpu_game():
    print("========================================")
    print(" HeteroGPU Interactive SIMT Demo")
    print("========================================")
    print("Resolution: 32x32 pixels (upscaled)")
    print("Rendering Engine: 4-Core SIMT Array")
    print("Controls: Close window to exit")
    print("----------------------------------------")

    # Allocate 2048 words (Framebuffer is address 0 to 1023)
    mem = Memory(size_words=2048)
    simt = SIMTEngine(num_cores=4)
    monitor = VirtualMonitor(mem, fb_base_addr=0, width=32, height=32, scale=16)

    x_pos = 0
    y_pos = 14
    dx = 1
    dy = 1

    while True:
        # 1. Clear screen using DMA / memory reset
        for i in range(32 * 32):
            mem.write(i, 15)  # Dark gray background

        # 2. Command SIMT Engine to render the 4-pixel paddle/ball
        # Load color 255 (Bright White) into Register 1 across all 4 PEs
        simt.execute({'opcode': 'LOAD', 'rd': 1, 'rs2': 255, 'imm': True}, mem)

        # Store parallel across 4 PEs: writes 4 pixels in a row simultaneously
        base_addr = (y_pos * 32) + x_pos
        simt.execute({'opcode': 'STORE_PARALLEL', 'rs1': 1, 'base_address': base_addr}, mem)

        # Also render a second row using SIMT to make a 4x2 block!
        base_addr_row2 = ((y_pos + 1) * 32) + x_pos
        simt.execute({'opcode': 'STORE_PARALLEL', 'rs1': 1, 'base_address': base_addr_row2}, mem)

        # 3. Virtual Monitor reads the memory and displays it
        monitor.refresh()

        # 4. Physics / Bounce update
        x_pos += dx
        y_pos += dy

        if x_pos <= 0 or x_pos >= (32 - 4):
            dx = -dx
        if y_pos <= 0 or y_pos >= (32 - 2):
            dy = -dy

        time.sleep(0.03)


if __name__ == '__main__':
    run_gpu_game()
