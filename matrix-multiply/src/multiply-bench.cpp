// Multi-version matrix multiply benchmark (FreeBSD/Linux/CHERI-ready)
// Measures time and memory (Max RSS) for each version
// Compilation: morello-clang++ -march=morello -mabi=purecap -O2 -o multiply_bench multiply_bench.cpp

#include <array>
#include <iostream>
#include <algorithm>
#include <chrono>
#include <sys/resource.h>
#include <unistd.h>
#include <vector>
#include <cstdio> // Added for FILE and fopen
#include <cstring> // Added for strncmp
#include <cstdlib> // Added for sscanf
#include <sys/sysctl.h>
#include <sys/user.h>

#ifndef NUM
#define NUM 2048
#endif
#ifndef TYPE
#define TYPE float
#endif

using namespace std;
using namespace std::chrono;

// General safe buffer allocation
template <typename T>
T* safe_alloc(size_t n) { return new T[n]; }
template <typename T>
void safe_free(T* ptr) { delete[] ptr; }

// Variant 1: Naive triple-loop (standard matrix multiply)
void multiply_v1(int msize, TYPE* a, TYPE* b, TYPE* c) {
    for (int i = 0; i < msize; ++i) {
        for (int j = 0; j < msize; ++j) {
            TYPE acc = 0;
            for (int k = 0; k < msize; ++k) {
                acc += a[i * msize + k] * b[k * msize + j];
            }
            c[i * msize + j] = acc;
        }
    }
}

// Variant 2: std::vector version (avoiding stack overflow)
void multiply_v2(int msize, std::vector<TYPE>& a, std::vector<TYPE>& b, std::vector<TYPE>& c) {
    for (int i = 0; i < msize; ++i) {
        for (int j = 0; j < msize; ++j) {
            TYPE acc = 0;
            for (int k = 0; k < msize; ++k) {
                acc += a[i * msize + k] * b[k * msize + j];
            }
            c[i * msize + j] = acc;
        }
    }
}

// Variant 3: Blocked/tiled multiply (improves cache locality)
void multiply_v3(int msize, TYPE* a, TYPE* b, TYPE* c, int tile) {
    std::fill(c, c + msize * msize, 0);
    for (int i0 = 0; i0 < msize; i0 += tile) {
        for (int j0 = 0; j0 < msize; j0 += tile) {
            for (int k0 = 0; k0 < msize; k0 += tile) {
                for (int i = i0; i < i0 + tile && i < msize; ++i) {
                    for (int j = j0; j < j0 + tile && j < msize; ++j) {
                        TYPE acc = 0;
                        for (int k = k0; k < k0 + tile && k < msize; ++k) {
                            acc += a[i * msize + k] * b[k * msize + j];
                        }
                        c[i * msize + j] += acc;
                    }
                }
            }
        }
    }
}

// Variant 4: Memory-bound version (row-major inner loop, minimizes cache misses)
void multiply_v4(int msize, TYPE* a, TYPE* b, TYPE* c) {
    std::fill(c, c + msize * msize, 0);
    for (int i = 0; i < msize; ++i) {
        for (int k = 0; k < msize; ++k) {
            TYPE aik = a[i * msize + k];
            for (int j = 0; j < msize; ++j) {
                c[i * msize + j] += aik * b[k * msize + j];
            }
        }
    }
}

// Variant 5: Column-wise version (if b is column-major)
void multiply_v5(int msize, TYPE* a, TYPE* b, TYPE* c) {
    std::fill(c, c + msize * msize, 0);
    for (int j = 0; j < msize; ++j) {
        for (int k = 0; k < msize; ++k) {
            TYPE bjk = b[k * msize + j];
            for (int i = 0; i < msize; ++i) {
                c[i * msize + j] += a[i * msize + k] * bjk;
            }
        }
    }
}

void print_memory_usage() {
    struct rusage usage;
    if (getrusage(RUSAGE_SELF, &usage) == 0) {
        std::cout << "[MEM] Max RSS: " << usage.ru_maxrss << " kB" << std::endl;
    }
}

void print_current_memory_usage() {
    // FreeBSD-compatible way to get current RSS
    struct kinfo_proc kp;
    size_t len = sizeof(kp);
    int mib[4] = { CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid() };
    
    if (sysctl(mib, 4, &kp, &len, NULL, 0) == 0) {
        std::cout << "[MEM] Current RSS: " << kp.ki_rssize << " kB" << std::endl;
    } else {
        std::cout << "[MEM] Current RSS: Unable to get" << std::endl;
    }
}

int main() {
    int msize = NUM;
    TYPE* a = safe_alloc<TYPE>(NUM * NUM);
    TYPE* b = safe_alloc<TYPE>(NUM * NUM);
    TYPE* c = safe_alloc<TYPE>(NUM * NUM);
    for (int i = 0; i < NUM * NUM; ++i) {
        a[i] = 1.0f;
        b[i] = 2.0f;
        c[i] = 0.0f;
    }

    auto t1 = high_resolution_clock::now();
    multiply_v1(msize, a, b, c);
    auto t2 = high_resolution_clock::now();
    cout << "multiply_v1 (naive): " << duration_cast<milliseconds>(t2 - t1).count() << " ms\n";
    // print_memory_usage();
    print_current_memory_usage();

    std::vector<TYPE> aa(NUM * NUM), bb(NUM * NUM), cc(NUM * NUM);
    std::fill(aa.begin(), aa.end(), 1.0f);
    std::fill(bb.begin(), bb.end(), 2.0f);
    std::fill(cc.begin(), cc.end(), 0.0f);
    t1 = high_resolution_clock::now();
    multiply_v2(msize, aa, bb, cc);
    t2 = high_resolution_clock::now();
    cout << "multiply_v2 (vector): " << duration_cast<milliseconds>(t2 - t1).count() << " ms\n";
    // // Prevent optimization by using the result
    // TYPE sum = 0;
    // for (int i = 0; i < NUM * NUM; ++i) {
    //     sum += cc[i];
    // }
    // cout << "Result sum: " << sum << " (should be " << NUM * NUM * 2.0f << ")\n";
    // print_memory_usage();
    print_current_memory_usage();

    std::fill(c, c + NUM * NUM, 0);
    t1 = high_resolution_clock::now();
    multiply_v3(msize, a, b, c, 32);
    t2 = high_resolution_clock::now();
    cout << "multiply_v3 (blocked/tiled): " << duration_cast<milliseconds>(t2 - t1).count() << " ms\n";
    // print_memory_usage();
    print_current_memory_usage();

    std::fill(c, c + NUM * NUM, 0);
    t1 = high_resolution_clock::now();
    multiply_v4(msize, a, b, c);
    t2 = high_resolution_clock::now();
    cout << "multiply_v4 (row-major inner): " << duration_cast<milliseconds>(t2 - t1).count() << " ms\n";
    // print_memory_usage();
    print_current_memory_usage();

    std::fill(c, c + NUM * NUM, 0);
    t1 = high_resolution_clock::now();
    multiply_v5(msize, a, b, c);
    t2 = high_resolution_clock::now();
    cout << "multiply_v5 (column-major): " << duration_cast<milliseconds>(t2 - t1).count() << " ms\n";
    // print_memory_usage();
    print_current_memory_usage();

    safe_free(a);
    safe_free(b);
    safe_free(c);
    return 0;
}
