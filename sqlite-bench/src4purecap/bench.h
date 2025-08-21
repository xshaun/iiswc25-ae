// Copyright (c) 2011 The LevelDB Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file. See the AUTHORS file for names of contributors.

#ifndef BENCH_H_
#define BENCH_H_

#include <assert.h>
#include <ctype.h>
#include <dirent.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <time.h>
#include "sqlite3.h"
#include <errno.h>

#ifdef __CHERI__
#include <cheriintrin.h>
#define CAPABILITY __capability
#define TO_CAPABILITY(ptr) ((void* __capability)(ptr))
#define FROM_CAPABILITY(ptr, type) ((type)(__cheri_fromcap(ptr)))
#else
#define CAPABILITY
#define TO_CAPABILITY(ptr) (ptr)
#define FROM_CAPABILITY(ptr, type) ((type)(ptr))
#endif

#define kNumBuckets 154
#define kNumData 1000000
#define MAX_PATH_LEN 1024
#define MAX_KEY_LEN 100
#define MAX_MSG_LEN 10000
#define MAX_BUF_LEN 200
#define MAX_CPUINFO_LINE 1000
#define MAX_CPUINFO_VAL 1000

// CHERI-specific safety macros
#ifdef __CHERI__
#define CHERI_CHECK_BOUNDS(ptr, size) do { \
    if (!__builtin_cheri_tag_get(TO_CAPABILITY(ptr)) || \
        __builtin_cheri_length_get(TO_CAPABILITY(ptr)) < (size)) { \
        fprintf(stderr, "CHERI capability violation: invalid or out of bounds access\n"); \
        exit(1); \
    } \
} while(0)

#define CHERI_CHECK_ALIGNMENT(ptr, align) do { \
    if (!__builtin_cheri_tag_get(TO_CAPABILITY(ptr)) || \
        (__builtin_cheri_offset_get(TO_CAPABILITY(ptr)) % (align)) != 0) { \
        fprintf(stderr, "CHERI capability violation: misaligned access\n"); \
        exit(1); \
    } \
} while(0)

#define CHERI_CHECK_PERMISSIONS(ptr, perms) do { \
    if (!__builtin_cheri_tag_get(TO_CAPABILITY(ptr)) || \
        (__builtin_cheri_perms_get(TO_CAPABILITY(ptr)) & (perms)) != (perms)) { \
        fprintf(stderr, "CHERI capability violation: insufficient permissions\n"); \
        exit(1); \
    } \
} while(0)

#define CHERI_SAFE_MALLOC(type, size) ({ \
    void* __capability _ptr = malloc(sizeof(type) * (size)); \
    if (_ptr == NULL) { \
        fprintf(stderr, "Memory allocation failed: %s\n", strerror(errno)); \
        exit(1); \
    } \
    CHERI_CHECK_BOUNDS(_ptr, sizeof(type) * (size)); \
    (type* __capability)_ptr; \
})

#define CHERI_SAFE_CALLOC(type, size) ({ \
    void* __capability _ptr = calloc(sizeof(type), (size)); \
    if (_ptr == NULL) { \
        fprintf(stderr, "Memory allocation failed: %s\n", strerror(errno)); \
        exit(1); \
    } \
    CHERI_CHECK_BOUNDS(_ptr, sizeof(type) * (size)); \
    (type* __capability)_ptr; \
})

#define CHERI_SAFE_REALLOC(ptr, type, size) ({ \
    void* __capability _new_ptr = realloc(TO_CAPABILITY(ptr), sizeof(type) * (size)); \
    if (_new_ptr == NULL) { \
        fprintf(stderr, "Memory reallocation failed: %s\n", strerror(errno)); \
        exit(1); \
    } \
    CHERI_CHECK_BOUNDS(_new_ptr, sizeof(type) * (size)); \
    (type* __capability)_new_ptr; \
})
#else
#define CHERI_CHECK_BOUNDS(ptr, size) ((void)0)
#define CHERI_CHECK_ALIGNMENT(ptr, align) ((void)0)
#define CHERI_CHECK_PERMISSIONS(ptr, perms) ((void)0)
#define CHERI_SAFE_MALLOC(type, size) malloc(sizeof(type) * (size))
#define CHERI_SAFE_CALLOC(type, size) calloc(sizeof(type), (size))
#define CHERI_SAFE_REALLOC(ptr, type, size) realloc(ptr, sizeof(type) * (size))
#endif

// Error handling macros
#define CHECK_ALLOC(ptr) do { \
    if ((ptr) == NULL) { \
        fprintf(stderr, "Memory allocation failed: %s\n", strerror(errno)); \
        exit(1); \
    } \
    CHERI_CHECK_BOUNDS(ptr, 1); \
} while(0)

#define CHECK_STRING_LEN(str, max_len) do { \
    if ((str) == NULL || strlen(str) >= (max_len)) { \
        fprintf(stderr, "String length exceeds maximum allowed length\n"); \
        exit(1); \
    } \
    CHERI_CHECK_BOUNDS(str, strlen(str) + 1); \
} while(0)

typedef struct Histogram {
  double min_;
  double max_;
  double num_;
  double sum_;
  double sum_squares_;
  double buckets_[kNumBuckets];
} Histogram;

typedef struct Raw {
  double* __capability data_;
  size_t data_size_;
  int pos_;
} Raw;

typedef struct Random {
  uint32_t seed_;
  uint32_t (*next)(struct Random*);  // Function pointer for next random number
} Random;

typedef struct RandomGenerator {
  char* __capability data_;
  size_t data_size_;
  int pos_;
} RandomGenerator;

// Comma-separated list of operations to run in the specified order
//   Actual benchmarks:
//
//   fillseq       -- write N values in sequential key order in async mode
//   fillseqsync   -- write N/100 values in sequential key order in sync mode
//   fillseqbatch  -- batch write N values in sequential key order in async mode
//   fillrandom    -- write N values in random key order in async mode
//   fillrandsync  -- write N/100 values in random key order in sync mode
//   fillrandbatch -- batch write N values in sequential key order in async mode
//   overwrite     -- overwrite N values in random key order in async mode
//   fillrand100K  -- write N/1000 100K values in random order in async mode
//   fillseq100K   -- write N/1000 100K values in sequential order in async mode
//   readseq       -- read N times sequentially
//   readrandom    -- read N times in random order
//   readrand100K  -- read N/1000 100K values in sequential order in async mode
extern CAPABILITY char* FLAGS_benchmarks;

// Number of key/values to place in database
extern int FLAGS_num;

// Number of read operations to do.  If negative, do FLAGS_num reads.
extern int FLAGS_reads;

// Size of each value
extern int FLAGS_value_size;

// Print histogram of operation timings
extern bool FLAGS_histogram;

// Print raw data
extern bool FLAGS_raw;

// Arrange to generate values that shrink to this fraction of
// their original size after compression
extern double FLAGS_compression_ratio;

// Page size. Default 1 KB.
extern int FLAGS_page_size;

// Number of pages.
// Default cache size = FLAGS_page_size * FLAGS_num_pages = 4 MB.
extern int FLAGS_num_pages;

// If true, do not destroy the existing database.  If you set this
// flag and also specify a benchmark that wants a fresh database, that
// benchmark will fail.
extern bool FLAGS_use_existing_db;

// If true, we allow batch writes to occur
extern bool FLAGS_transaction;

// If true, we enable Write-Ahead Logging
extern bool FLAGS_WAL_enabled;

// Use the db with the following name.
extern CAPABILITY char* FLAGS_db;

/* benchmark.c */
void benchmark_init(void);
void benchmark_fini(void);
void benchmark_run(void);
void benchmark_open(void);
void benchmark_write(bool, int, int, int, int, int);
void benchmark_read(int, int);
void benchmark_read_sequential(void);

/* histogram.c */
void histogram_clear(CAPABILITY Histogram*);
void histogram_add(CAPABILITY Histogram*, double);
void histogram_merge(CAPABILITY Histogram*, CAPABILITY const Histogram*);
CAPABILITY char* histogram_to_string(CAPABILITY Histogram*);

/* Raw */
void raw_clear(CAPABILITY Raw *);
void raw_add(CAPABILITY Raw *, double);
CAPABILITY char* raw_to_string(CAPABILITY Raw *);
void raw_print(CAPABILITY FILE *, CAPABILITY Raw *);

/* random.c */
void rand_init(CAPABILITY Random*, uint32_t);
uint32_t rand_next(CAPABILITY Random*);
uint32_t rand_uniform(CAPABILITY Random*, int);
void rand_gen_init(CAPABILITY RandomGenerator*, CAPABILITY const char*, size_t);
CAPABILITY char* rand_gen_generate(CAPABILITY RandomGenerator*, int);
CAPABILITY char* compressible_string(CAPABILITY Random*, double, size_t, size_t*);

/* util.c */
uint64_t now_micros(void);
bool starts_with(CAPABILITY const char*, CAPABILITY const char*);
CAPABILITY char* trim_space(CAPABILITY const char*);

#endif /* BENCH_H_ */
