// Copyright (c 2011 The LevelDB Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file. See the AUTHORS file for names of contributors.

#include "bench.h"
#include <cheriintrin.h>

enum Order {
  SEQUENTIAL,
  RANDOM
};

enum DBState {
  FRESH,
  EXISTING
};

sqlite3* db_;
int db_num_;
int num_;
int reads_;
double start_;
double last_op_finish_;
int64_t bytes_;
char* message_;
Histogram hist_;
Raw raw_;
RandomGenerator gen_;
Random rand_;

/* State kept for progress messages */
int done_;
int next_report_;

static void print_header(void);
static void print_warnings(void);
static void print_environment(void);
static void start(void);
static void stop(const char *name);

inline
static void exec_error_check(int status, char *err_msg) {
  if (status != SQLITE_OK) {
    fprintf(stderr, "SQL error: %s\n", err_msg);
    sqlite3_free(err_msg);
    exit(1);
  }
}

inline
static void step_error_check(int status) {
  if (status != SQLITE_DONE) {
    fprintf(stderr, "SQL step error: status = %d\n", status);
    exit(1);
  }
}

inline
static void error_check(int status) {
  if (status != SQLITE_OK) {
    fprintf(stderr, "sqlite3 error: status = %d\n", status);
    exit(1);
  }
}

inline
static void wal_checkpoint(sqlite3* db_) {
  /* Flush all writes to disk */
  if (FLAGS_WAL_enabled) {
    sqlite3_wal_checkpoint_v2(db_, NULL, SQLITE_CHECKPOINT_FULL, NULL,
                              NULL);
  }
}

static void print_header() {
  const int kKeySize = 16;
  print_environment();
  fprintf(stderr, "Keys:       %d bytes each\n", kKeySize);
  fprintf(stderr, "Values:     %d bytes each\n", FLAGS_value_size);  
  fprintf(stderr, "Entries:    %d\n", num_);
  fprintf(stderr, "RawSize:    %.1f MB (estimated)\n",
            (((int64_t)(kKeySize + FLAGS_value_size) * num_)
            / 1048576.0));
  print_warnings();
  fprintf(stderr, "------------------------------------------------\n");
}

static void print_warnings() {
#if defined(__GNUC__) && !defined(__OPTIMIZE__)
  fprintf(stderr,
      "WARNING: Optimization is disabled: benchmarks unnecessarily slow\n"
      );
#endif
#ifndef NDEBUG
  fprintf(stderr,
      "WARNING: Assertions are enabled: benchmarks unnecessarily slow\n"
      );
#endif
}

static void print_environment() {
  fprintf(stderr, "SQLite:     version %s\n", SQLITE_VERSION);
#if defined(__linux)
  time_t now = time(NULL);
  fprintf(stderr, "Date:       %s", ctime(&now));

  FILE* cpuinfo = fopen("/proc/cpuinfo", "r");
  if (cpuinfo != NULL) {
    char line[1000];
    int num_cpus = 0;
    char* cpu_type = malloc(sizeof(char) * 1000);
    char* cache_size = malloc(sizeof(char) * 1000);
    while (fgets(line, sizeof(line), cpuinfo) != NULL) {
      char* sep = strchr(line, ':');
      if (sep == NULL) {
        continue;
      }
      char* key = calloc(sizeof(char), 1000);
      char* val = calloc(sizeof(char), 1000);
      strncpy(key, line, sep - 1 - line);
      strcpy(val, sep + 1);
      char* trimed_key = trim_space(key);
      char* trimed_val = trim_space(val);
      free(key);
      free(val);
      if (!strcmp(trimed_key, "model name")) {
        ++num_cpus;
        strcpy(cpu_type, trimed_val);
      } else if (!strcmp(trimed_key, "cache size")) {
        strcpy(cache_size, trimed_val);
      }
      free(trimed_key);
      free(trimed_val);
    }
    fclose(cpuinfo);
    fprintf(stderr, "CPU:        %d * %s\n", num_cpus, cpu_type);
    fprintf(stderr, "CPUCache:   %s\n", cache_size);
    free(cpu_type);
    free(cache_size);
  }
#endif
}

static void start() {
  start_ = now_micros() * 1e-6;
  bytes_ = 0;
  message_ = malloc(sizeof(char) * MAX_MSG_LEN);
  CHECK_ALLOC(message_);
  message_[0] = '\0';
  last_op_finish_ = start_;
  histogram_clear(&hist_);
  raw_clear(&raw_);
  done_ = 0;
  next_report_ = 100;
}

void finished_single_op() {
  if (FLAGS_histogram || FLAGS_raw) {
    double now = now_micros() * 1e-6;
    double micros = (now - last_op_finish_) * 1e6;
    if (FLAGS_histogram) {
      histogram_add(&hist_, micros);
      if (micros > 20000) {
        fprintf(stderr, "long op: %.1f micros%30s\r", micros, "");
        fflush(stderr);
      }
    }
    if (FLAGS_raw) {
      raw_add(&raw_, micros);
    }
    last_op_finish_ = now;
  }

  done_++;
  if (done_ >= next_report_) {
    if      (next_report_ < 1000)   next_report_ += 100;
    else if (next_report_ < 5000)   next_report_ += 500;
    else if (next_report_ < 10000)  next_report_ += 1000;
    else if (next_report_ < 50000)  next_report_ += 5000;
    else if (next_report_ < 100000) next_report_ += 10000;
    else if (next_report_ < 500000) next_report_ += 50000;
    else                            next_report_ += 100000;
    fprintf(stderr, "... finished %d ops%30s\r", done_, "");
    fflush(stderr);
  }
}

static void stop(const char* name) {
  double finish = now_micros() * 1e-6;

  if (done_ < 1) done_ = 1;

  if (bytes_ > 0) {
    char *rate = malloc(sizeof(char) * 100);;
    snprintf(rate, strlen(rate), "%6.1f MB/s",
              (bytes_ / 1048576.0) / (finish - start_));
    if (message_ && !strcmp(message_, "")) {
      message_ = strcat(strcat(rate, " "), message_);
    } else {
      message_ = rate;
    }
  }

  fprintf(stderr, "%-12s : %11.3f micros/op;%s%s\n",
          name,
          (finish - start_) * 1e6 / done_,
          (!message_ || !strcmp(message_, "") ? "" : " "),
          (!message_) ? "" : message_);
  if (FLAGS_raw) {
    raw_print(stdout, &raw_);
  }
  if (FLAGS_histogram) {
    fprintf(stderr, "Microseconds per op:\n%s\n",
            histogram_to_string(&hist_));
  }
  fflush(stdout);
  fflush(stderr);
}

void benchmark_init() {
  db_ = NULL;
  db_num_ = 0;
  num_ = FLAGS_num;
  reads_ = FLAGS_reads < 0 ? FLAGS_num : FLAGS_reads;
  bytes_ = 0;
  
  // Initialize random number generator first
  rand_init(&rand_, 301);
  
  // Generate a compressible string for the random generator
  size_t raw_len;
  CAPABILITY char* data = compressible_string(&rand_, FLAGS_compression_ratio, FLAGS_value_size, &raw_len);
  if (data == NULL) {
    fprintf(stderr, "Failed to generate compressible string\n");
    exit(1);
  }
  
  // Initialize the random generator with the compressible string
  rand_gen_init(&gen_, data, raw_len);
  free(data);

  if (FLAGS_db == NULL) {
    fprintf(stderr, "Database path is NULL\n");
    exit(1);
  }

  CHECK_STRING_LEN(FLAGS_db, MAX_PATH_LEN);

  struct dirent* ep;
  DIR* test_dir = opendir(FLAGS_db);
  if (!test_dir) {
    fprintf(stderr, "Cannot open directory %s: %s\n", FLAGS_db, strerror(errno));
    exit(1);
  }

  if (!FLAGS_use_existing_db) {
    while ((ep = readdir(test_dir)) != NULL) {
      if (starts_with(ep->d_name, "dbbench_sqlite3")) {
        char file_name[MAX_PATH_LEN];
        int written = snprintf(file_name, sizeof(file_name), "%s%s", FLAGS_db, ep->d_name);
        if (written < 0 || (size_t)written >= sizeof(file_name)) {
          fprintf(stderr, "Path too long\n");
          closedir(test_dir);
          exit(1);
        }
        remove(file_name);
      }
    }
  }
  closedir(test_dir);
}

void benchmark_fini() {
  int status = sqlite3_close(db_);
  error_check(status);
}

void benchmark_run() {
  print_header();
  benchmark_open();

  char* benchmarks = FLAGS_benchmarks;
  while (benchmarks != NULL) {
    char* sep = strchr(benchmarks, ',');
    char* name;
    if (sep == NULL) {
      name = benchmarks;
      benchmarks = NULL;
    } else {
      name = calloc(sizeof(char), (sep - benchmarks + 1));
      strncpy(name, benchmarks, sep - benchmarks);
      benchmarks = sep + 1;
    }
    bytes_ = 0;
    start();
    bool known = true;
    bool write_sync = false;
    if (!strcmp(name, "fillseq")) {
      benchmark_write(write_sync, SEQUENTIAL, FRESH, num_, FLAGS_value_size, 1);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "fillseqbatch")) {
      benchmark_write(write_sync, SEQUENTIAL, FRESH, num_, FLAGS_value_size, 1000);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "fillrandom")) {
      benchmark_write(write_sync, RANDOM, FRESH, num_, FLAGS_value_size, 1);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "fillrandbatch")) {
      benchmark_write(write_sync, RANDOM, FRESH, num_, FLAGS_value_size, 1000);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "overwrite")) {
      benchmark_write(write_sync, RANDOM, EXISTING, num_, FLAGS_value_size, 1);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "overwritebatch")) {
      benchmark_write(write_sync, RANDOM, EXISTING, num_, FLAGS_value_size, 1000);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "fillrandsync")) {
      write_sync = true;
      benchmark_write(write_sync, RANDOM, FRESH, num_ / 100, FLAGS_value_size, 1);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "fillseqsync")) {
      write_sync = true;
      benchmark_write(write_sync, SEQUENTIAL, FRESH, num_ / 100, FLAGS_value_size, 1);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "fillrand100K")) {
      benchmark_write(write_sync, RANDOM, FRESH, num_ / 1000, 100 * 1000, 1);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "fillseq100K")) {
      benchmark_write(write_sync, SEQUENTIAL, FRESH, num_ / 1000, 100 * 1000, 1);
      wal_checkpoint(db_);
    } else if (!strcmp(name, "readseq")) {
      benchmark_read(SEQUENTIAL, 1);
    } else if (!strcmp(name, "readrandom")) {
      benchmark_read(RANDOM, 1);
    } else if (!strcmp(name, "readrand100K")) {
      int n = reads_;
      reads_ /= 1000;
      benchmark_read(RANDOM, 1);
      reads_ = n;
    } else {
      known = false;
      if (strcmp(name, "")) {
        fprintf(stderr, "unknown benchmark '%s'\n", name);
      }
    }
    if (known) {
      stop(name);
    }
  }
}

void benchmark_open() {
  assert(db_ == NULL);

  int status;
  char file_name[MAX_PATH_LEN];
  char* err_msg = NULL;
  db_num_++;

  if (FLAGS_db == NULL) {
    fprintf(stderr, "Database path is NULL\n");
    exit(1);
  }

  CHECK_STRING_LEN(FLAGS_db, MAX_PATH_LEN);

  int written = snprintf(file_name, sizeof(file_name),
                        "%sdbbench_sqlite3-%d.db",
                        (char*)__builtin_cheri_address_get(FLAGS_db),
                        db_num_);
  if (written < 0 || (size_t)written >= sizeof(file_name)) {
    fprintf(stderr, "Database path too long\n");
    exit(1);
  }

  status = sqlite3_open(file_name, &db_);
  if (status) {
    fprintf(stderr, "open error: %s\n", sqlite3_errmsg(db_));
    exit(1);
  }

  char cache_size[MAX_BUF_LEN];
  written = snprintf(cache_size, sizeof(cache_size), 
                    "PRAGMA cache_size = %d", FLAGS_num_pages);
  if (written < 0 || (size_t)written >= sizeof(cache_size)) {
    fprintf(stderr, "Cache size string too long\n");
    sqlite3_close(db_);
    exit(1);
  }

  status = sqlite3_exec(db_, cache_size, NULL, NULL, &err_msg);
  exec_error_check(status, err_msg);

  if (FLAGS_page_size != 1024) {
    char page_size[MAX_BUF_LEN];
    written = snprintf(page_size, sizeof(page_size), 
                      "PRAGMA page_size = %d", FLAGS_page_size);
    if (written < 0 || (size_t)written >= sizeof(page_size)) {
      fprintf(stderr, "Page size string too long\n");
      sqlite3_close(db_);
      exit(1);
    }
    status = sqlite3_exec(db_, page_size, NULL, NULL, &err_msg);
    exec_error_check(status, err_msg);
  }

  if (FLAGS_WAL_enabled) {
    status = sqlite3_exec(db_, "PRAGMA journal_mode = WAL", NULL, NULL, &err_msg);
    exec_error_check(status, err_msg);
    status = sqlite3_exec(db_, "PRAGMA wal_autocheckpoint = 4096", NULL, NULL, &err_msg);
    exec_error_check(status, err_msg);
  }

  const char* stmt_array[] = {
    "PRAGMA locking_mode = EXCLUSIVE",
    "CREATE TABLE test (key blob, value blob, PRIMARY KEY (key))",
    NULL
  };

  for (const char** stmt = stmt_array; *stmt != NULL; stmt++) {
    status = sqlite3_exec(db_, *stmt, NULL, NULL, &err_msg);
    exec_error_check(status, err_msg);
  }
}

void benchmark_write(bool write_sync, int order, int state,
                    int num_entries, int value_size, int entries_per_batch) {
  if (state == FRESH) {
    if (FLAGS_use_existing_db) {
      message_ = malloc(sizeof(char) * MAX_MSG_LEN);
      CHECK_ALLOC(message_);
      strncpy(message_, "skipping (--use_existing_db is true)", MAX_MSG_LEN - 1);
      message_[MAX_MSG_LEN - 1] = '\0';
      return;
    }
    sqlite3_close(db_);
    db_ = NULL;
    benchmark_open();
    start();
  }

  if (num_entries != num_) {
    char* msg = malloc(sizeof(char) * MAX_MSG_LEN);
    CHECK_ALLOC(msg);
    int written = snprintf(msg, MAX_MSG_LEN, "(%d ops)", num_entries);
    if (written < 0 || (size_t)written >= MAX_MSG_LEN) {
      free(msg);
      fprintf(stderr, "Message string too long\n");
      exit(1);
    }
    message_ = msg;
  }

  char* err_msg = NULL;
  int status;

  sqlite3_stmt *replace_stmt, *begin_trans_stmt, *end_trans_stmt;
  char* replace_str = "REPLACE INTO test (key, value) VALUES (?, ?)";
  char* begin_trans_str = "BEGIN TRANSACTION";
  char* end_trans_str = "END TRANSACTION";

  /* Check for synchronous flag in options */
  char* sync_stmt = (write_sync) ? "PRAGMA synchronous = FULL" :
                                    "PRAGMA synchronous = OFF";
  status = sqlite3_exec(db_, sync_stmt, NULL, NULL, &err_msg);
  exec_error_check(status, err_msg);

  /* Preparing sqlite3 statements */
  status = sqlite3_prepare_v2(db_, replace_str, -1,
                              &replace_stmt, NULL);
  error_check(status);
  status = sqlite3_prepare_v2(db_, begin_trans_str, -1,
                              &begin_trans_stmt, NULL);
  error_check(status);
  status = sqlite3_prepare_v2(db_, end_trans_str, -1,
                              &end_trans_stmt, NULL);
  error_check(status);

  bool transaction = (entries_per_batch > 1);
  for (int i = 0; i < num_entries; i += entries_per_batch) {
    /* Begin write transaction */
    if (FLAGS_transaction && transaction) {
      status = sqlite3_step(begin_trans_stmt);
      step_error_check(status);
      status = sqlite3_reset(begin_trans_stmt);
      error_check(status);
    }

    /* Create and execute SQL statements */
    for (int j = 0; j < entries_per_batch; j++) {
      const char* value = rand_gen_generate(&gen_, value_size);

      /* Create values for key-value pair */
      const int k = (order == SEQUENTIAL) ? i + j :
                    (rand_next(&rand_) % num_entries);
      char key[100];
      snprintf(key, sizeof(key), "%016d", k);

      /* Bind KV values into replace_stmt */
      status = sqlite3_bind_blob(replace_stmt, 1, key, 16, SQLITE_STATIC);
      error_check(status);
      status = sqlite3_bind_blob(replace_stmt, 2, value,
                                  value_size, SQLITE_STATIC);
      error_check(status);

      /* Execute replace_stmt */
      bytes_ += value_size + strlen(key);
      status = sqlite3_step(replace_stmt);
      step_error_check(status);

      /* Reset SQLite statement for another use */
      status = sqlite3_clear_bindings(replace_stmt);
      error_check(status);
      status = sqlite3_reset(replace_stmt);
      error_check(status);

      finished_single_op();
    }

    /* End write transaction */
    if (FLAGS_transaction && transaction) {
      status = sqlite3_step(end_trans_stmt);
      step_error_check(status);
      status = sqlite3_reset(end_trans_stmt);
      error_check(status);
    }
  }

  status = sqlite3_finalize(replace_stmt);
  error_check(status);
  status = sqlite3_finalize(begin_trans_stmt);
  error_check(status);
  status = sqlite3_finalize(end_trans_stmt);
  error_check(status);
}

void benchmark_read(int order, int entries_per_batch) {
  int status;
  sqlite3_stmt *read_stmt, *begin_trans_stmt, *end_trans_stmt;

  char *read_str = "SELECT * FROM test WHERE key = ?";
  char *begin_trans_str = "BEGIN TRANSACTION";
  char *end_trans_str = "END TRANSACTION";

  /* Preparing sqlite3 statements */
  status = sqlite3_prepare_v2(db_, begin_trans_str, -1,
                              &begin_trans_stmt, NULL);
  error_check(status);
  status = sqlite3_prepare_v2(db_, end_trans_str, -1,
                              &end_trans_stmt, NULL);
  error_check(status);
  status = sqlite3_prepare_v2(db_, read_str, -1,
                              &read_stmt, NULL);
  error_check(status);

  bool transaction = (entries_per_batch > 1);
  for (int i = 0; i < reads_; i += entries_per_batch) {
    /* Begin read transaction */
    if (FLAGS_transaction && transaction) {
      status = sqlite3_step(begin_trans_stmt);
      step_error_check(status);
      status = sqlite3_reset(begin_trans_stmt);
      error_check(status);
    }

    /* Create and execute SQL statements */
    for (int j = 0; j < entries_per_batch; j++) {
      /* Create key value */
      char key[100];
      int k = (order == SEQUENTIAL) ? i + j : (rand_next(&rand_) % reads_);
      snprintf(key, sizeof(key), "%016d", k);

      /* Bind key value into read_stmt */
      status = sqlite3_bind_blob(read_stmt, 1, key, 16, SQLITE_STATIC);
      error_check(status);
      
      /* Execute read statement */
      while ((status = sqlite3_step(read_stmt)) == SQLITE_ROW) {}
      step_error_check(status);

      /* Reset SQLite statement for another use */
      status = sqlite3_clear_bindings(read_stmt);
      error_check(status);
      status = sqlite3_reset(read_stmt);
      error_check(status);
      finished_single_op();
    }

    /* End read transaction */
    if (FLAGS_transaction && transaction) {
      status = sqlite3_step(end_trans_stmt);
      step_error_check(status);
      status = sqlite3_reset(end_trans_stmt);
      error_check(status);
    }
  }

  status = sqlite3_finalize(read_stmt);
  error_check(status);
  status = sqlite3_finalize(begin_trans_stmt);
  error_check(status);
  status = sqlite3_finalize(end_trans_stmt);
  error_check(status);
}
