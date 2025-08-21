from ast import literal_eval

# Architectural constants
ISSUE_WIDTH = 4  # Neoverse-N1 & Morello theoretical maximum
# Reasonable latency values that work well with instruction mix validation
L1_LAT = 2    # 2 cycles (pipelined, hit under miss)
L2_LAT = 6    # 6 cycles (good prefetching)
LL_LAT = 50   # 50 cycles (modern memory hierarchy)

def read_data_as_dict(file_path):
    with open(file_path, "r") as f:
        content = f.read()
        return literal_eval(content)

def top_down_analysis(
    cpu_cycles,
    inst_retired,
    stall_frontend,
    stall_backend,
    l1d_cache_refill,
    l2d_cache_refill,
    ll_cache_miss_rd,
    mem_access_rd,
    mem_access_wr,
    inst_spec,
    ld_spec,
    st_spec,
    dp_spec,
    ase_spec,
    br_indirect_spec,
    br_return_spec,
    br_immed_spec,
    vfp_spec,
    mem_access_rd_ctag,
    mem_access_wr_ctag,
    cap_mem_access_rd,
    cap_mem_access_wr,
):
    """
    Top-down analysis following standard methodology.
    All metrics are normalized as fractions of total cycles or their parent metric.
    """

    # Input validation
    if cpu_cycles <= 0 or inst_retired <= 0:
        print("ERROR: Invalid input - cpu_cycles and inst_retired must be positive")
        return [0.0] * 15
    
    # Handle edge cases
    if stall_frontend < 0 or stall_backend < 0:
        print("WARNING: Negative stall counters detected, clamping to 0")
        stall_frontend = max(0, stall_frontend)
        stall_backend = max(0, stall_backend)
    
    # Check for unrealistic values
    if inst_retired > cpu_cycles * ISSUE_WIDTH:
        print("WARNING: inst_retired > cpu_cycles * ISSUE_WIDTH - this is impossible")
        print(f"  inst_retired: {inst_retired}, max possible: {cpu_cycles * ISSUE_WIDTH}")
    
    if stall_frontend + stall_backend > cpu_cycles:
        print("WARNING: Total stalls > cpu_cycles - counters may overlap")
        print(f"  Total stalls: {stall_frontend + stall_backend}, cpu_cycles: {cpu_cycles}")

    # ---------- Overall ----------
    IPC = inst_retired / cpu_cycles
    TOTAL_SLOTS = cpu_cycles * ISSUE_WIDTH

    # ---------- 1st-level metrics (normalized as fractions of total slots) ----------
    # Retiring: fraction of total slots that retired instructions
    Retiring = inst_spec / (inst_spec + ld_spec + st_spec + dp_spec + ase_spec + br_indirect_spec + br_return_spec + br_immed_spec + vfp_spec)

    # Frontend_Bound: fraction of total slots where frontend was the bottleneck
    # Note: stall_frontend likely represents cycles, not slots
    Frontend_Bound = stall_frontend / cpu_cycles
    
    # Backend_Bound: fraction of total slots where backend was the bottleneck  
    # Note: stall_backend likely represents cycles, not slots
    Backend_Bound = stall_backend / cpu_cycles
    
    # Bad_Speculation: remaining fraction (ensures sum = 1.0)
    # This is the standard top-down approach
    Bad_Speculation = max(0.0, 1.0 - (Retiring + Frontend_Bound + Backend_Bound))

    # ---------- 2nd-level backend split using instruction mix validation ----------
    # Calculate memory stalls using latency model
    Mem_Stall_Cycles = (
        l1d_cache_refill * L1_LAT
        + l2d_cache_refill * L2_LAT
        + ll_cache_miss_rd * LL_LAT
    )
    
    # Validate memory stall calculation
    if Mem_Stall_Cycles < 0:
        print("WARNING: Negative memory stall cycles calculated, setting to 0")
        Mem_Stall_Cycles = 0
    
    # NEW: Use instruction mix to validate/correct memory vs core bound calculation
    if inst_spec > 0:
        # Calculate instruction mix ratios
        mem_inst_ratio = (ld_spec + st_spec) / inst_spec  # Memory instruction ratio
        core_inst_ratio = dp_spec / inst_spec             # Core instruction ratio
        
        # Validate instruction mix
        total_inst_ratio = mem_inst_ratio + core_inst_ratio
        if total_inst_ratio > 1.0:
            print(f"WARNING: Instruction mix ratios sum to {total_inst_ratio:.4f} > 1.0")
            # Normalize
            mem_inst_ratio = mem_inst_ratio / total_inst_ratio
            core_inst_ratio = core_inst_ratio / total_inst_ratio
        
        # SIMPLE APPROACH: Use instruction mix directly to split backend stalls
        if stall_backend > 0:
            # Memory_Bound = fraction of backend stalls proportional to memory instructions
            # Core_Bound = fraction of backend stalls proportional to core instructions
            Memory_Bound = Backend_Bound * mem_inst_ratio
            Core_Bound = Backend_Bound * core_inst_ratio
        else:
            Memory_Bound = 0.0
            Core_Bound = Backend_Bound
        
        # Validate the split makes sense
        if abs((Memory_Bound + Core_Bound) - Backend_Bound) > 0.001:
            print("WARNING: Memory_Bound + Core_Bound != Backend_Bound")
            # Normalize to ensure they sum correctly
            total_backend = Memory_Bound + Core_Bound
            if total_backend > 0:
                Memory_Bound = Memory_Bound * Backend_Bound / total_backend
                Core_Bound = Core_Bound * Backend_Bound / total_backend
            else:
                Memory_Bound = 0.0
                Core_Bound = Backend_Bound
    else:
        # Fallback to original latency-based approach if no instruction mix data
        if stall_backend > 0:
            memory_ratio = Mem_Stall_Cycles / stall_backend
            if memory_ratio >= 1.0:
                Memory_Bound = Backend_Bound
                Core_Bound = 0.0
            elif memory_ratio >= 0.5:
                Memory_Bound = Backend_Bound * memory_ratio
                Core_Bound = Backend_Bound - Memory_Bound
            else:
                Memory_Bound = Backend_Bound * min(memory_ratio, 0.8)
                Core_Bound = Backend_Bound - Memory_Bound
        else:
            Memory_Bound = 0.0
            Core_Bound = Backend_Bound

    # ---------- 3rd-level memory breakdown ----------
    # Calculate individual cache level stalls
    L1_Stall_Cycles = l1d_cache_refill * L1_LAT
    L2_Stall_Cycles = l2d_cache_refill * L2_LAT
    LL_Stall_Cycles = ll_cache_miss_rd * LL_LAT
    
    # Validate cache stall calculations
    if L1_Stall_Cycles < 0 or L2_Stall_Cycles < 0 or LL_Stall_Cycles < 0:
        print("WARNING: Negative cache stall cycles detected, clamping to 0")
        L1_Stall_Cycles = max(0, L1_Stall_Cycles)
        L2_Stall_Cycles = max(0, L2_Stall_Cycles)
        LL_Stall_Cycles = max(0, LL_Stall_Cycles)
    
    # Normalize as fractions of Memory_Bound
    if Mem_Stall_Cycles > 0 and Memory_Bound > 0:
        L1_Bound = Memory_Bound * (L1_Stall_Cycles / Mem_Stall_Cycles)
        L2_Bound = Memory_Bound * (L2_Stall_Cycles / Mem_Stall_Cycles)
    else:
        L1_Bound = 0.0
        L2_Bound = 0.0
    
    # ExtMem_Bound: remaining memory stalls (LL cache + any unaccounted)
    ExtMem_Bound = max(0.0, Memory_Bound - (L1_Bound + L2_Bound))

    # ---------- CHERI metrics (ratios, not normalized) ----------
    # Handle division by zero cases and validate inputs
    if ld_spec < 0 or st_spec < 0 or inst_spec < 0:
        print("WARNING: Negative speculative instruction counts detected")
        ld_spec = max(0, ld_spec)
        st_spec = max(0, st_spec)
        inst_spec = max(0, inst_spec)
    
    if mem_access_rd < 0 or mem_access_wr < 0:
        print("WARNING: Negative memory access counts detected")
        mem_access_rd = max(0, mem_access_rd)
        mem_access_wr = max(0, mem_access_wr)
    
    Cap_Load_Density = cap_mem_access_rd / ld_spec if ld_spec > 0 else 0.0
    Cap_Store_Density = cap_mem_access_wr / st_spec if st_spec > 0 else 0.0
    
    total_mem_access = mem_access_rd + mem_access_wr
    Cap_Traffic_Share = (cap_mem_access_rd + cap_mem_access_wr) / total_mem_access if total_mem_access > 0 else 0.0
    Cap_Tag_Overhead = (mem_access_rd_ctag + mem_access_wr_ctag) / total_mem_access if total_mem_access > 0 else 0.0

    # ---------- Memory Intensity ----------
    Mem_Intensity = (ld_spec + st_spec) / inst_spec if inst_spec > 0 else 0.0

    return (
        Retiring,
        Frontend_Bound,
        Backend_Bound,
        Bad_Speculation,
        Memory_Bound,
        Core_Bound,
        L1_Bound,
        L2_Bound,
        ExtMem_Bound,
        IPC,
        Cap_Load_Density,
        Cap_Store_Density,
        Cap_Traffic_Share,
        Cap_Tag_Overhead,
        Mem_Intensity,
    )


def diagnose_warnings(cpu_cycles, inst_retired, stall_frontend, stall_backend, 
                     l1d_cache_refill, l2d_cache_refill, ll_cache_miss_rd,
                     inst_spec, ld_spec, st_spec, dp_spec):
    """Diagnose potential issues with input data that could cause top-down analysis warnings."""
    print("\n=== DIAGNOSTIC INFORMATION ===")
    
    # Check for basic data validity
    if cpu_cycles <= 0:
        print("ERROR: cpu_cycles must be positive")
    if inst_retired <= 0:
        print("ERROR: inst_retired must be positive")
    
    # Check stall counters
    total_stalls = stall_frontend + stall_backend
    if total_stalls > cpu_cycles:
        print(f"WARNING: Total stalls ({total_stalls}) > cpu_cycles ({cpu_cycles})")
        print("  This suggests overlapping or incorrect stall counters")
    
    # Check IPC
    ipc = inst_retired / cpu_cycles
    print(f"IPC: {ipc:.4f}")
    if ipc > 4.0:
        print("WARNING: IPC > 4.0 (theoretical max for Neoverse-N1)")
    if ipc < 0.1:
        print("WARNING: Very low IPC, workload may be severely bottlenecked")
    
    # NEW: Instruction mix analysis
    if inst_spec > 0:
        mem_inst_ratio = (ld_spec + st_spec) / inst_spec
        core_inst_ratio = dp_spec / inst_spec
        total_inst_ratio = mem_inst_ratio + core_inst_ratio
        
        print(f"\n=== INSTRUCTION MIX ANALYSIS ===")
        print(f"Memory instructions (ld+st): {ld_spec + st_spec} ({mem_inst_ratio:.4f})")
        print(f"Core instructions (dp): {dp_spec} ({core_inst_ratio:.4f})")
        print(f"Total speculative instructions: {inst_spec}")
        print(f"Instruction mix sum: {total_inst_ratio:.4f}")
        
        if total_inst_ratio > 1.0:
            print("WARNING: Instruction mix ratios sum > 1.0 - will normalize")
        elif total_inst_ratio < 0.8:
            print("WARNING: Low instruction mix coverage - missing instruction types")
        
        # Classify workload based on instruction mix
        if mem_inst_ratio >= 0.6:
            print("CLASSIFICATION: Memory-intensive workload")
        elif core_inst_ratio >= 0.6:
            print("CLASSIFICATION: Core-intensive workload")
        else:
            print("CLASSIFICATION: Balanced workload")
    
    # Check memory stall calculation
    mem_stall_cycles = (l1d_cache_refill * L1_LAT + l2d_cache_refill * L2_LAT + 
                       ll_cache_miss_rd * LL_LAT)
    print(f"\n=== MEMORY STALL ANALYSIS ===")
    print(f"Calculated memory stall cycles: {mem_stall_cycles}")
    print(f"Backend stall cycles: {stall_backend}")
    
    if mem_stall_cycles > stall_backend:
        print("WARNING: Memory stalls > backend stalls")
        print("  This suggests:")
        print("    - Cache misses may overlap with other operations")
        print("    - Latency model may overestimate stall cycles")
        print("    - Backend stall counter may not include all memory stalls")
        print("    - Memory operations may be pipelined/hidden")
        print("  The analysis will use instruction mix to validate this")
    elif mem_stall_cycles < stall_backend * 0.1:
        print("WARNING: Memory stalls << backend stalls")
        print("  This suggests most backend stalls are not memory-related")
        print("  Core_Bound will be significant")
    
    # NEW: Cross-validate with instruction mix
    if inst_spec > 0 and stall_backend > 0:
        latency_memory_ratio = mem_stall_cycles / stall_backend
        instruction_memory_ratio = (ld_spec + st_spec) / inst_spec
        
        print(f"\n=== CROSS-VALIDATION ===")
        print(f"Latency-based memory ratio: {latency_memory_ratio:.4f}")
        print(f"Instruction-based memory ratio: {instruction_memory_ratio:.4f}")
        
        ratio_diff = abs(latency_memory_ratio - instruction_memory_ratio)
        if ratio_diff > 0.3:
            print("WARNING: Large discrepancy between latency and instruction ratios")
            print("  This suggests:")
            if latency_memory_ratio > instruction_memory_ratio:
                print("    - Latency model overestimates memory stalls")
                print("    - Memory operations are efficient/hidden")
            else:
                print("    - Instruction mix suggests more memory operations")
                print("    - Memory stalls may be hidden by other operations")
        else:
            print("✓ Latency and instruction ratios are consistent")
    
    # Check cache miss ratios
    if l1d_cache_refill > 0:
        l1_miss_rate = l1d_cache_refill / (l1d_cache_refill + 1000)  # Rough estimate
        print(f"L1 miss rate estimate: {l1_miss_rate:.4f}")
    
    # Check top-level metric calculations
    total_slots = cpu_cycles * 4
    retiring = inst_retired / total_slots
    frontend_bound = stall_frontend / cpu_cycles
    backend_bound = stall_backend / cpu_cycles
    
    print(f"\n=== TOP-LEVEL METRICS ===")
    print(f"  Retiring: {retiring:.4f}")
    print(f"  Frontend_Bound: {frontend_bound:.4f}")
    print(f"  Backend_Bound: {backend_bound:.4f}")
    print(f"  Sum: {retiring + frontend_bound + backend_bound:.4f}")
    
    if retiring + frontend_bound + backend_bound > 1.0:
        print("WARNING: Top-level metrics sum > 1.0")
        print("  This indicates overlapping stall counters or incorrect normalization")
    
    print("=== END DIAGNOSTIC ===\n")


def validate_top_down_analysis(Retiring, Frontend_Bound, Backend_Bound, Bad_Speculation,
                              Memory_Bound, Core_Bound, L1_Bound, L2_Bound, ExtMem_Bound):
    """
    Validate the mathematical consistency of top-down analysis results.
    Returns True if valid, False if issues found.
    """
    is_valid = True
    
    # Check 1st-level metrics sum to 1.0
    top_level_sum = Retiring + Frontend_Bound + Backend_Bound + Bad_Speculation
    if abs(top_level_sum - 1.0) > 0.01:
        print(f"WARNING: Top-level metrics sum to {top_level_sum:.4f}, should be 1.0")
        print(f"  Retiring: {Retiring:.4f}")
        print(f"  Frontend_Bound: {Frontend_Bound:.4f}")
        print(f"  Backend_Bound: {Backend_Bound:.4f}")
        print(f"  Bad_Speculation: {Bad_Speculation:.4f}")
        is_valid = False
    
    # Check 2nd-level backend metrics sum correctly
    backend_sum = Memory_Bound + Core_Bound
    if abs(backend_sum - Backend_Bound) > 0.01:
        print(f"WARNING: Backend metrics sum to {backend_sum:.4f}, should be {Backend_Bound:.4f}")
        print(f"  Memory_Bound: {Memory_Bound:.4f}")
        print(f"  Core_Bound: {Core_Bound:.4f}")
        is_valid = False
    
    # Check 3rd-level memory metrics sum correctly
    memory_sum = L1_Bound + L2_Bound + ExtMem_Bound
    if abs(memory_sum - Memory_Bound) > 0.01:
        print(f"WARNING: Memory metrics sum to {memory_sum:.4f}, should be {Memory_Bound:.4f}")
        print(f"  L1_Bound: {L1_Bound:.4f}")
        print(f"  L2_Bound: {L2_Bound:.4f}")
        print(f"  ExtMem_Bound: {ExtMem_Bound:.4f}")
        is_valid = False
    
    # Check for negative values
    metrics = [Retiring, Frontend_Bound, Backend_Bound, Bad_Speculation, 
               Memory_Bound, Core_Bound, L1_Bound, L2_Bound, ExtMem_Bound]
    metric_names = ['Retiring', 'Frontend_Bound', 'Backend_Bound', 'Bad_Speculation',
                   'Memory_Bound', 'Core_Bound', 'L1_Bound', 'L2_Bound', 'ExtMem_Bound']
    
    for metric, name in zip(metrics, metric_names):
        if metric < -0.001:  # Allow small floating point errors
            print(f"WARNING: {name} is negative: {metric:.4f}")
            is_valid = False
    
    return is_valid


def verify_mathematical_consistency(Retiring, Frontend_Bound, Backend_Bound, Bad_Speculation,
                                   Memory_Bound, Core_Bound, L1_Bound, L2_Bound, ExtMem_Bound):
    """
    Verify all mathematical relationships in top-down analysis.
    Returns True if all relationships are satisfied.
    """
    print("\n=== MATHEMATICAL CONSISTENCY CHECK ===")
    all_valid = True
    
    # 1. Top-level metrics must sum to 1.0
    top_sum = Retiring + Frontend_Bound + Backend_Bound + Bad_Speculation
    if abs(top_sum - 1.0) <= 0.001:
        print(f"✓ Top-level metrics sum to 1.0: {top_sum:.6f}")
    else:
        print(f"✗ Top-level metrics sum to {top_sum:.6f}, should be 1.0")
        all_valid = False
    
    # 2. Backend metrics must sum to Backend_Bound
    backend_sum = Memory_Bound + Core_Bound
    if abs(backend_sum - Backend_Bound) <= 0.001:
        print(f"✓ Backend metrics sum to Backend_Bound: {backend_sum:.6f} = {Backend_Bound:.6f}")
    else:
        print(f"✗ Backend metrics sum to {backend_sum:.6f}, should be {Backend_Bound:.6f}")
        all_valid = False
    
    # 3. Memory metrics must sum to Memory_Bound
    memory_sum = L1_Bound + L2_Bound + ExtMem_Bound
    if abs(memory_sum - Memory_Bound) <= 0.001:
        print(f"✓ Memory metrics sum to Memory_Bound: {memory_sum:.6f} = {Memory_Bound:.6f}")
    else:
        print(f"✗ Memory metrics sum to {memory_sum:.6f}, should be {Memory_Bound:.6f}")
        all_valid = False
    
    # 4. All metrics must be non-negative
    metrics = [Retiring, Frontend_Bound, Backend_Bound, Bad_Speculation,
               Memory_Bound, Core_Bound, L1_Bound, L2_Bound, ExtMem_Bound]
    metric_names = ['Retiring', 'Frontend_Bound', 'Backend_Bound', 'Bad_Speculation',
                   'Memory_Bound', 'Core_Bound', 'L1_Bound', 'L2_Bound', 'ExtMem_Bound']
    
    for metric, name in zip(metrics, metric_names):
        if metric >= -0.001:  # Allow small floating point errors
            print(f"✓ {name}: {metric:.6f} (non-negative)")
        else:
            print(f"✗ {name}: {metric:.6f} (negative!)")
            all_valid = False
    
    # 5. Check for reasonable ranges
    if Retiring > 1.0:
        print(f"✗ Retiring > 1.0: {Retiring:.6f}")
        all_valid = False
    elif Retiring > 0.8:
        print(f"⚠ Retiring very high: {Retiring:.6f}")
    
    if Memory_Bound > Backend_Bound + 0.001:
        print(f"✗ Memory_Bound > Backend_Bound: {Memory_Bound:.6f} > {Backend_Bound:.6f}")
        all_valid = False
    
    print(f"=== CONSISTENCY CHECK {'PASSED' if all_valid else 'FAILED'} ===\n")
    return all_valid


def main():
    # data from verbose
    results = read_data_as_dict("./raw-profiling-pmu-event-data.txt")

    (
        Retiring,
        Frontend_Bound,
        Backend_Bound,
        Bad_Speculation,
        Memory_Bound,
        Core_Bound,
        L1_Bound,
        L2_Bound,
        ExtMem_Bound,
        IPC,
        Cap_Load_Density,
        Cap_Store_Density,
        Cap_Traffic_Share,
        Cap_Tag_Overhead,
        Mem_Intensity,
    ) = [[0.0, 0.0, 0.0] for _ in range(15)]

    for benchmark, metrics in results.items():
        for i in (0, 1, 2):
            cpu_cycles = metrics["cpu_cycles"][i]
            inst_retired = metrics["inst_retired"][i]
            stall_frontend = metrics["stall_frontend"][i]
            stall_backend = metrics["stall_backend"][i]
            l1d_cache_refill = metrics["l1d_cache_refill"][i]
            l2d_cache_refill = metrics["l2d_cache_refill"][i]
            ll_cache_miss_rd = metrics["ll_cache_miss_rd"][i]
            ll_cache_rd = metrics["ll_cache_rd"][i]
            mem_access_rd = metrics["mem_access_rd"][i]
            mem_access_wr = metrics["mem_access_wr"][i]
            inst_spec = metrics["inst_spec"][i]
            ld_spec = metrics["ld_spec"][i]
            st_spec = metrics["st_spec"][i]
            dp_spec = metrics["dp_spec"][i]
            ase_spec = metrics["ase_spec"][i]
            br_indirect_spec = metrics["br_indirect_spec"][i]
            br_return_spec = metrics["br_return_spec"][i]
            br_immed_spec = metrics["br_immed_spec"][i]
            vfp_spec = metrics["vfp_spec"][i]
            mem_access_rd_ctag = metrics["mem_access_rd_ctag"][i]
            mem_access_wr_ctag = metrics["mem_access_wr_ctag"][i]
            cap_mem_access_rd = metrics["cap_mem_access_rd"][i]
            cap_mem_access_wr = metrics["cap_mem_access_wr"][i]

            (
                Retiring[i],
                Frontend_Bound[i],
                Backend_Bound[i],
                Bad_Speculation[i],
                Memory_Bound[i],
                Core_Bound[i],
                L1_Bound[i],
                L2_Bound[i],
                ExtMem_Bound[i],
                IPC[i],
                Cap_Load_Density[i],
                Cap_Store_Density[i],
                Cap_Traffic_Share[i],
                Cap_Tag_Overhead[i],
                Mem_Intensity[i],
            ) = top_down_analysis(
                cpu_cycles,
                inst_retired,
                stall_frontend,
                stall_backend,
                l1d_cache_refill,
                l2d_cache_refill,
                ll_cache_miss_rd,
                mem_access_rd,
                mem_access_wr,
                inst_spec,
                ld_spec,
                st_spec,
                dp_spec,
                ase_spec,
                br_indirect_spec,
                br_return_spec,
                br_immed_spec,
                vfp_spec,
                mem_access_rd_ctag,
                mem_access_wr_ctag,
                cap_mem_access_rd,
                cap_mem_access_wr,
            )
            
            # Validate the results
            if i == 0:  # Only validate first iteration to avoid spam
                print(f"\nValidating results for {benchmark}:")
                is_valid = validate_top_down_analysis(
                    Retiring[i], Frontend_Bound[i], Backend_Bound[i], Bad_Speculation[i],
                    Memory_Bound[i], Core_Bound[i], L1_Bound[i], L2_Bound[i], ExtMem_Bound[i]
                )
                if is_valid:
                    print("✓ Top-down analysis validation passed")
                else:
                    print("✗ Top-down analysis validation failed - check input data")
                
                # Additional mathematical consistency check
                verify_mathematical_consistency(
                    Retiring[i], Frontend_Bound[i], Backend_Bound[i], Bad_Speculation[i],
                    Memory_Bound[i], Core_Bound[i], L1_Bound[i], L2_Bound[i], ExtMem_Bound[i]
                )
            
            # Run diagnostics if this is the first iteration (i=0) to avoid spam
            if i == 0:
                diagnose_warnings(cpu_cycles, inst_retired, stall_frontend, stall_backend,
                                    l1d_cache_refill, l2d_cache_refill, ll_cache_miss_rd,
                                    inst_spec, ld_spec, st_spec, dp_spec)

            # cut to three decimal places
            Retiring = [round(_, 3) for _ in Retiring]
            Frontend_Bound = [round(_, 3) for _ in Frontend_Bound]
            Backend_Bound = [round(_, 3) for _ in Backend_Bound]
            Bad_Speculation = [round(_, 3) for _ in Bad_Speculation]
            Memory_Bound = [round(_, 3) for _ in Memory_Bound]
            Core_Bound = [round(_, 3) for _ in Core_Bound]
            L1_Bound = [round(_, 3) for _ in L1_Bound]
            L2_Bound = [round(_, 3) for _ in L2_Bound]
            ExtMem_Bound = [round(_, 3) for _ in ExtMem_Bound]
            IPC = [round(_, 3) for _ in IPC]
            Cap_Load_Density = [round(_, 3) for _ in Cap_Load_Density]
            Cap_Store_Density = [round(_, 3) for _ in Cap_Store_Density]
            Cap_Traffic_Share = [round(_, 3) for _ in Cap_Traffic_Share]
            Cap_Tag_Overhead = [round(_, 3) for _ in Cap_Tag_Overhead]
            Mem_Intensity = [round(_, 3) for _ in Mem_Intensity]

        with open(f"./top-down-analysis-data-full.txt", "a") as f:
            print(f"'{benchmark}': {{", file=f)
            print(f"  'Retiring': {Retiring},", file=f)
            print(f"  'Frontend_Bound': {Frontend_Bound},", file=f)
            print(f"  'Backend_Bound': {Backend_Bound},", file=f)
            print(f"  'Bad_Speculation': {Bad_Speculation},", file=f)
            print(f"  'Memory_Bound': {Memory_Bound},", file=f)
            print(f"  'Core_Bound': {Core_Bound},", file=f)
            print(f"  'L1_Bound': {L1_Bound},", file=f)
            print(f"  'L2_Bound': {L2_Bound},", file=f)
            print(f"  'ExtMem_Bound': {ExtMem_Bound},", file=f)
            print(f"  'IPC': {IPC},", file=f)
            print(f"  'Cap_Load_Density': {Cap_Load_Density},", file=f)
            print(f"  'Cap_Store_Density': {Cap_Store_Density},", file=f)
            print(f"  'Cap_Traffic_Share': {Cap_Traffic_Share},", file=f)
            print(f"  'Cap_Tag_Overhead': {Cap_Tag_Overhead},", file=f)
            print(f"  'Mem_Intensity': {Mem_Intensity},", file=f)
            print("},", file=f)


if __name__ == "__main__":
    with open(f"./top-down-analysis-data-full.txt", "w") as f:
        print("{", file=f)
    main()
    with open(f"./top-down-analysis-data-full.txt", "a") as f:
        print("}", file=f)
