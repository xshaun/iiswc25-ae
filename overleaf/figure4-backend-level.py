import matplotlib.pyplot as plt
import numpy as np
from ast import literal_eval

def read_data_as_dict(file_path):
    with open(file_path, "r") as f:
        content = f.read()
        return literal_eval(content)

data = read_data_as_dict("./top-down-analysis-data.txt")

benchmarks = list(data.keys())

# Hybrid data
core_bound_1 = [data[benchmark]['Core_Bound'][0] * 100 for benchmark in benchmarks]
memory_bound_1 = [data[benchmark]['Memory_Bound'][0] * 100 for benchmark in benchmarks]

# Benchmark data (example values - replace with actual data)
core_bound_2 = [data[benchmark]['Core_Bound'][1] * 100 for benchmark in benchmarks]
memory_bound_2 = [data[benchmark]['Memory_Bound'][1] * 100 for benchmark in benchmarks]

# Purecap data (example values - replace with actual data)
core_bound_3 = [data[benchmark]['Core_Bound'][2] * 100 for benchmark in benchmarks]
memory_bound_3 = [data[benchmark]['Memory_Bound'][2] * 100 for benchmark in benchmarks]

x = np.arange(len(benchmarks))
width = 0.25  # Reduced width to accommodate three groups

fig, ax = plt.subplots(figsize=(16, 6))


# Plot Hybrid
p1 = ax.bar(x - width, core_bound_1, width, label='Core Bound (Hybrid)', color='#b6d7a8')
p2 = ax.bar(x - width, memory_bound_1, width, bottom=core_bound_1, label='Memory Bound (Hybrid)', color='#ffe599')

# Plot Benchmark
p3 = ax.bar(x, core_bound_2, width, label='Core Bound (Benchmark)', color='#8dc63f')
p4 = ax.bar(x, memory_bound_2, width, bottom=core_bound_2, label='Memory Bound (Benchmark)', color='#f1c232')

# Plot Purecap
p5 = ax.bar(x + width, core_bound_3, width, label='Core Bound (Purecap)', color='#6aa84f')
p6 = ax.bar(x + width, memory_bound_3, width, bottom=core_bound_3, label='Memory Bound (Purecap)', color='#bf9000')

# # Add values at the top of each bar
# for i in range(len(benchmarks)):
#     # Hybrid values
#     if core_bound_1[i] > 0:
#       hybrid_total = core_bound_1[i] + memory_bound_1[i]
#       ax.text(i - width, hybrid_total+.02, f'{core_bound_1[i]:.2f}'.lstrip('0'),
#               ha='center', va='bottom', fontsize=10, color='#4B6FA5', rotation=45)
#       ax.text(i - width, hybrid_total+.08, f'{memory_bound_1[i]:.2f}'.lstrip('0'),
#               ha='center', va='bottom', fontsize=10, color='#E6A6C6', rotation=45)
#     else:
#       ax.text(i - width, memory_bound_1[i]+.02, f'{memory_bound_1[i]:.2f}'.lstrip('0'),
#               ha='center', va='bottom', fontsize=10, color='#E6A6C6', rotation=45)
#     # Benchmark values
#     if core_bound_2[i] > 0:
#       benchmark_total = core_bound_2[i] + memory_bound_2[i]
#       ax.text(i, benchmark_total+.02, f'{core_bound_2[i]:.2f}'.lstrip('0'),
#               ha='center', va='bottom', fontsize=10, color='#2E4B8F', rotation=45)
#       ax.text(i, benchmark_total+.08, f'{memory_bound_2[i]:.2f}'.lstrip('0'),
#               ha='center', va='bottom', fontsize=10, color='#C47AA6', rotation=45)
#     else:
#       ax.text(i, memory_bound_2[i]+.02, f'{memory_bound_2[i]:.2f}'.lstrip('0'),
#               ha='center', va='bottom', fontsize=10, color='#C47AA6', rotation=45)
    
#     # Purecap values
#     if core_bound_3[i] > 0:
#       purecap_total = core_bound_3[i] + memory_bound_3[i]
#       ax.text(i + width, purecap_total+.02, f'{core_bound_3[i]:.2f}'.lstrip('0'),
#               ha='center', va='bottom', fontsize=8, color='#1A2B5F', rotation=45)
#       ax.text(i + width, purecap_total+.08, f'{memory_bound_3[i]:.2f}'.lstrip('0'),
#               ha='center', va='bottom', fontsize=8, color='#A24D86', rotation=45)
#     else:
#       ax.text(i + width, memory_bound_3[i]+.02, f'{memory_bound_3[i]:.2f}'.lstrip('0'),
#               ha='center', va='bottom', fontsize=8, color='#A24D86', rotation=45)

ax.set_ylabel('Counter Percentage(%)', fontsize=28, fontweight='bold')
ax.set_ylim(0, 100)
ax.tick_params(axis='y', labelsize=20)
ax.set_xticks(x)
benchmarks = [_[0:7] for _ in benchmarks]
ax.set_xticklabels(benchmarks, rotation=90, fontsize=24, ha='left', rotation_mode='anchor', fontweight='bold')
for tick in ax.xaxis.get_major_ticks():
    tick.set_pad(80)

# Create custom legend with fewer entries
handles = [p2, p1, p4, p3, p6, p5]
labels = ['Memory Bound (Hybrid)', 'Core Bound (Hybrid)',
          'Memory Bound (Benchmark)', 'Core Bound (Benchmark)',
          'Memory Bound (Purecap)', 'Core Bound (Purecap)']
ax.legend(handles, labels, loc='upper center',
          ncol=3, frameon=False, fontsize=18)

plt.tight_layout()
plt.savefig('figure4-backend-level.png', dpi=300, bbox_inches='tight')
plt.close()
