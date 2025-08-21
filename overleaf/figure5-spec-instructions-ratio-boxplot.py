#!/usr/bin/env python3

import ast
from re import A
import matplotlib.pyplot as plt
import numpy as np

# Read the raw profiling data
with open('raw-profiling-pmu-event-data.txt', 'r') as f:
    data_str = f.read()

# Parse the data (it's in Python dict format)
data = ast.literal_eval(data_str)

# ABI labels
abi_labels = ['Hybrid', 'Purecap Benchmark', 'Purecap']

# Spec instruction types we want to analyze
spec_types = ['inst_spec', 'ase_spec', 'br_indirect_spec', 'br_return_spec', 
              'br_immed_spec', 'vfp_spec', 'ld_spec', 'st_spec', 'dp_spec']

# Initialize results storage
results = []

# Process each benchmark
for benchmark, metrics in data.items():
    print(f"\nProcessing {benchmark}:")
    
    # Get the three runs for each metric (Hybrid, Benchmark, Purecap)
    for run_idx in range(3):
        run_results = {'benchmark': benchmark, 'abi': abi_labels[run_idx]}
        
        # Calculate total spec events
        total_spec = 0
        spec_events = {}
        
        # Find all spec events
        for metric, values in metrics.items():
            if metric in spec_types:
                spec_events[metric] = values[run_idx]
                total_spec += values[run_idx]
        
        # Calculate ratios for each spec type
        for spec_type in spec_types:
            if spec_type in spec_events and total_spec > 0:
                run_results[f'{spec_type}_ratio'] = spec_events[spec_type] / total_spec * 100
            else:
                run_results[f'{spec_type}_ratio'] = 0
        
        # Store total spec events for reference
        run_results['total_spec'] = total_spec
        
        # Print detailed breakdown for this run
        print(f"  {abi_labels[run_idx]} ABI:")
        print(f"    Total spec events: {total_spec:,}")
        for spec_type in spec_types:
            if spec_type in spec_events:
                ratio = run_results[f'{spec_type}_ratio']
                print(f"    {spec_type}: {spec_events[spec_type]:,} ({ratio:.2f}%)")
        
        results.append(run_results)

# Create a single figure with all spec instructions
fig, ax = plt.subplots(figsize=(16, 6))

# Prepare data for boxplots
all_data = []
all_labels = []
all_positions = []

# Colors for different ABIs
colors = ['#2E86AB', '#A23B72', '#F18F01']

# For each spec type, create 3 boxplots (one for each ABI)
for i, spec_type in enumerate(spec_types):
    base_pos = i * 4  # Space between spec types
    
    for j, abi in enumerate(abi_labels):
        # Get data for this spec type and ABI
        abi_data = [r[f'{spec_type}_ratio'] for r in results if r['abi'] == abi]
        all_data.append(abi_data)
        all_labels.append(f'{spec_type}\n{abi}')
        all_positions.append(base_pos + j)

# Create boxplots
bp = ax.boxplot(all_data, positions=all_positions, patch_artist=True, widths=0.6, boxprops=dict(alpha=0.7))

# Color the boxes
for i, patch in enumerate(bp['boxes']):
    abi_idx = i % 3
    patch.set_facecolor(colors[abi_idx])
    patch.set_alpha(0.7)

# Set x-axis labels
ax.set_xticks([i * 4 + 1 for i in range(len(spec_types))])
ax.set_xticklabels([_.replace('_spec', '\n_spec').replace('_return\n_spec', '\n_return_spec') for _ in spec_types], rotation=0, ha='center', fontsize=22, fontweight='bold')

# Add grid and labels
ax.grid(True, alpha=0.3, axis='y')
ax.set_yscale('log')
ax.set_ylabel('Ratio (%)', fontsize=30)
ax.tick_params(axis='y', labelsize=30)
# ax.set_title('Distribution of Spec Instruction Ratios Across Benchmarks by ABI', fontsize=22)

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=colors[i], alpha=0.7, label=abi_labels[i]) for i in range(3)]
ax.legend(handles=legend_elements, loc='lower right', fontsize=23)

# Add mean values as text on top of each box
for i, (data, pos) in enumerate(zip(all_data, all_positions)):
    mean_val = np.mean(data)
    
    if i // 3 == 0:
        _ypos = 1.0/3**(i % 3)
        _xpos = 1
    elif i // 3 == 1:
        _ypos = [0.01, 0.003, 0.001][i%3]
        _xpos = 5
    elif i // 3 == 2:
        _ypos = [35, 10, 3][i%3]
        _xpos = 9
    elif i // 3 == 3:
        _ypos = [35, 10, 3][i%3]
        _xpos = 13
    elif i // 3 == 4:
        _ypos = [0.01, 0.003, 0.001][i%3]
        _xpos = 17
    elif i // 3 == 5:
        _ypos = [0.01, 0.003, 0.001][i%3]
        _xpos = 21
    elif i // 3 == 6:
        _ypos = [1, 0.3, 0.1][i%3]
        _xpos = 25
    elif i // 3 == 7:
        _ypos = [0.4, 0.15, 0.05][i%3]
        _xpos = 29
    elif i // 3 == 8:
        _ypos = [1, 0.3, 0.1][i%3]
        _xpos = 33
    else:
        print(f"Error: i // 3 == {i // 3}")
        exit(1)

    ax.annotate(f'{mean_val:.1f}',
                xy=(_xpos, _ypos),
                xytext=(0, 5),  # 5 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=22, fontweight='bold',
                color=colors[i % 3],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig('figure5-spec-instructions-ratio-boxplot.png', dpi=300, bbox_inches='tight')

# Create a summary table
print(f"\n{'='*100}")
print("SUMMARY STATISTICS BY ABI:")
print(f"{'='*100}")

for abi in abi_labels:
    abi_data = [r for r in results if r['abi'] == abi]
    
    print(f"\n{abi} ABI:")
    print("-" * 50)
    
    for spec_type in spec_types:
        ratio_col = f'{spec_type}_ratio'
        values = [r[ratio_col] for r in abi_data]
        
        mean_val = np.mean(values)
        median_val = np.median(values)
        std_val = np.std(values)
        min_val = np.min(values)
        max_val = np.max(values)
        
        print(f"{spec_type:15s}: Mean={mean_val:6.2f}%, Median={median_val:6.2f}%, Std={std_val:6.2f}%, Range=[{min_val:5.2f}%, {max_val:5.2f}%]")

print(f"\n{'='*100}")
print("FILES GENERATED:")
print(f"{'='*100}")
print("- spec-instructions-ratio-boxplots-single.png: Single figure with all spec instruction ratios")

# Show the plots
plt.show() 