import matplotlib.pyplot as plt
import numpy as np
import re
from collections import defaultdict

# Parse the raw benchmark data
def parse_data():
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    # Extract data from the raw output
    sections = [
        ("Hybrid", "O0", [332117, 320913, 294577, 232674, 50226, 50178, 58643, 58668, 406765, 401175]),
        ("Hybrid", "O1", [72683, 72657, 79424, 79529, 13466, 13457, 6846, 6806, 171920, 171130]),
        ("Hybrid", "O2", [82846, 82818, 83099, 82710, 12441, 12575, 2124, 2131, 174533, 175023]),
        ("Hybrid", "O3", [83029, 82545, 82521, 82731, 3117, 3097, 2112, 2141, 174439, 175004]),
        ("Purecap Benchmark", "O0", [332408, 332332, 150394, 149183, 49901, 49894, 58950, 58951, 410201, 416466]),
        ("Purecap Benchmark", "O1", [67960, 67879, 69473, 69710, 14362, 14363, 8395, 8407, 172423, 172358]),
        ("Purecap Benchmark", "O2", [83342, 83709, 83574, 83512, 14420, 14419, 2077, 2074, 174525, 175368]),
        ("Purecap Benchmark", "O3", [83467, 83492, 83282, 83653, 3633, 3630, 2095, 2091, 176911, 176100]),
        ("Purecap", "O0", [331926, 331731, 521089, 521290, 50486, 50487, 58938, 58942, 407100, 407822]),
        ("Purecap", "O1", [68179, 68491, 69367, 69326, 14363, 14362, 8393, 8400, 171675, 171169]),
        ("Purecap", "O2", [84047, 83552, 83625, 83741, 14417, 14420, 2080, 2077, 175121, 174968]),
        ("Purecap", "O3", [83655, 83710, 83733, 83564, 3629, 3633, 2085, 2077, 175699, 175090])
    ]
    
    implementations = ["v1 (naive)", "v2 (vector)", "v3 (blocked/tiled)", "v4 (row-major)", "v5 (column-major)"]
    
    for abi, opt, times in sections:
        for i, impl in enumerate(implementations):
            # Each implementation has 2 measurements per section
            data[impl][abi][opt].extend(times[i*2:i*2+2])
    
    return data

def create_chart():
    data = parse_data()
    
    # Calculate averages
    averages = {}
    for impl in data:
        averages[impl] = {}
        for abi in data[impl]:
            averages[impl][abi] = {}
            for opt in data[impl][abi]:
                averages[impl][abi][opt] = np.mean(data[impl][abi][opt])
    
    # Setup
    implementations = ["v1 (naive)", "v2 (vector)", "v3 (blocked/tiled)", "v4 (row-major)", "v5 (column-major)"]
    abis = ['Hybrid', 'Purecap Benchmark', 'Purecap']
    optimizations = ['O0', 'O1', 'O2', 'O3']
    
    fig, ax = plt.subplots(figsize=(16, 4))
    
    # Calculate positions for each implementation group
    # Each implementation gets 12 bars (3 ABIs × 4 optimization levels)
    bar_width = 0.06  # Width of each individual bar
    group_width = 12 * bar_width  # Total width for one implementation group
    group_spacing = 0.1  # Spacing between implementation groups
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # Create bars for each implementation
    for impl_idx, impl in enumerate(implementations):
        # Calculate the center position for this implementation group
        group_center = impl_idx * (group_width + group_spacing)
        
        # Create 12 bars for this implementation (3 ABIs × 4 optimization levels)
        bar_idx = 0
        for abi_idx, abi in enumerate(abis):
            for opt_idx, opt in enumerate(optimizations):
                # Calculate position for this specific bar
                bar_pos = group_center - group_width/2 + bar_idx * bar_width + bar_width/2
                
                # Get the value for this combination
                if impl in averages and abi in averages[impl] and opt in averages[impl][abi]:
                    value = averages[impl][abi][opt]
                else:
                    value = 0
                
                # Create the bar
                ax.bar(bar_pos, value, bar_width, 
                      label=f'{abi} {opt}' if impl_idx == 0 else "",  # Only show legend for first implementation
                      color=colors[opt_idx], alpha=0.8,
                      hatch=["", "//", "\\"][abi_idx])
                
                bar_idx += 1
    
    # Set x-axis labels at the center of each implementation group
    x_positions = [i * (group_width + group_spacing) for i in range(len(implementations))]
    ax.set_xticks(x_positions)
    ax.set_xticklabels(implementations, rotation=0, ha='center', fontsize=18, fontweight='bold')
    ax.set_yscale('log')

    # Customize
    ax.set_xlabel('Matrix Multiplication Implementation', fontsize=30, fontweight='bold')
    ax.set_ylabel('Average Runtime (ms)', fontsize=20, fontweight='bold')
    ax.tick_params(axis='y', labelsize=20)
    # ax.set_title('Matrix Multiplication Performance Across ABIs and Optimization Levels', fontsize=20, fontweight='bold')
    ax.legend(bbox_to_anchor=(0.5, 1.38), loc='upper center', ncol=6, fontsize=14)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figure8-optimization-impact.png', dpi=300, bbox_inches='tight')
    # plt.show()

if __name__ == "__main__":
    create_chart()






