# Plotting script to generate benchmark graphs using matplotlib
# Saves high-res figure to results/heterogpu_evaluation_results.png

import os
import matplotlib.pyplot as plt
import numpy as np

def generate_all_plots():
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    # clean plot styling
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'figure.titlesize': 15,
        'figure.dpi': 300
    })

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    fig.suptitle('HeteroGPU Architecture: Evaluation & Benchmark Results', fontsize=16, fontweight='bold', y=0.98)

    # plot 1: latency comparison (simt vs hetero)
    ax1 = axes[0]
    categories = ['4x4 GEMM\n(Matrix Multiply)', '64-Word\nMemory Copy', 'AI Forward Pass\n(2-Layer MLP)']
    simt_baseline = [96, 80, 110]
    hetero_gpu = [16, 65, 34]

    x = np.arange(len(categories))
    bar_width = 0.35

    rects1 = ax1.bar(x - bar_width/2, simt_baseline, bar_width, label='Homogeneous SIMT', color='#e74c3c', edgecolor='black', alpha=0.9)
    rects2 = ax1.bar(x + bar_width/2, hetero_gpu, bar_width, label='HeteroGPU (Specialized)', color='#2ecc71', edgecolor='black', alpha=0.9)

    ax1.set_ylabel('Execution Latency (Clock Cycles)', fontweight='bold')
    ax1.set_title('(A) Execution Latency (Lower is Better)', fontweight='bold', pad=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend(loc='upper right', frameon=True)
    ax1.set_ylim(0, 130)

    for r in rects1:
        h = r.get_height()
        ax1.annotate(f'{h}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#c0392b')
    for r in rects2:
        h = r.get_height()
        ax1.annotate(f'{h}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontweight='bold', color='#27ae60')

    # plot 2: speedup factors
    ax2 = axes[1]
    speedup_labels = ['4x4 GEMM\n(Matrix Engine)', 'Memory Transfer\n(DMA Engine)', 'Complete AI Pass\n(Hetero SoC)']
    speedups = [96 / 16, 80 / 65, 110 / 34]
    colors = ['#3498db', '#f39c12', '#9b59b6']

    bars = ax2.bar(speedup_labels, speedups, color=colors, width=0.5, edgecolor='black', alpha=0.9)
    ax2.axhline(1.0, color='gray', linestyle='--', linewidth=1.5, label='1.0x Baseline')
    ax2.set_ylabel('Speedup Factor vs. SIMT Baseline', fontweight='bold')
    ax2.set_title('(B) Hardware Speedup Factor (Higher is Better)', fontweight='bold', pad=12)
    ax2.set_ylim(0, 7.5)
    ax2.legend(loc='upper right', frameon=True)

    for bar in bars:
        h = bar.get_height()
        ax2.annotate(f'{h:.2f}x', xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0, 4),
                     textcoords="offset points", ha='center', va='bottom', fontsize=12, fontweight='bold')

    # plot 3: cycle breakdown for AI forward pass
    ax3 = axes[2]
    engine_labels = ['AI Matrix Engine (GEMM)\n24 cyc (70.6%)',
                     'SIMT Engine (ReLU)\n5 cyc (14.7%)',
                     'DMA Engine (I/O)\n5 cyc (14.7%)']
    cycles = [24, 5, 5]
    pie_colors = ['#e74c3c', '#2ecc71', '#3498db']

    wedges, texts, autotexts = ax3.pie(
        cycles, labels=engine_labels, autopct='%1.1f%%',
        startangle=140, colors=pie_colors,
        wedgeprops=dict(width=0.45, edgecolor='black', linewidth=1.2),
        pctdistance=0.75, textprops={'fontsize': 10}
    )
    for at in autotexts:
        at.set_fontweight('bold')
        at.set_color('white')

    ax3.set_title('(C) AI Forward Pass Cycle Distribution\n(Total: 34 Clock Cycles)', fontweight='bold', pad=12)

    plt.tight_layout()

    out_path = os.path.join(results_dir, 'heterogpu_evaluation_results.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved plot to: {out_path}")
    return out_path

if __name__ == '__main__':
    generate_all_plots()
