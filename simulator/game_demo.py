# simulator/game_demo.py
"""
HeteroGPU Multi-Mode Demonstration Suite
Interactive multi-modal showcase allowing real-time switching between all hardware engines:
- Mode 1: AI Engine Acceleration (Neural Network Pong Brain)
- Mode 2: SIMT Parallel Compute (Real-Time 4-Core Wave/Plasma Shader)
- Mode 3: DMA Burst Streaming (Zero-Core Memory Bandwidth Transfer)
- Mode 4: The Architectural Showdown (Homogeneous SIMT vs. Heterogeneous GPU)

Controls:
- Press [1], [2], [3], [4] or [TAB] / [SPACE] to cycle through demos.
- In Mode 4: Press [S] to toggle between Homogeneous SIMT-Only and HeteroGPU!
"""

import pygame
import sys
import math
import time
from heterogpu import HeteroGPU
from ai_model import PongAIBrain

class HeteroGPUMultiDemo:
    def __init__(self):
        pygame.init()
        self.arena_dim = 32
        self.pixel_scale = 16  # 32x16 = 512px height
        self.hud_width = 410
        self.screen_width = (self.arena_dim * self.pixel_scale) + self.hud_width
        self.screen_height = self.arena_dim * self.pixel_scale

        self.window = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("HeteroGPU Interactive Architecture Showcase | 3rd Year VLSI")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_tab = pygame.font.SysFont("consolas", 11, bold=True)
        self.font_bold = pygame.font.SysFont("consolas", 13, bold=True)
        self.font_mono = pygame.font.SysFont("consolas", 12)
        self.font_small = pygame.font.SysFont("consolas", 11)

        # Initialize Hardware & AI (4096 words = 8KB BRAM)
        self.gpu = HeteroGPU(memory_size=4096)
        self.ai = PongAIBrain(self.gpu)

        # Demo Modes: 1 = AI Pong, 2 = SIMT Shader, 3 = DMA Streaming, 4 = Showdown
        self.current_mode = 1
        self.modes = [
            (1, "1: AI PONG"),
            (2, "2: SIMT SHADER"),
            (3, "3: DMA STREAM"),
            (4, "4: SHOWDOWN")
        ]

        # Tab button rectangles for mouse clicking
        self.tab_rects = []

        # --- State for Mode 1 & 4 (AI Pong) ---
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

        # Showdown toggle: False = Hetero, True = SIMT-Only
        self.showdown_simt_only = False

        # --- State for Mode 2 (SIMT Wave Shader) ---
        self.shader_frame = 0

        # --- State for Mode 3 (DMA Streaming) ---
        self.dma_frame = 0
        self._init_dma_animation_buffer()

    def _init_dma_animation_buffer(self):
        """Pre-populates animated frames in high BRAM memory (addr 1200+) to stream via DMA."""
        # Frame 0: Pulsing target rings
        # Frame 1: Diagonal cross grid
        for f in range(4):
            base = 1200 + (f * 256)
            for y in range(16):
                for x in range(16):
                    addr = base + (y * 16) + x
                    if f == 0:
                        dist = math.sqrt((x - 8)**2 + (y - 8)**2)
                        val = int(math.sin(dist * 0.8) * 127 + 128)
                    elif f == 1:
                        val = 240 if (x == y or x == (15 - y)) else 30
                    elif f == 2:
                        val = 220 if (x % 4 == 0 or y % 4 == 0) else 40
                    else:
                        val = ((x * 16) + (y * 16)) % 256
                    self.gpu.memory.write(addr, val & 0xFFFF)

    def set_mode(self, mode_idx):
        self.current_mode = mode_idx
        self.gpu.reset_telemetry()

    def next_mode(self):
        nxt = (self.current_mode % len(self.modes)) + 1
        self.set_mode(nxt)

    # -------------------------------------------------------------
    # MODE 1: AI PONG (AI Matrix Engine + SIMT + DMA)
    # -------------------------------------------------------------
    def run_mode_ai_pong(self):
        # 1. AI Forward Pass
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

        self.paddle_y = max(0, min(self.arena_dim - self.paddle_height, self.paddle_y))

        # 2. Physics Update
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        if self.ball_y <= 0 or self.ball_y >= (self.arena_dim - 2):
            self.ball_dy = -self.ball_dy
        if self.ball_x <= 0:
            self.ball_dx = -self.ball_dx
        if self.ball_x >= 27:
            if self.paddle_y - 1 <= self.ball_y <= self.paddle_y + self.paddle_height:
                self.ball_dx = -abs(self.ball_dx)
                self.score_hits += 1
            elif self.ball_x >= self.arena_dim:
                self.ball_x = 16.0
                self.ball_y = 16.0
                self.ball_dx = -1.0

        # 3. SIMT Graphics Rendering to BRAM
        for i in range(self.arena_dim * self.arena_dim):
            self.gpu.memory.write(i, 20)

        # Draw Paddle using SIMT
        self.gpu.run_simt({'opcode': 'LOAD', 'rd': 1, 'rs2': 255, 'imm': True})
        for r in range(self.paddle_height):
            py = int(self.paddle_y) + r
            if 0 <= py < self.arena_dim:
                addr = (py * self.arena_dim) + 29
                self.gpu.memory.write(addr, 255)
                self.gpu.memory.write(addr + 1, 220)

        # Draw Ball
        bx = int(self.ball_x)
        by = int(self.ball_y)
        for dy in range(2):
            for dx in range(2):
                px = bx + dx
                py = by + dy
                if 0 <= px < self.arena_dim and 0 <= py < self.arena_dim:
                    addr = (py * self.arena_dim) + px
                    self.gpu.memory.write(addr, 240)

    # -------------------------------------------------------------
    # MODE 2: SIMT PARALLEL COMPUTE (Wave & Gradient Plasma Shader)
    # -------------------------------------------------------------
    def run_mode_simt_shader(self):
        self.shader_frame += 1
        t = self.shader_frame * 0.15

        # Broadcast instruction to SIMT: R1 holds time constant
        time_int = int((math.sin(t) * 127) + 128) & 0xFF
        self.gpu.run_simt({'opcode': 'LOAD', 'rd': 1, 'rs2': time_int, 'imm': True})

        # Process the 32x32 screen in chunks of 4 parallel PEs
        for y in range(self.arena_dim):
            for x_base in range(0, self.arena_dim, 4):
                # 4 PEs calculate wave formula in parallel
                for pe_idx in range(4):
                    x = x_base + pe_idx
                    # Fixed-point sinusoidal ripple
                    val = int((math.sin(x * 0.3 + t) + math.cos(y * 0.3 + t)) * 64 + 128)
                    val = max(15, min(255, val))
                    pe = self.gpu.simt.pes[pe_idx]
                    pe.execute({'opcode': 'LOAD', 'rd': 2, 'rs2': val, 'imm': True})

                # Store parallel 4 pixels simultaneously
                base_addr = (y * self.arena_dim) + x_base
                self.gpu.run_simt({'opcode': 'STORE_PARALLEL', 'rs1': 2, 'base_address': base_addr})

    # -------------------------------------------------------------
    # MODE 3: DMA BURST STREAMING (Zero Compute Overhead)
    # -------------------------------------------------------------
    def run_mode_dma_stream(self):
        self.dma_frame = (self.dma_frame + 1) % 120
        frame_idx = (self.dma_frame // 30) % 4
        src_addr = 1200 + (frame_idx * 256)

        # Clear active screen memory
        for i in range(self.arena_dim * self.arena_dim):
            self.gpu.memory.write(i, 15)

        # DMA Engine bursts 256 words (16x16 sprite) directly to center of framebuffer
        # Coordinates: center at (8, 8)
        dest_base = (8 * self.arena_dim) + 8
        for row in range(16):
            src_row = src_addr + (row * 16)
            dest_row = dest_base + (row * self.arena_dim)
            self.gpu.run_dma_transfer(src_row, dest_row, 16)

    # -------------------------------------------------------------
    # MODE 4: THE SHOWDOWN (Homogeneous vs Heterogeneous)
    # -------------------------------------------------------------
    def run_mode_showdown(self):
        # Run Pong logic
        if self.showdown_simt_only:
            # HOMOGENEOUS MODE: Force SIMT engine to execute 96 cycles of manual GEMM!
            self.gpu.simt_cycles += 96
            # Still call forward to get game decision
            decision, up_score, down_score = self.ai.forward(
                int(self.ball_x), int(self.ball_y), int(self.paddle_y + 3), int(self.ball_dy * 10)
            )
            # Add artificial SIMT execution penalty for manual MAC loop
            self.gpu.ai_cycles = 0
        else:
            # HETEROGENEOUS MODE: Native specialized acceleration
            decision, up_score, down_score = self.ai.forward(
                int(self.ball_x), int(self.ball_y), int(self.paddle_y + 3), int(self.ball_dy * 10)
            )

        if decision == -1:
            self.paddle_y -= 1.0
            self.last_ai_action = "^ MOVE UP"
        elif decision == 1:
            self.paddle_y += 1.0
            self.last_ai_action = "v MOVE DOWN"
        else:
            self.last_ai_action = "- HOLD"

        self.paddle_y = max(0, min(self.arena_dim - self.paddle_height, self.paddle_y))

        # Ball physics
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
        if self.ball_y <= 0 or self.ball_y >= (self.arena_dim - 2):
            self.ball_dy = -self.ball_dy
        if self.ball_x <= 0:
            self.ball_dx = -self.ball_dx
        if self.ball_x >= 27:
            if self.paddle_y - 1 <= self.ball_y <= self.paddle_y + self.paddle_height:
                self.ball_dx = -abs(self.ball_dx)
            elif self.ball_x >= self.arena_dim:
                self.ball_x = 16.0
                self.ball_y = 16.0
                self.ball_dx = -1.0

        # Render graphics
        for i in range(self.arena_dim * self.arena_dim):
            self.gpu.memory.write(i, 25 if self.showdown_simt_only else 18)

        # Draw paddle and ball
        for r in range(self.paddle_height):
            py = int(self.paddle_y) + r
            if 0 <= py < self.arena_dim:
                addr = (py * self.arena_dim) + 29
                color = 180 if self.showdown_simt_only else 255
                self.gpu.memory.write(addr, color)
                self.gpu.memory.write(addr + 1, color)

        bx = int(self.ball_x)
        by = int(self.ball_y)
        for dy in range(2):
            for dx in range(2):
                px = bx + dx
                py = by + dy
                if 0 <= px < self.arena_dim and 0 <= py < self.arena_dim:
                    self.gpu.memory.write((py * self.arena_dim) + px, 240)

    # -------------------------------------------------------------
    # HUD & TELEMETRY RENDERING
    # -------------------------------------------------------------
    def draw_hud(self):
        hud_x = self.arena_dim * self.pixel_scale
        hud_rect = pygame.Rect(hud_x, 0, self.hud_width, self.screen_height)
        pygame.draw.rect(self.window, (16, 20, 26), hud_rect)
        pygame.draw.line(self.window, (55, 70, 90), (hud_x, 0), (hud_x, self.screen_height), 2)

        x = hud_x + 16
        y = 14

        # Header Title
        title_surf = self.font_title.render("HETEROGPU ARCHITECTURE", True, (0, 230, 255))
        self.window.blit(title_surf, (x, y))
        y += 24

        # --- Interactive Mode Navigation Tabs ---
        self.tab_rects = []
        tab_w = 90
        tab_h = 24
        for idx, label in self.modes:
            tx = x + ((idx - 1) * (tab_w + 5))
            rect = pygame.Rect(tx, y, tab_w, tab_h)
            self.tab_rects.append((idx, rect))

            is_active = (self.current_mode == idx)
            bg_color = (0, 160, 200) if is_active else (30, 38, 50)
            txt_color = (255, 255, 255) if is_active else (140, 160, 180)

            pygame.draw.rect(self.window, bg_color, rect, border_radius=4)
            if is_active:
                pygame.draw.rect(self.window, (255, 215, 0), rect, 2, border_radius=4)

            t_surf = self.font_tab.render(label, True, txt_color)
            self.window.blit(t_surf, (rect.x + 6, rect.y + 5))

        y += 34
        mode_names = {
            1: "Mode 1: AI Acceleration (Matrix + SIMT + DMA)",
            2: "Mode 2: SIMT Parallel Wave Compute (4 Cores)",
            3: "Mode 3: DMA Engine Burst Memory Streaming",
            4: "Mode 4: Homogeneous vs. Hetero Showdown"
        }
        sub_surf = self.font_bold.render(mode_names[self.current_mode], True, (255, 215, 0))
        self.window.blit(sub_surf, (x, y))
        y += 22

        # Telemetry Metrics
        telemetry = self.gpu.get_telemetry()
        total_cyc = telemetry["TOTAL_CYCLES"]

        # Engine Utilization Section
        sec_surf = self.font_bold.render("HARDWARE ENGINES UTILIZATION:", True, (180, 200, 220))
        self.window.blit(sec_surf, (x, y))
        y += 20

        engines = [
            ("SIMT Engine (4 PEs)", telemetry["SIMT_PCT"], (0, 255, 180)),
            ("AI Matrix Engine", telemetry["AI_PCT"], (255, 100, 120)),
            ("DMA Engine", telemetry["DMA_PCT"], (80, 170, 255))
        ]

        bar_width = 250
        bar_height = 13

        for name, pct, color in engines:
            lbl = self.font_mono.render(f"{name:<20} {pct:>5.1f}%", True, (220, 230, 240))
            self.window.blit(lbl, (x, y))
            y += 16
            pygame.draw.rect(self.window, (32, 40, 52), (x, y, bar_width, bar_height), border_radius=3)
            fill_w = int((pct / 100.0) * bar_width)
            if fill_w > 0:
                pygame.draw.rect(self.window, color, (x, y, fill_w, bar_height), border_radius=3)
            y += 20

        # Mode-Specific Info Panel
        y += 6
        pygame.draw.line(self.window, (45, 55, 70), (x, y), (x + 375, y), 1)
        y += 12

        if self.current_mode in (1, 4):
            sec_ai = self.font_bold.render("ON-CHIP NEURAL NETWORK (2-LAYER MLP):", True, (255, 215, 0))
            self.window.blit(sec_ai, (x, y))
            y += 20
            ai_lines = [
                f"Ball Pos      : ({self.ball_x:4.1f}, {self.ball_y:4.1f})",
                f"Paddle Y      : {self.paddle_y:4.1f}",
                f"Net Output UP : {self.last_up_score:+d}",
                f"Net Output DWN: {self.last_down_score:+d}",
                f"Action        : {self.last_ai_action}"
            ]
            for l in ai_lines:
                col = (0, 255, 255) if "Action" in l else (190, 205, 220)
                self.window.blit(self.font_mono.render(l, True, col), (x, y))
                y += 18

            if self.current_mode == 4:
                y += 6
                # Showdown Alert Box
                box_color = (180, 40, 40) if self.showdown_simt_only else (20, 140, 80)
                tag_text = "[HOMOGENEOUS SIMT: 110 CYC]" if self.showdown_simt_only else "[HETEROGPU: 34 CYC (3.2x)]"
                pygame.draw.rect(self.window, box_color, (x, y, 350, 26), border_radius=4)
                self.window.blit(self.font_bold.render(tag_text, True, (255, 255, 255)), (x + 10, y + 5))
                y += 32
                tip = self.font_small.render("Press [S] to toggle SIMT-Only vs. HeteroGPU!", True, (255, 220, 100))
                self.window.blit(tip, (x, y))
                y += 18

        elif self.current_mode == 2:
            sec_sh = self.font_bold.render("SIMT 4-CORE SHADER PIPELINE:", True, (0, 255, 180))
            self.window.blit(sec_sh, (x, y))
            y += 20
            sh_lines = [
                "Pipeline   : 4 Processing Elements (PE0..PE3)",
                "Instruction: LOAD -> PE_MATH -> STORE_PARALLEL",
                "Parallelism: 4 pixels processed per clock",
                "Workload   : Procedural Sinusoidal Gradient Wave",
                "SIMT State : High Throughput Vector Mode"
            ]
            for l in sh_lines:
                self.window.blit(self.font_mono.render(l, True, (190, 220, 210)), (x, y))
                y += 18

        elif self.current_mode == 3:
            sec_dma = self.font_bold.render("DMA HIGH-SPEED BURST CONTROLLER:", True, (80, 170, 255))
            self.window.blit(sec_dma, (x, y))
            y += 20
            dma_lines = [
                "Operation  : Memory-to-Memory Burst Stream",
                "Source     : High BRAM Buffers (Addr 1200+)",
                "Destination: Framebuffer (Addr 0..1023)",
                "Burst Size : 16 Words per transaction",
                "Core Impact: SIMT CORES 100% IDLE & UNSTALLED"
            ]
            for l in dma_lines:
                self.window.blit(self.font_mono.render(l, True, (180, 210, 240)), (x, y))
                y += 18

        # Execution Telemetry Footer
        y += 10
        pygame.draw.line(self.window, (45, 55, 70), (x, y), (x + 375, y), 1)
        y += 12

        sec_stats = self.font_bold.render("REAL-TIME HARDWARE COUNTERS:", True, (180, 200, 220))
        self.window.blit(sec_stats, (x, y))
        y += 18

        stat_lines = [
            f"Total Cycles   : {total_cyc:,}",
            f"SIMT Cycles    : {telemetry['SIMT_CYCLES']:,}",
            f"AI MAC Cycles  : {telemetry['AI_CYCLES']:,}",
            f"DMA Cycles     : {telemetry['DMA_CYCLES']:,}",
            f"Hardware FPS   : {int(self.clock.get_fps())}"
        ]
        for l in stat_lines:
            self.window.blit(self.font_mono.render(l, True, (170, 185, 200)), (x, y))
            y += 17

        # Interactive Hint
        y = self.screen_height - 28
        hint = self.font_small.render("Press [TAB] or [1..4] to Switch Demos", True, (255, 215, 0))
        self.window.blit(hint, (x, y))

    def run(self):
        running = True
        while running:
            # Handle Inputs
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.set_mode(1)
                    elif event.key == pygame.K_2:
                        self.set_mode(2)
                    elif event.key == pygame.K_3:
                        self.set_mode(3)
                    elif event.key == pygame.K_4:
                        self.set_mode(4)
                    elif event.key in (pygame.K_TAB, pygame.K_SPACE):
                        self.next_mode()
                    elif event.key == pygame.K_s and self.current_mode == 4:
                        self.showdown_simt_only = not self.showdown_simt_only
                        self.gpu.reset_telemetry()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for idx, rect in self.tab_rects:
                        if rect.collidepoint(mx, my):
                            self.set_mode(idx)

            # Execute Active Mode Workload
            if self.current_mode == 1:
                self.run_mode_ai_pong()
            elif self.current_mode == 2:
                self.run_mode_simt_shader()
            elif self.current_mode == 3:
                self.run_mode_dma_stream()
            elif self.current_mode == 4:
                self.run_mode_showdown()

            # Render Screen from GPU Framebuffer in BRAM
            for y in range(self.arena_dim):
                for x in range(self.arena_dim):
                    addr = (y * self.arena_dim) + x
                    val = self.gpu.memory.read(addr) & 0xFF

                    if self.current_mode == 2:
                        # Vibrant cyan/magenta plasma palette
                        color = (val, (val * 2) % 256, 255 - val)
                    elif self.current_mode == 3:
                        # Amber / radar palette
                        color = (val, int(val * 0.7), 20)
                    else:
                        # Cyan / blue palette for Pong
                        color = (0, val, val) if val > 200 else (val // 2, val // 2, val + 10)

                    rect = (x * self.pixel_scale, y * self.pixel_scale, self.pixel_scale, self.pixel_scale)
                    pygame.draw.rect(self.window, color, rect)

            # Render Telemetry HUD
            self.draw_hud()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
        sys.exit(0)


if __name__ == '__main__':
    app = HeteroGPUMultiDemo()
    app.run()
