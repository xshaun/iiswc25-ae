import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# Example data structure (replace with your actual data)
benchmarks = [
    '510.pa\nrest_r', '519.\nlbm_r', '520.om\nnetpp_r', '523.xala\nncbmk_r', '531.deep\nsjeng_r',
    '541.\nleela_r', '544.\nnab_r', '557.\nxz_r', 'LLAMA \n inference', 'LLAMA \n matmul', 'SQLite', 'QuickJS'
]
metrics = [
    'Execution Time', 'IPC', 'Branch MR', 'L1I MR', 'L1D MR', 'L2D MR'
]
# Fill this with your actual data, each entry: [Hybrid, Purecap Benchmark, Purecap ABIs]
data = {
    'Execution Time': [
        [37.87, 41.94, 43.10], [38.00, 35.06, 35.0], 
        [81.73, 142.30,153.21], [53.59, 77.95, 109.07], 
        [67.42, 73.64, 78.85], [97.01, 110.59, 119.46], 
        [99.03, 103.39, 103.92], [46.93, 49.65, 49.98], 
        [477.93, 483.79, 484.11], [126.31, 124.57, 124.61], 
        [18.18, 28.24, 29.30], [22.51, None, 59.87]
    ],
    'IPC': [
        [1.691, 1.634, 1.599], [.929, 1.112, 1.108], 
        [.578, .554, .516], [1.813, 1.605, 1.188], 
        [1.702, 1.635, 1.539], [1.406, 1.402, 1.295], 
        [1.538, 1.515, 1.516], [1.091, 1.059, 1.037], 
        [1.827, 2.049, 2.055], [2.306, 2.329, 2.324], 
        [1.579, 1.366, 1.299], [1.612, None, 1.182]
    ],
    'Branch MR': [
        [.90, .77, .76], [1.52, 1.53, 1.46], 
        [2.80, 1.95, 2.20], [.44, .39, .53], 
        [2.99, 3.00, 2.99], [7.36, 7.25, 7.22], 
        [1.16, 1.12, 1.14], [5.56, 5.52, 5.48], 
        [.04, .05, .05], [.04, .03, .04], 
        [.91, 1.04, 1.10], [1.79, None, 1.68]
    ],
    'L1I MR': [
        [.05, .12, .11], [.15, .16, .15], 
        [.35, .57, .70], [.98, 1.32, .98], 
        [.03, .13, .13], [.01, .09, .05], 
        [0, 0, 0], [.07, .09, .09], 
        [.02, .02, .02], [0, 0, 0], 
        [4.29, 4.40, 4.54], [1.17, None, 1.67]
    ],
    'L1D MR': [
        [2.65, 2.72, 2.73], [19.71, 22.75, 22.29], 
        [4.55, 4.65, 4.46], [.62, 1.21, 1.04], 
        [.43, .49, .47], [.55, .61, .61], 
        [1.28, 1.29, 1.31], [1.88, 1.88, 1.88], 
        [2.05, 1.99, 1.97], [.96, .97, .96], 
        [1.70, 2.08, 2.11], [1.06, None, 1.61]
    ],
    'L2D MR': [
        [5.75, 5.64, 5.64], [12.32, 9.50, 9.52], 
        [27.74, 25.42, 25.59], [.41, 2.06, 2.42], 
        [22.98, 19.15, 18.46], [1.93, 3.31, 3.39], 
        [1.85, 1.88, 1.83], [22.63, 22.24, 22.08], 
        [6.74, 7.15, 7.14], [.32, .34, .35], 
        [2.55, 3.77, 3.77], [2.49, None, 5.39]
    ],
    'LLC Read MR': [
        [99.19, 99.27, 99.38], [99.17, 99.09, 98.96], 
        [92.88, 96.10, 95.95], [94.52, 96.29, 96.00], 
        [97.77, 97.45, 97.72], [96.24, 96.38, 96.45], 
        [97.58, 99.18, 97.95], [96.95, 96.32, 96.53], 
        [67.21, 67.49, 66.93], [92.56, 92.51, 92.13], 
        [95.16, 93.86, 94.20], [91.31, None, 96.39]
    ]
}

# Normalize to Hybrid
normalized_data = {}
for metric, values in data.items():
    norm = []
    for v in values:
        hybrid = v[0]
        norm.append([1.0 if hybrid > 0 else 0, v[1]/hybrid if hybrid >0 and v[1] is not None else 0, v[2]/hybrid if hybrid >0 and v[2] is not None else 0])
    normalized_data[metric] = norm

# Plotting
num_metrics = len(metrics)
fig, axes = plt.subplots(num_metrics, 1, figsize=(16, 1*num_metrics), sharex=True)

x = np.arange(len(benchmarks))
width = 0.25
labels = ['Hybrid', 'Purecap Benchmark', 'Purecap ABIs']
colors = ['#2E86AB', '#A23B72', '#F18F01']


for idx, metric in enumerate(metrics):
    ax = axes[idx] if num_metrics > 1 else axes
    norm_vals = np.array(normalized_data[metric])
    
    for j in range(len(norm_vals)):
        if norm_vals[j][1] == 0:
            ax.plot([j + -1 * width, j + 1 * width], [norm_vals[j][0], norm_vals[j][2]], color='#5dade2', linestyle='solid', linewidth=2)
        else:
            ax.plot([j + (i-1) * width for i in range(3)], norm_vals[j], color='#5dade2', linestyle='solid', linewidth=2)

    for i in range(3):
        # ax.bar(x + (i-1)*width, norm_vals[:, i], width, label=labels[i] if idx == 0 else "", color=colors[i], alpha=0.7)
        area = (40 * norm_vals[:, i])
        ax.scatter(x + (i-1)*width, norm_vals[:, i], s=area,  color=colors[i], alpha=0.7)
        # print(norm_vals[:, i])
        
    ax.set_ylabel(metric.replace('Execution', 'Exec').replace(' ', '\n'), fontsize=20, rotation=0, ha='right', position=(0, -0.2), fontweight='bold')

    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1)
    if idx == 0 or idx == 4:
        ax.set_ylim(0, 3)
    elif idx == 1 or idx == 2:
        ax.set_ylim(0, 2)
    elif idx == 3:
        ax.set_yscale('log')
        ax.set_ylim(0.1, 100)
    elif idx == 5:
        ax.set_yscale('log')
        ax.set_ylim(0.1, 10)
    elif idx == 6:
        ax.set_ylim(0.5, 1.5)

    if idx == num_metrics - 1:
        ax.set_xticks(x)
        ax.set_xticklabels(benchmarks, rotation=45, ha='right', fontsize=22, fontweight='bold')
    
    ax.tick_params(axis='y', labelsize=15)

legend_elements = [Patch(facecolor='#2E86AB', alpha=0.7, label='Hybrid'),
                   Patch(facecolor='#A23B72', alpha=0.7, label='Purecap Benchmark'),
                   Patch(facecolor='#F18F01', alpha=0.7, label='Purecap')]
fig.legend(handles=legend_elements, loc='upper center', fontsize=25, ncol=3, bbox_to_anchor=(0.5, 1.12))

plt.tight_layout()
plt.savefig('figure1-macroscopic-performance.png', dpi=300, bbox_inches='tight')

