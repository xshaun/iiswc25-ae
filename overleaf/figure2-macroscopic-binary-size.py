#!/usr/bin/env python3
"""
Binary Section Comparison Chart
Compares binary sections across different ABIs (hybrid, purecap-benchmark, purecap)

.text: Contains the executable machine code of the program. It's typically marked as read-only and executable.
.data: Holds initialized global and static variables that can be modified at runtime. It's both readable and writable.
.bss: Represents uninitialized global and static variables. At runtime, the system allocates and zero-initializes this section.
.rodata: Stores read-only data, such as string literals and constant variables. It's marked as read-only to prevent modifications.
.got + .got.plt (Global Offset Table)
.note.cheri 48
.data.rel.ro
.rela.dyn   Relocations for data and non-PLT code   Global variables, function pointers
Others
"""

import matplotlib.pyplot as plt
import numpy as np

def parse_readelf_data(filename):
    """Parse readelf output and return section sizes in bytes"""
    sections = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and '.' in line:
                parts = line.split()
                if len(parts) >= 2:
                    section_name = parts[0]
                    try:
                        size = int(parts[1])
                        sections[section_name] = size
                    except ValueError:
                        continue
    return sections

def classify_sections(sections):
    """Classify sections into categories"""
    categories = {
        '.text': 0,
        '.data': 0,
        '.bss': 0,
        '.rodata': 0,
        '.got*': 0,
        '.note.\n cheri': 0,
        '.data.\n rel.ro': 0,
        '.rela.\n dyn': 0,
        '.debug': 0,
        '.others': 0,
        'total': 0
    }
    
    for section, size in sections.items():
        if section == '.text':
            categories['.text'] += size
        elif section == '.data':
            categories['.data'] += size
        elif section == '.bss':
            categories['.bss'] += size
        elif section == '.rodata':
            categories['.rodata'] += size
        elif section in ['.got', '.got.plt']:
            categories['.got*'] += size
        elif section == '.note.cheri':
            categories['.note.\n cheri'] += size
        elif section == '.data.rel.ro':
            categories['.data.\n rel.ro'] += size
        elif section == '.rela.dyn':
            categories['.rela.\n dyn'] += size
        elif section.startswith('.debug'):
            categories['.debug'] += size
        else:
            categories['.others'] += size
        categories['total'] += size
    
    return categories

all_hybrid_values_normalized = []
all_purecap_benchmark_values_normalized = []
all_purecap_values_normalized = []
for benchmark_name in ['510.parest_r', '519.lbm_r', '520.omnetpp_r', '523.xalancbmk_r', '531.deepsjeng_r', '541.leela_r', '544.nab_r', '557.xz_r']:
    
    # Parse data from the three files
    hybrid_data = parse_readelf_data(f'../results/readelf/spec_run_readelf_{benchmark_name}_train_cheribsd-morello-hybrid-cheribuild_llvm')
    purecap_benchmark_data = parse_readelf_data(f'../results/readelf/spec_run_readelf_{benchmark_name}_train_cheribsd-morello-purecap-benchmark-cheribuild_llvm')
    purecap_data = parse_readelf_data(f'../results/readelf/spec_run_readelf_{benchmark_name}_train_cheribsd-morello-purecap-cheribuild_llvm')

    # Classify sections
    hybrid_categories = classify_sections(hybrid_data)
    purecap_benchmark_categories = classify_sections(purecap_benchmark_data)
    purecap_categories = classify_sections(purecap_data)

    # Prepare data for plotting
    categories = list(hybrid_categories.keys())
    hybrid_values = [hybrid_categories[cat] for cat in categories]
    purecap_benchmark_values = [purecap_benchmark_categories[cat] for cat in categories]
    purecap_values = [purecap_categories[cat] for cat in categories]

    # Use raw byte values (no conversion to MB)
    hybrid_values_normalized = []
    purecap_benchmark_values_normalized = []
    purecap_values_normalized = []
    for _value_hybrid, _value_purecap_benchmark, _value_purecap in zip(hybrid_values, purecap_benchmark_values, purecap_values):
        if _value_hybrid > 0:
            hybrid_values_normalized.append(1)
            purecap_benchmark_values_normalized.append(_value_purecap_benchmark / _value_hybrid)
            purecap_values_normalized.append(_value_purecap / _value_hybrid)
        else:
            hybrid_values_normalized.append(0)
            purecap_benchmark_values_normalized.append(_value_purecap_benchmark)
            purecap_values_normalized.append(_value_purecap)

    all_hybrid_values_normalized.append(hybrid_values_normalized)
    all_purecap_benchmark_values_normalized.append(purecap_benchmark_values_normalized)
    all_purecap_values_normalized.append(purecap_values_normalized)

# Create the plot
fig, ax1 = plt.subplots(figsize=(16, 6))

# Set up the positions for boxplots
x = np.arange(len(categories))
width = 0.25

# Prepare data for boxplots and determine which sections need secondary y-axis
hybrid_data_for_boxplot = []
purecap_bm_data_for_boxplot = []
purecap_data_for_boxplot = []
use_secondary_axis = []

for i in range(len(categories)):
    hybrid_section_data = [benchmark_data[i] for benchmark_data in all_hybrid_values_normalized if benchmark_data[i] > 0]
    purecap_bm_section_data = [benchmark_data[i] for benchmark_data in all_purecap_benchmark_values_normalized if benchmark_data[i] > 0]
    purecap_section_data = [benchmark_data[i] for benchmark_data in all_purecap_values_normalized if benchmark_data[i] > 0]
    
    hybrid_data_for_boxplot.append(hybrid_section_data)
    purecap_bm_data_for_boxplot.append(purecap_bm_section_data)
    purecap_data_for_boxplot.append(purecap_section_data)
    
    # Check if all values in this section are > 100
    all_values = hybrid_section_data + purecap_bm_section_data + purecap_section_data
    use_secondary_axis.append(all(all_values) and max(all_values) > 100)

# Create secondary y-axis
ax2 = ax1.twinx()

# Create boxplots with appropriate y-axis
secondary_positions = []  # Track positions of secondary y-axis boxplots

for i in range(len(categories)):
    if use_secondary_axis[i]:
        # Use secondary y-axis for sections with all values > 100
        bp1 = ax2.boxplot([hybrid_data_for_boxplot[i]], positions=[x[i]-width], widths=width*0.8,
                    patch_artist=True, boxprops=dict(facecolor='#2E86AB', alpha=0.7),
                    medianprops=dict(color='black'), flierprops=dict(marker='o', markerfacecolor='#2E86AB'))
        bp2 = ax2.boxplot([purecap_bm_data_for_boxplot[i]], positions=[x[i]], widths=width*0.8,
                    patch_artist=True, boxprops=dict(facecolor='#A23B72', alpha=0.7),
                    medianprops=dict(color='black'), flierprops=dict(marker='o', markerfacecolor='#A23B72'))
        bp3 = ax2.boxplot([purecap_data_for_boxplot[i]], positions=[x[i]+width], widths=width*0.8,
                    patch_artist=True, boxprops=dict(facecolor='#F18F01', alpha=0.7),
                    medianprops=dict(color='black'), flierprops=dict(marker='o', markerfacecolor='#F18F01'))
        
        # Track positions for shadow lines
        secondary_positions.append(x[i])
    else:
        # Use primary y-axis for sections with mixed values
        bp1 = ax1.boxplot([hybrid_data_for_boxplot[i]], positions=[x[i]-width], widths=width*0.8,
                    patch_artist=True, boxprops=dict(facecolor='#2E86AB', alpha=0.7),
                    medianprops=dict(color='black'), flierprops=dict(marker='o', markerfacecolor='#2E86AB'))
        bp2 = ax1.boxplot([purecap_bm_data_for_boxplot[i]], positions=[x[i]], widths=width*0.8,
                    patch_artist=True, boxprops=dict(facecolor='#A23B72', alpha=0.7),
                    medianprops=dict(color='black'), flierprops=dict(marker='o', markerfacecolor='#A23B72'))
        bp3 = ax1.boxplot([purecap_data_for_boxplot[i]], positions=[x[i]+width], widths=width*0.8,
                    patch_artist=True, boxprops=dict(facecolor='#F18F01', alpha=0.7),
                    medianprops=dict(color='black'), flierprops=dict(marker='o', markerfacecolor='#F18F01'))
    
    # Annotate median values
    def annotate_median(bp, ax, position, color, adjust_y_position=0):
        if len(bp['medians']) > 0:
            median_val = bp['medians'][0].get_ydata()[0]
            if median_val > 0:
                # Format the label based on the magnitude
                if median_val >= 1000:
                    label = f'{median_val:.0f}'
                elif median_val >= 100:
                    label = f'{median_val:.1f}'
                elif median_val >= 10:
                    label = f'{median_val:.2f}'
                else:
                    label = f'{median_val:.3f}'
                
                ax.annotate(label,
                           xy=(position, median_val + adjust_y_position),
                           xytext=(0, 5),  # 5 points vertical offset
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=16, fontweight='bold',
                           color=color,
                           bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
    
    # Annotate medians for each boxplot
    if use_secondary_axis[i]:
        # annotate_median(bp1, ax2, x[i]-width, '#2E86AB')
        annotate_median(bp2, ax2, x[i] - width, '#A23B72')
        annotate_median(bp3, ax2, x[i] + 2*width, '#F18F01')
    else:
        if categories[i] in ['.others', '.debug', 'total', '.rodata', '.bss']:
            # annotate_median(bp1, ax1, x[i]-width, '#2E86AB')
            annotate_median(bp2, ax1, x[i] + .5*width, '#A23B72', adjust_y_position=0.4)
            annotate_median(bp3, ax1, x[i] + .5* width, '#F18F01', adjust_y_position=1.2)
        else:
            # annotate_median(bp1, ax1, x[i]-width, '#2E86AB')
            annotate_median(bp2, ax1, x[i] - width, '#A23B72')
            annotate_median(bp3, ax1, x[i] + 2*width, '#F18F01')

# Add shadow lines for secondary y-axis boxplots
if secondary_positions:
    for pos in secondary_positions:
        # Add vertical dashed lines to indicate secondary y-axis usage
        ax1.axvline(x=pos, color='red', linestyle='--', alpha=0.3, linewidth=4)
        # Add horizontal dashed line at the bottom to connect
        ax1.axhline(y=ax1.get_ylim()[0], xmin=(pos-width*2)/len(categories), xmax=(pos+width*2)/len(categories), 
                   color='red', linestyle='--', alpha=0.3, linewidth=4)

# Customize the plot
# ax1.set_xlabel('Binary Sections', fontsize=12, fontweight='bold')
ax1.set_ylabel('Size (normalized to Hybrid)', fontsize=20, fontweight='bold')
ax2.set_ylabel('Size - Scaled Secondary Y', fontsize=20, fontweight='bold', color='red')
# ax1.set_title('Binary Section Comparison Across SPEC CPU Benchmarks\n(Boxplot showing distribution across 8 benchmarks)', fontsize=14, fontweight='bold', pad=20)
ax1.set_xticks(x)
ax1.set_xticklabels(categories, rotation=45, ha='right', fontsize=25, fontweight='bold')
ax1.tick_params(axis='y', labelsize=20)
ax1.grid(axis='y', alpha=0.3)

# Use logarithmic scale for both axes
ax1.set_yscale('log')
ax1.set_ylim(0, 100)
ax2.set_yscale('log')
ax2.set_ylim(1, 1000000)

# Color the secondary y-axis
ax2.spines['right'].set_color('red')
ax2.tick_params(axis='y', colors='red', labelsize=20)
ax2.yaxis.label.set_color('red')

# Create legend
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
legend_elements = [Patch(facecolor='#2E86AB', alpha=0.7, label='Hybrid'),
                   Patch(facecolor='#A23B72', alpha=0.7, label='Purecap Benchmark'),
                   Patch(facecolor='#F18F01', alpha=0.7, label='Purecap'),
                   Line2D([0], [0], color='red', linestyle='--', alpha=0.3, label='Secondary Y-axis indicator')]
ax1.legend(handles=legend_elements, loc='upper right', fontsize=18)

# Add horizontal line at y=1 (baseline) on primary axis
ax1.axhline(y=1, color='black', linestyle='--', alpha=0.5, label='Baseline (Hybrid=1)')

# # Add note about secondary y-axis
# ax1.text(0.02, 0.98, 'Red dashed lines indicate sections using secondary y-axis', 
#          transform=ax1.transAxes, fontsize=9, verticalalignment='top',
#          bbox=dict(boxstyle='round,pad=0.2', facecolor='lightgray', alpha=0.8))

ax1.text(0.02, 0.95, 'Numbers indicate median values', 
         transform=ax1.transAxes, fontsize=23, verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.2', facecolor='lightgray', alpha=0.4))

# Adjust layout
plt.tight_layout()

# Save the plot
plt.savefig('figure2-macroscopic-binary-size.png', dpi=300, bbox_inches='tight')

# Print summary statistics
print("Binary Section Sizes (normalized to Hybrid) - Statistics across 8 benchmarks:")
print("-" * 80)
print(f"{'Section':<20} {'Hybrid':<15} {'PureCap-BM':<15} {'PureCap':<15} {'Y-Axis':<10}")
print("-" * 80)

for i, cat in enumerate(categories):
    hybrid_stats = hybrid_data_for_boxplot[i]
    purecap_bm_stats = purecap_bm_data_for_boxplot[i]
    purecap_stats = purecap_data_for_boxplot[i]
    
    hybrid_median = np.median(hybrid_stats) if hybrid_stats else 0
    purecap_bm_median = np.median(purecap_bm_stats) if purecap_bm_stats else 0
    purecap_median = np.median(purecap_stats) if purecap_stats else 0
    
    y_axis_type = "Secondary" if use_secondary_axis[i] else "Primary"
    
    print(f"{cat:<20} {hybrid_median:<15.3f} {purecap_bm_median:<15.3f} {purecap_median:<15.3f} {y_axis_type:<10}")

print("\nNote: Values shown are medians across 8 SPEC CPU benchmarks")
print("Boxplots show the full distribution including outliers")
print("Secondary Y-axis is used for sections where all values > 100")

# plt.show()
