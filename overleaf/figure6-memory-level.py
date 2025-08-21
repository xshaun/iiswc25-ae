import matplotlib.pyplot as plt
import numpy as np
from ast import literal_eval

def read_data_as_dict(file_path):
    with open(file_path, "r") as f:
        content = f.read()
        return literal_eval(content)

data = read_data_as_dict("./top-down-analysis-data.txt")

# Benchmarks (x-axis labels)
benchmarks = list(data.keys())

# Data structure for three groups (Hybrid, Benchmark, Purecap)
# Each inner list contains [Hybrid, Benchmark, Purecap] values
L1_bound = [metrics['L1_Bound'] for _, metrics in data.items()]
L2_bound = [metrics['L2_Bound'] for _, metrics in data.items()]
ExtMem_bound = [metrics['ExtMem_Bound'] for _, metrics in data.items()]

# Set up the figure
fig, ax = plt.subplots(figsize=(16, 6))

# Bar width and positions
bar_width = 0.25  # Width of each bar
group_spacing = 0.2  # Space between groups
ind = np.arange(len(benchmarks)) * (bar_width * 3 + group_spacing)

# Colors for each mode
colors = {
    'L1': ['#ffe599', '#f1c232', '#bf9000'],    # Light to dark yellow
    'L2': ['#a64d4d', '#8b0000', '#5c0000'],  # Light to dark red
    'ExtMem': ['#b6d7a8', '#8dc63f', '#6aa84f'],  # Light to dark green
}


# Plot bars for each group (Hybrid, Benchmark, Purecap)
for i, group in enumerate(['Hybrid', 'Benchmark', 'Purecap']):
    offset = i * bar_width *1.05
    bottom = np.zeros(len(benchmarks))
    
    # Plot each memory level
    ax.bar(ind + offset, [ExtMem_bound[j][i] * 100 for j in range(len(benchmarks))], bar_width,
           bottom=bottom, label=f'{group} ExtMem' if i == 0 else "", color=colors['ExtMem'][i])
    bottom += [ExtMem_bound[j][i] * 100 for j in range(len(benchmarks))]
    
    ax.bar(ind + offset, [L2_bound[j][i] * 100 for j in range(len(benchmarks))], bar_width,
           bottom=bottom, label=f'{group} L2' if i == 0 else "", color=colors['L2'][i])
    bottom += [L2_bound[j][i] * 100 for j in range(len(benchmarks))]

    ax.bar(ind + offset, [L1_bound[j][i] * 100 for j in range(len(benchmarks))], bar_width,
           bottom=bottom, label=f'{group} L1' if i == 0 else "", color=colors['L1'][i])

# Add group labels to x-axis
group_positions = ind + bar_width
ax.set_xticks(group_positions)
benchmarks = [_[0:7] for _ in benchmarks]
ax.set_xticklabels(benchmarks, rotation=90, fontsize=24, ha='left', rotation_mode='anchor', fontweight='bold')
for tick in ax.xaxis.get_major_ticks():
    tick.set_pad(80)

# ax.text(2, 0.7, '(Hybrid, Benchmark, Purecap)',
#             ha='center', va='bottom', fontsize=20)

ax.set_ylim(0, 60)
ax.set_ylabel('Counter Percentage(%)', fontsize=28, fontweight='bold')
ax.tick_params(axis='y', labelsize=20)
# ax.set_title('Memory Level Analysis by Execution Mode')

# Create a custom legend
handles = []
handles.extend([
    plt.Rectangle((0,0), 1, 1, color=colors['L1'][0], label=f'L1 Bound'),
    plt.Rectangle((0,0), 1, 1, color=colors['L2'][0], label=f'L2 Bound'),
    plt.Rectangle((0,0), 1, 1, color=colors['ExtMem'][0], label=f'ExtMem Bound')
])

ax.legend(handles=handles, loc='upper right', ncol=1, fontsize=25, frameon=False)

plt.tight_layout()
plt.savefig('figure6-memory-level.png', dpi=300, bbox_inches='tight')
plt.close()
