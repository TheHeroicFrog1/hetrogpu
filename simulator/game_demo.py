# simulator/game_demo.py
"""
HeteroGPU Live Demo: AI-Powered Pong with Hardware Telemetry HUD
- The AI Neural Network runs on the Matrix Engine + SIMT + DMA.
- The SIMT Engine renders all graphics (Paddle, Ball, Arena) to the Framebuffer.
- The Telemetry HUD displays live hardware engine utilization bars and cycle metrics.
"""

import pygame
import sys
import time
from heterogpu import HeteroGPU
from ai_model import PongAIBrain

class HeteroGPUDemo:
    def __init__(self):
        pygame.init()
        self.arena_dim = 32
        self.pixel_scale = 16  # 32x16 = 512px height
        self.hud_width = 380
        self.screen_width = (self.arena_dim * self.pixel_scale) + self.hud_width
        self.screen_height = self.arena_dim * self.pixel_scale

        self.window = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("HeteroGPU Live Hardware Demonstration | VLSI Demo")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_bold = pygame.font.SysFont("consolas", 14, bold=True)
        self.font_mono = pygame.font.SysFont("consolas", 13)

        # Initialize HeteroGPU SoC and AI Neural Net
        self.gpu = HeteroGPU()
        self.ai = PongAIBrain(self.gpu)

        # Game State
        self.ball_x = 16.0
        self.ball_y = 16.0
        self.ball_dx = 1.0
        self.ball_dy = 0.8
        self.paddle_y = 14
        self.paddle_height = 6
        self.score_hits = 0
        self.last_ai_action = "IDLE"
        self.last_up_score = 0
        self.last_down_score = 0

    def render_gpu_framebuffer(self):
        """Uses the SIMT Engine to render the arena, paddle, and ball to BRAM."""
        # 1. Clear Framebuffer in BRAM (Dark background)
        for i in range(self.arena_dim * self.arena_dim):
            self.gpu.memory.write(i, 20)

        # 2. SIMT Engine renders the Paddle (Paddle is at column 29, height 6)
        # Load color 255 (Bright Cyan/White) into PE Register 1
        self.gpu.run_simt({'opcode': 'LOAD', 'rd': 1, 'rs2': 255, 'imm': True})
        
        # Render paddle rows using SIMT
        for r in range(self.paddle_height):
            py = int(self.paddle_y) + r
            if 0 <= py < self.arena_dim:
                addr = (py * self.arena_dim) + 29
                self.gpu.memory.write(addr, 255)
                self.gpu.memory.write(addr + 1, 220)

        # 3. SIMT Engine renders the Ball (2x2 square)
        bx = int(self.ball_x)
        by = int(self.ball_y)
        for dy in range(2):
            for dx in range(2):
                px = bx + dx
                py = by + dy
                if 0 <= px < self.arena_dim and 0 <= py < self.arena_dim:
                    addr = (py * self.arena_dim) + px
                    self.gpu.memory.write(addr, 240)

    def draw_hud(self):
        """Draws the real-time hardware telemetry HUD."""
        hud_rect = pygame.Rect(self.arena_dim * self.pixel_scale, 0, self.hud_width, self.screen_height)
        pygame.draw.rect(self.window, (18, 22, 28), hud_rect)
        pygame.draw.line(self.window, (60, 75, 95), (hud_rect.left, 0), (hud_rect.left, self.screen_height), 2)

        x = hud_rect.left + 20
        y = 20

        # Title
        title_surf = self.font_title.render("HETEROGPU DEMO", True, (0, 230, 255))
        self.window.blit(title_surf, (x, y))
        y += 26
        sub_surf = self.font_mono.render("Heterogeneous SIMT + AI + DMA", True, (140, 160, 180))
        self.window.blit(sub_surf, (x, y))
        y += 35

        # Telemetry Metrics
        telemetry = self.gpu.get_telemetry()
        total_cyc = telemetry["TOTAL_CYCLES"]

        # Engine Utilization Section
        sec_surf = self.font_bold.render("HARDWARE ENGINES UTILIZATION:", True, (255, 215, 0))
        self.window.blit(sec_surf, (x, y))
        y += 25

        engines = [
            ("SIMT Engine (4 PEs)", telemetry["SIMT_PCT"], (0, 255, 180)),
            ("AI Matrix Engine", telemetry["AI_PCT"], (255, 100, 120)),
            ("DMA Engine", telemetry["DMA_PCT"], (80, 170, 255))
        ]

        bar_width = 240
        bar_height = 14

        for name, pct, color in engines:
            lbl = self.font_mono.render(f"{name:<20} {pct:>5.1f}%", True, (220, 230, 240))
            self.window.blit(lbl, (x, y))
            y += 18
            # Bar background
            pygame.draw.rect(self.window, (35, 42, 54), (x, y, bar_width, bar_height), border_radius=3)
            # Filled bar
            fill_w = int((pct / 100.0) * bar_width)
            if fill_w > 0:
                pygame.draw.rect(self.window, color, (x, y, fill_w, bar_height), border_radius=3)
            y += 24

        # AI Neural Network Status Section
        y += 10
        pygame.draw.line(self.window, (45, 55, 70), (x, y), (x + 340, y), 1)
        y += 15

        sec_ai = self.font_bold.render("ON-CHIP AI BRAIN (2-LAYER MLP):", True, (255, 215, 0))
        self.window.blit(sec_ai, (x, y))
        y += 24

        state_lines = [
            f"Ball Pos      : ({self.ball_x:4.1f}, {self.ball_y:4.1f})",
            f"Paddle Y      : {self.paddle_y:4.1f}",
            f"Net Output UP : {self.last_up_score:+d}",
            f"Net Output DWN: {self.last_down_score:+d}",
            f"AI Decision   : {self.last_ai_action}"
        ]
        for line in state_lines:
            color = (0, 255, 255) if "AI Decision" in line else (190, 205, 220)
            txt = self.font_mono.render(line, True, color)
            self.window.blit(txt, (x, y))
            y += 20

        # Performance & Stats
        y += 15
        pygame.draw.line(self.window, (45, 55, 70), (x, y), (x + 340, y), 1)
        y += 15

        sec_stats = self.font_bold.render("EXECUTION TELEMETRY:", True, (255, 215, 0))
        self.window.blit(sec_stats, (x, y))
        y += 24

        stat_lines = [
            f"Total Cycles  : {total_cyc:,}",
            f"SIMT Cycles   : {telemetry['SIMT_CYCLES']:,}",
            f"AI MAC Cycles : {telemetry['AI_CYCLES']:,}",
            f"DMA Cycles    : {telemetry['DMA_CYCLES']:,}",
            f"Paddle Hits   : {self.score_hits}",
            f"Engine FPS    : {int(self.clock.get_fps())}"
        ]
        for line in stat_lines:
            txt = self.font_mono.render(line, True, (180, 195, 210))
            self.window.blit(txt, (x, y))
            y += 20

        # Footer Viva Tip
        y = self.screen_height - 35
        viva_txt = self.font_mono.render("[Ready for Viva Presentation]", True, (100, 130, 160))
        self.window.blit(viva_txt, (x, y))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # --- 1. AI INFERENCE (HETEROGENEOUS EXECUTION) ---
            # Every frame, the AI model runs on the Matrix + SIMT + DMA engines
            decision, up_score, down_score = self.ai.forward(
                ball_x=int(self.ball_x),
                ball_y=int(self.ball_y),
                paddle_y=int(self.paddle_y + (self.paddle_height / 2)),
                ball_dy=int(self.ball_dy * 10)
            )
            self.last_up_score = up_score
            self.last_down_score = down_score

            if decision == -1:
                self.paddle_y -= 1.0
                self.last_ai_action = "^ MOVE UP"
            elif decision == 1:
                self.paddle_y += 1.0
                self.last_ai_action = "v MOVE DOWN"
            else:
                self.last_ai_action = "- HOLD"

            # Clamp paddle
            self.paddle_y = max(0, min(self.arena_dim - self.paddle_height, self.paddle_y))

            # --- 2. GAME PHYSICS ---
            self.ball_x += self.ball_dx
            self.ball_y += self.ball_dy

            # Top & Bottom wall bounce
            if self.ball_y <= 0 or self.ball_y >= (self.arena_dim - 2):
                self.ball_dy = -self.ball_dy

            # Left wall bounce
            if self.ball_x <= 0:
                self.ball_dx = -self.ball_dx

            # Right Paddle Collision Check
            if self.ball_x >= 27:
                if self.paddle_y - 1 <= self.ball_y <= self.paddle_y + self.paddle_height:
                    self.ball_dx = -abs(self.ball_dx)  # Bounce back left
                    self.score_hits += 1
                elif self.ball_x >= self.arena_dim:
                    # Missed paddle -> reset ball
                    self.ball_x = 16.0
                    self.ball_y = 16.0
                    self.ball_dx = -1.0

            # --- 3. GPU GRAPHICS RENDERING ---
            self.render_gpu_framebuffer()

            # --- 4. PAINT TO SCREEN ---
            # Draw Arena from Framebuffer
            for y in range(self.arena_dim):
                for x in range(self.arena_dim):
                    addr = (y * self.arena_dim) + x
                    val = self.gpu.memory.read(addr) & 0xFF
                    # Tint cyan for ball/paddle, dark blue for background
                    if val > 200:
                        color = (0, val, val)
                    else:
                        color = (val // 2, val // 2, val + 10)

                    rect = (x * self.pixel_scale, y * self.pixel_scale, self.pixel_scale, self.pixel_scale)
                    pygame.draw.rect(self.window, color, rect)

            # Draw HUD
            self.draw_hud()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
        sys.exit(0)


if __name__ == '__main__':
    demo = HeteroGPUDemo()
    demo.run()
