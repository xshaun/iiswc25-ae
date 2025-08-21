import matplotlib.pyplot as plt
import numpy as np
from ast import literal_eval

def read_data_as_dict(file_path):
    with open(file_path, "r") as f:
        content = f.read()
        return literal_eval(content)

data = read_data_as_dict("./top-down-analysis-data.txt")

# Example data (replace with your actual data)
benchmarks = list(data.keys())
n = len(benchmarks)

# Generate data for three groups (replace with your actual values)
# Each group's values must sum to 1 for each benchmark
groups = ['Hybrid', 'Benchmark', 'Purecap']
n_groups = len(groups)

# Generate random data for each group (replace with your actual data)
retiring = [[metrics['Retiring'][i] * 100 for _, metrics in data.items()] for i in range(3)]
bad_spec = [[metrics['Bad_Speculation'][i] * 100 for _, metrics in data.items()] for i in range(3)]
frontend = [[metrics['Frontend_Bound'][i] * 100 for _, metrics in data.items()] for i in range(3)]
backend = [[metrics['Backend_Bound'][i] * 100 for _, metrics in data.items()] for i in range(3)]
ipc = [[metrics['IPC'][i] for _, metrics in data.items()] for i in range(3)]

# Set up the figure
fig, ax1 = plt.subplots(figsize=(16, 6))

# Define colors with different shades for each group
colors = {
    'retiring': ['#b6d7a8', '#8dc63f', '#6aa84f'],  # Light to dark green
    'bad_spec': ['#a64d4d', '#8b0000', '#5c0000'],  # Light to dark red
    'frontend': ['#6c3483', '#4a235a', '#2e0f3a'],  # Light to dark purple
    'backend': ['#ffe599', '#f1c232', '#bf9000']    # Light to dark yellow
}

# Calculate bar positions
bar_width = 0.25  # Width of each bar
group_spacing = 0.2  # Space between groups
ind = np.arange(n) * (bar_width * n_groups + group_spacing)

# Plot bars for each group
for i, group in enumerate(groups):
    offset = i * bar_width * 1.05
    # Stacked bars for each group
    bottom = np.zeros(n)
    ax1.bar(ind + offset, retiring[i], bar_width, bottom=bottom, 
            label=f'{group} Retiring' if i == 0 else "", color=colors['retiring'][i])
    bottom += retiring[i]
    ax1.bar(ind + offset, bad_spec[i], bar_width, bottom=bottom,
            label=f'{group} Bad Spec' if i == 0 else "", color=colors['bad_spec'][i])
    bottom += bad_spec[i]
    ax1.bar(ind + offset, frontend[i], bar_width, bottom=bottom,
            label=f'{group} Frontend' if i == 0 else "", color=colors['frontend'][i])
    bottom += frontend[i]
    ax1.bar(ind + offset, backend[i], bar_width, bottom=bottom,
            label=f'{group} Backend' if i == 0 else "", color=colors['backend'][i])

# Add group labels to x-axis
group_positions = ind + bar_width * (n_groups - 1) / 2
ax1.set_xticks(group_positions)
benchmarks = [_[0:7] for _ in benchmarks]
ax1.set_xticklabels(benchmarks, rotation=90, fontsize=24, ha='left', rotation_mode='anchor', zorder=0, transform=ax1.get_xaxis_transform(), fontweight='bold')
for tick in ax1.xaxis.get_major_ticks():
    tick.set_pad(80)

# # Add group indicators
# for i, group in enumerate(groups):
#     ax1.text(ind[0] + i * bar_width, -0.05, group, 
#              transform=ax1.transData, ha='center', va='top')

ax1.set_ylabel('Counter Percentage(%)', fontsize=28, fontweight='bold')
ax1.tick_params(axis='y', labelsize=30)
ax1.set_ylim(0, 100)

# Create a custom legend
# handles = []
# for i, group in enumerate(groups):
#     handles.extend([
#         plt.Rectangle((0,0), 1, 1, color=colors['retiring'][i], label=f'{group} Retiring'),
#         plt.Rectangle((0,0), 1, 1, color=colors['bad_spec'][i], label=f'{group} Bad Spec'),
#         plt.Rectangle((0,0), 1, 1, color=colors['frontend'][i], label=f'{group} Frontend'),
#         plt.Rectangle((0,0), 1, 1, color=colors['backend'][i], label=f'{group} Backend')
#     ])
handles = []
handles.extend([
    plt.Rectangle((0,0), 1, 1, color=colors['retiring'][0], label=f'Retiring'),
    plt.Rectangle((0,0), 1, 1, color=colors['bad_spec'][0], label=f'Bad Spec'),
    plt.Rectangle((0,0), 1, 1, color=colors['frontend'][0], label=f'Frontend'),
    plt.Rectangle((0,0), 1, 1, color=colors['backend'][0], label=f'Backend')
])

# Add IPC lines for each group
ax2 = ax1.twinx()

# Plot IPC lines within each group
for j, benchmark in enumerate(benchmarks):
    # First plot the points
    x_positions = []
    y_values = []
    for i, group in enumerate(groups):
        if ipc[i][j] == 0:
            continue
        # Calculate x position for this benchmark within the group
        x_pos = ind[j] + i * bar_width
        x_positions.append(x_pos)
        y_values.append(ipc[i][j])
        # Plot individual points
        ax2.plot(x_pos, ipc[i][j], color='#5dade2', marker='^', linestyle='None', markersize=10,
                label=f'IPC' if j == 0 and i == 0 else "")
    
    # Then connect the points with a line
    ax2.plot(x_positions, y_values, color='#5dade2', linestyle='solid', linewidth=2)
    

ax2.set_ylabel('IPC', fontsize=30)
ax2.tick_params(axis='y', labelsize=30)
ax2.set_ylim(0, 3)

# Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
# Only show unique benchmark names in legend
unique_benchmark_labels = []
unique_benchmark_handles = []
seen_labels = set()
for handle, label in zip(lines2, labels2):
    if label not in seen_labels:
        seen_labels.add(label)
        unique_benchmark_labels.append(label)
        unique_benchmark_handles.append(handle)

ax1.legend(handles=handles + unique_benchmark_handles, 
          labels=[h.get_label() for h in handles] + unique_benchmark_labels,
          loc='upper left', bbox_to_anchor=(-0.05, 1.2), fontsize=24, ncol=5, frameon=False)

# plt.title('Top Level')
plt.tight_layout()
plt.savefig('figure3-top-level.png', dpi=300, bbox_inches='tight')
# plt.show()
