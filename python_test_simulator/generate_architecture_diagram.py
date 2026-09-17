import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_architecture_diagram(output_path="python_test_simulator/results/heterogpu_architecture_diagram.png"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=300)
    fig.patch.set_facecolor("#0F172A")

    for ax in (ax1, ax2):
        ax.set_facecolor("#0F172A")
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")

    # ==========================================
    # Panel 1: Traditional Homogeneous SIMT GPU
    # ==========================================
    ax1.text(5, 9.4, "Traditional Homogeneous GPU", fontsize=15, fontweight="bold", color="#F8FAFC", ha="center")
    ax1.text(5, 8.9, "(Unified, Unspecialized Execution)", fontsize=10, color="#94A3B8", ha="center")

    # CPU Host
    p_cpu = patches.FancyBboxPatch((1.5, 7.6), 7, 0.9, boxstyle="round,pad=0.2", ec="#475569", fc="#1E293B", lw=1.5)
    ax1.add_patch(p_cpu)
    ax1.text(5, 8.05, "Host CPU / Software Driver", fontsize=11, fontweight="bold", color="#E2E8F0", ha="center")

    # Memory
    p_mem1 = patches.FancyBboxPatch((1.5, 1.0), 7, 1.0, boxstyle="round,pad=0.2", ec="#475569", fc="#1E293B", lw=1.5)
    ax1.add_patch(p_mem1)
    ax1.text(5, 1.5, "Unified Global / Video Memory (VRAM)", fontsize=11, fontweight="bold", color="#E2E8F0", ha="center")

    # Unified SIMT Cores (All doing everything)
    p_simt1 = patches.FancyBboxPatch((1.5, 2.7), 7, 4.2, boxstyle="round,pad=0.2", ec="#EF4444", fc="#1E1B4B", lw=2)
    ax1.add_patch(p_simt1)
    ax1.text(5, 6.4, "Homogeneous SIMT Core Array", fontsize=12, fontweight="bold", color="#F87171", ha="center")

    for i in range(4):
        x = 2.0 + i * 1.6
        p_core = patches.FancyBboxPatch((x, 3.2), 1.2, 2.7, boxstyle="round,pad=0.1", ec="#DC2626", fc="#2D122D", lw=1)
        ax1.add_patch(p_core)
        ax1.text(x + 0.6, 5.4, f"Core {i}", fontsize=10, fontweight="bold", color="#FCA5A5", ha="center")
        ax1.text(x + 0.6, 4.7, "ALU", fontsize=9, color="#CBD5E1", ha="center")
        ax1.text(x + 0.6, 4.1, "GEMM", fontsize=8, color="#F87171", ha="center")
        ax1.text(x + 0.6, 3.6, "Copy", fontsize=8, color="#F87171", ha="center")

    # Bottlenecks text
    ax1.text(5, 0.4, "Bottlenecks: Matrix GEMM causes register spills & stalls;\nBulk memory copying halts shader compute cores.",
             fontsize=9.5, color="#F87171", ha="center", style="italic")

    # Arrows
    ax1.annotate("", xy=(5, 7.4), xytext=(5, 7.0), arrowprops=dict(arrowstyle="->", color="#94A3B8", lw=1.8))
    ax1.annotate("", xy=(5, 2.6), xytext=(5, 2.1), arrowprops=dict(arrowstyle="<->", color="#EF4444", lw=1.8))

    # ==========================================
    # Panel 2: Proposed HeteroGPU Architecture
    # ==========================================
    ax2.text(5, 9.4, "Proposed HeteroGPU Architecture", fontsize=15, fontweight="bold", color="#38BDF8", ha="center")
    ax2.text(5, 8.9, "(Workload-Specialized Heterogeneous Cores)", fontsize=10, color="#94A3B8", ha="center")

    # Top Controller & Arbiter
    p_top = patches.FancyBboxPatch((1.0, 7.4), 8, 1.1, boxstyle="round,pad=0.2", ec="#38BDF8", fc="#0B2A4A", lw=2)
    ax2.add_patch(p_top)
    ax2.text(5, 8.1, "HeteroGPU Top Controller & Memory Arbiter", fontsize=11, fontweight="bold", color="#BAE6FD", ha="center")
    ax2.text(5, 7.6, "Hardware Cycle Telemetry Unit (SIMT / AI / DMA / Total)", fontsize=9, color="#7DD3FC", ha="center")

    # 3 Specialized Engines
    # 1. 4-Core SIMT
    p_simt2 = patches.FancyBboxPatch((0.8, 3.2), 2.6, 3.4, boxstyle="round,pad=0.15", ec="#A855F7", fc="#1E1035", lw=1.8)
    ax2.add_patch(p_simt2)
    ax2.text(2.1, 6.2, "4-Core SIMT", fontsize=10.5, fontweight="bold", color="#D8B4FE", ha="center")
    ax2.text(2.1, 5.7, "Vector Shaders", fontsize=8.5, color="#C084FC", ha="center")
    ax2.text(2.1, 4.8, "4x PE Cores\n8 GPRs / Core\nHW ReLU Clamp", fontsize=8, color="#E9D5FF", ha="center")
    ax2.text(2.1, 3.6, "95% Shader Util", fontsize=8, fontweight="bold", color="#A855F7", ha="center")

    # 2. 2x2 Systolic Array (AI Tensor Core)
    p_ai = patches.FancyBboxPatch((3.7, 3.2), 2.6, 3.4, boxstyle="round,pad=0.15", ec="#22C55E", fc="#052E16", lw=1.8)
    ax2.add_patch(p_ai)
    ax2.text(5.0, 6.2, "2x2 Systolic Array", fontsize=10.5, fontweight="bold", color="#86EFAC", ha="center")
    ax2.text(5.0, 5.7, "AI / Tensor Core", fontsize=8.5, color="#4ADE80", ha="center")
    ax2.text(5.0, 4.8, "4x DSP MACs\n2D Dataflow\n4-Cycle GEMM", fontsize=8, color="#DCFCE7", ha="center")
    ax2.text(5.0, 3.6, "5.75x Speedup", fontsize=8.5, fontweight="bold", color="#22C55E", ha="center")

    # 3. DMA Burst Engine
    p_dma = patches.FancyBboxPatch((6.6, 3.2), 2.6, 3.4, boxstyle="round,pad=0.15", ec="#EAB308", fc="#2E2105", lw=1.8)
    ax2.add_patch(p_dma)
    ax2.text(7.9, 6.2, "DMA Burst Engine", fontsize=10.5, fontweight="bold", color="#FDE047", ha="center")
    ax2.text(7.9, 5.7, "Data Movement", fontsize=8.5, color="#FACC15", ha="center")
    ax2.text(7.9, 4.8, "Burst Controller\n1+N Clock Cycles\nZero Core Stalls", fontsize=8, color="#FEF08A", ha="center")
    ax2.text(7.9, 3.6, "100% Cores Free", fontsize=8.5, fontweight="bold", color="#EAB308", ha="center")

    # Dual Port Block RAM (BRAM)
    p_bram = patches.FancyBboxPatch((1.0, 1.0), 8, 1.3, boxstyle="round,pad=0.2", ec="#38BDF8", fc="#0B2A4A", lw=2)
    ax2.add_patch(p_bram)
    ax2.text(5, 1.8, "8 KB Dual-Port Synchronous Block RAM (BRAM)", fontsize=11, fontweight="bold", color="#BAE6FD", ha="center")
    ax2.text(5, 1.3, "Port A: Host / SIMT Vector Access  |  Port B: AI Weights & DMA Stream", fontsize=8.5, color="#7DD3FC", ha="center")

    # Interconnect Lines
    ax2.annotate("", xy=(2.1, 6.7), xytext=(2.1, 7.3), arrowprops=dict(arrowstyle="<->", color="#A855F7", lw=1.5))
    ax2.annotate("", xy=(5.0, 6.7), xytext=(5.0, 7.3), arrowprops=dict(arrowstyle="<->", color="#22C55E", lw=1.5))
    ax2.annotate("", xy=(7.9, 6.7), xytext=(7.9, 7.3), arrowprops=dict(arrowstyle="<->", color="#EAB308", lw=1.5))

    ax2.annotate("", xy=(2.1, 2.4), xytext=(2.1, 3.1), arrowprops=dict(arrowstyle="<->", color="#A855F7", lw=1.5))
    ax2.annotate("", xy=(5.0, 2.4), xytext=(5.0, 3.1), arrowprops=dict(arrowstyle="<->", color="#22C55E", lw=1.5))
    ax2.annotate("", xy=(7.9, 2.4), xytext=(7.9, 3.1), arrowprops=dict(arrowstyle="<->", color="#EAB308", lw=1.5))

    ax2.text(5, 0.4, "Advantages: Workloads mapped to specialized hardware engines;\nZero CPU stalls, 5.75x faster AI matrix math, 27 MHz FPGA ready.",
             fontsize=9.5, color="#38BDF8", ha="center", style="italic")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"Architecture diagram saved to {output_path}")

if __name__ == "__main__":
    generate_architecture_diagram()
