# Clear, self-explanatory academic evaluation plots for HeteroGPU
# Generates a 2x2 presentation-ready dashboard where each test is explicitly labeled
# Saves to results/heterogpu_evaluation_results.png

import os
import matplotlib.pyplot as plt
import numpy as np

def generate_all_plots():
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    # clean modern styling
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 11,
        'axes.titlesize': 13,
        'axes.labelsize': 11,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.titlesize': 16,
        'figure.dpi': 300
    })

    # 2x2 grid: each test gets its own dedicated, clearly labeled card
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle('HeteroGPU Architecture: Test-by-Test Performance Comparison', fontsize=17, fontweight='bold', y=0.98)

    # common color palette
    c_baseline = '#d9534f'   # Red: Standard SIMT baseline (Slower)
    c_hetero   = '#27ae60'   # Green: HeteroGPU specialized hardware (Faster)
    c_box_bg   = '#f8f9fa'

    # -------------------------------------------------------------------------
    # TEST 1: Matrix Multiplication (GEMM)
    # -------------------------------------------------------------------------
    ax1 = axes[0, 0]
    t1_labels = ['Standard SIMT Cores\n(Sequential loops on 4 PEs)', 'HeteroGPU Matrix Engine\n(2x2 Systolic Array)']
    t1_cycles = [96, 16]

    bars1 = ax1.bar(t1_labels, t1_cycles, color=[c_baseline, c_hetero], width=0.45, edgecolor='black', alpha=0.9)
    ax1.set_ylabel('Execution Time (Clock Cycles)', fontweight='bold')
    ax1.set_title('TEST 1: 4x4 Matrix Multiply (GEMM)\nWhich engine does matrix math faster?', fontweight='bold', pad=10)
    ax1.set_ylim(0, 125)

    # annotate cycle numbers
    for b in bars1:
        h = b.get_height()
        ax1.annotate(f'{h} cycles', xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 4),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', fontsize=12)

    # big speedup callout
    ax1.text(0.5, 0.72, '6.0x FASTER\nwith Matrix Engine', transform=ax1.transAxes,
             ha='center', va='center', fontsize=13, fontweight='bold', color='#1e7e34',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#e8f5e9', edgecolor='#27ae60', linewidth=1.5))

    # plain-English takeaway box
    ax1.text(0.5, 0.08, 'Takeaway: The 2x2 Systolic Array finishes in 16 cycles vs 96 cycles,\nbecause all 4 MAC units compute simultaneously without loop overhead.',
             transform=ax1.transAxes, ha='center', va='bottom', fontsize=9.5, style='italic',
             bbox=dict(boxstyle='square,pad=0.4', facecolor=c_box_bg, edgecolor='#ccc'))

    # -------------------------------------------------------------------------
    # TEST 2: Block Memory Transfer (DMA vs Core Copy)
    # -------------------------------------------------------------------------
    ax2 = axes[0, 1]
    t2_labels = ['Manual SIMT Copy\n(PEs stalled doing load/store)', 'Hardware DMA Engine\n(Dedicated burst controller)']
    t2_cycles = [80, 65]

    bars2 = ax2.bar(t2_labels, t2_cycles, color=[c_baseline, c_hetero], width=0.45, edgecolor='black', alpha=0.9)
    ax2.set_ylabel('Execution Time (Clock Cycles)', fontweight='bold')
    ax2.set_title('TEST 2: 64-Word Memory Block Copy\nCan we move data without stalling compute cores?', fontweight='bold', pad=10)
    ax2.set_ylim(0, 110)

    for b in bars2:
        h = b.get_height()
        ax2.annotate(f'{h} cycles', xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 4),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax2.text(0.5, 0.72, '1.23x FASTER\n+ 100% Cores Free!', transform=ax2.transAxes,
             ha='center', va='center', fontsize=13, fontweight='bold', color='#1e7e34',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#e8f5e9', edgecolor='#27ae60', linewidth=1.5))

    ax2.text(0.5, 0.08, 'Takeaway: DMA finishes faster and completely frees the 4 SIMT cores\nto continue doing graphics/game physics instead of moving memory.',
             transform=ax2.transAxes, ha='center', va='bottom', fontsize=9.5, style='italic',
             bbox=dict(boxstyle='square,pad=0.4', facecolor=c_box_bg, edgecolor='#ccc'))

    # -------------------------------------------------------------------------
    # TEST 3: End-to-End AI Forward Pass
    # -------------------------------------------------------------------------
    ax3 = axes[1, 0]
    t3_labels = ['Homogeneous SIMT Mode\n(All math forced onto SIMT)', 'HeteroGPU Mode\n(Matrix Engine + SIMT + DMA)']
    t3_cycles = [110, 34]

    bars3 = ax3.bar(t3_labels, t3_cycles, color=[c_baseline, c_hetero], width=0.45, edgecolor='black', alpha=0.9)
    ax3.set_ylabel('Inference Latency (Clock Cycles)', fontweight='bold')
    ax3.set_title('TEST 3: Full Neural Network Inference Pass\n(2-Layer MLP: 4 Inputs -> 4 Hidden -> 2 Actions)', fontweight='bold', pad=10)
    ax3.set_ylim(0, 140)

    for b in bars3:
        h = b.get_height()
        ax3.annotate(f'{h} cycles', xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 4),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax3.text(0.5, 0.72, '3.24x OVERALL SPEEDUP\n(Smooth 60+ FPS)', transform=ax3.transAxes,
             ha='center', va='center', fontsize=13, fontweight='bold', color='#1e7e34',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#e8f5e9', edgecolor='#27ae60', linewidth=1.5))

    ax3.text(0.5, 0.08, 'Takeaway: By offloading dense matrix layers to the Matrix Engine and\nparallel ReLU to SIMT, decision latency drops from 110 to 34 cycles.',
             transform=ax3.transAxes, ha='center', va='bottom', fontsize=9.5, style='italic',
             bbox=dict(boxstyle='square,pad=0.4', facecolor=c_box_bg, edgecolor='#ccc'))

    # -------------------------------------------------------------------------
    # TEST 4: Where Do the 34 Cycles Go? (Hardware Workload Breakdown)
    # -------------------------------------------------------------------------
    ax4 = axes[1, 1]
    engine_names = [
        'Matrix Engine (GEMM)\n24 cycles',
        'SIMT Cores (ReLU)\n5 cycles',
        'DMA Engine (I/O)\n5 cycles'
    ]
    cycles_spent = [24, 5, 5]
    pie_colors = ['#e74c3c', '#2ecc71', '#3498db']

    wedges, texts, autotexts = ax4.pie(
        cycles_spent, labels=engine_names, autopct='%1.1f%%',
        startangle=140, colors=pie_colors,
        wedgeprops=dict(width=0.45, edgecolor='black', linewidth=1.2),
        pctdistance=0.75, textprops={'fontsize': 10}
    )
    for at in autotexts:
        at.set_fontweight('bold')
        at.set_color('white')

    ax4.set_title('TEST 4: Workload Breakdown in 34 Cycles\nWhich specialized hardware does what?', fontweight='bold', pad=10)

    ax4.text(0.5, -0.02, 'Takeaway: 70.6% of time is matrix math (handled by Matrix Engine),\n14.7% is parallel non-linear ReLU (SIMT), and 14.7% is sensor I/O (DMA).',
             transform=ax4.transAxes, ha='center', va='bottom', fontsize=9.5, style='italic',
             bbox=dict(boxstyle='square,pad=0.4', facecolor=c_box_bg, edgecolor='#ccc'))

    plt.tight_layout()

    out_path = os.path.join(results_dir, 'heterogpu_evaluation_results.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Generated clean test-by-test comparison chart at:\n  -> {out_path}")
    return out_path

if __name__ == '__main__':
    generate_all_plots()
