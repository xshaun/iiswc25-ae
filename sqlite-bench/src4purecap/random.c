// Copyright (c) 2011 The LevelDB Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file. See the AUTHORS file for names of contributors.

#include "bench.h"

static char *random_string(Random*, int);
char *compressible_string(Random*, double, size_t, size_t*);

/*
 * https://github.com/google/leveldb/blob/master/util/testutil.cc
 */
static char *random_string(Random* rnd, int len) {
  if (rnd == NULL || len < 0) {
    return NULL;
  }
  
  CHERI_CHECK_BOUNDS(rnd, sizeof(Random));
  
  CAPABILITY char* dst = CHERI_SAFE_MALLOC(char, len + 1);
  
  for (int i = 0; i < len; i++) {
    CHERI_CHECK_BOUNDS(dst + i, 1);
    dst[i] = ' ' + (rnd->next(rnd) % (95));  // ' ' .. '~'
  }
  dst[len] = '\0';

  return dst;
}

char *compressible_string(Random* rnd, double compressed_fraction, size_t len, size_t* raw_len) {
  if (rnd == NULL || compressed_fraction < 0.0 || compressed_fraction > 1.0) {
    return NULL;
  }
  
  CHERI_CHECK_BOUNDS(rnd, sizeof(Random));
  int raw = (int)(len * compressed_fraction);
  if (raw < 1) raw = 1;
  *raw_len = raw;
  
  CAPABILITY char* raw_data = CHERI_SAFE_MALLOC(char, raw);
  for (int i = 0; i < raw; i++) {
    CHERI_CHECK_BOUNDS(raw_data + i, 1);
    raw_data[i] = ' ' + (rnd->next(rnd) % (95));
  }
  
  CAPABILITY char* dst = CHERI_SAFE_MALLOC(char, len);
  int pos = 0;
  while (pos < len) {
    CHERI_CHECK_BOUNDS(raw_data, raw);
    CHERI_CHECK_BOUNDS(dst + pos, raw);
    memcpy(dst + pos, raw_data, raw);
    pos += raw;
  }
  dst[len - 1] = ' ';
  
  free(raw_data);
  return dst;
}

/*
 * https://github.com/google/leveldb/blob/master/util/random.h
 */
void rand_init(Random* rand_, uint32_t s) {
  rand_->seed_ = s & 0x7fffffffu;
  /* Avoid bad seeds. */
  if (rand_->seed_ == 0 || rand_->seed_ == 2147483647L) {
    rand_->seed_ = 1;
  }
  rand_->next = rand_next;  // Set the function pointer
}

uint32_t rand_next(Random* rand_) {
  static const uint32_t M = 2147483647L;
  static const uint64_t A = 16807;

  uint64_t product = rand_->seed_ * A;

  rand_->seed_ = (uint32_t)((product >> 31) + (product & M));

  if (rand_->seed_ > M) {
    rand_->seed_ -= M;
  }

  return rand_->seed_;
}

uint32_t rand_uniform(Random* rand_, int n) { return rand_next(rand_) % n; }

void rand_gen_init(RandomGenerator* gen_, const char* data_, size_t data_size_) {
  if (gen_ == NULL || data_ == NULL) {
    return;
  }
  
  CHERI_CHECK_BOUNDS(gen_, sizeof(RandomGenerator));
  CHERI_CHECK_BOUNDS(data_, data_size_);
  
  gen_->data_ = CHERI_SAFE_MALLOC(char, data_size_);
  CHERI_CHECK_BOUNDS(gen_->data_, data_size_);
  CHERI_CHECK_BOUNDS(data_, data_size_);
  memcpy(gen_->data_, data_, data_size_);
  gen_->data_size_ = data_size_;
  gen_->pos_ = 0;
}

CAPABILITY char* rand_gen_generate(CAPABILITY RandomGenerator* gen_, int len) {
  if (gen_ == NULL || gen_->data_ == NULL || len < 0) {
    return NULL;
  }
  
  CHERI_CHECK_BOUNDS(gen_, sizeof(RandomGenerator));
  CHERI_CHECK_BOUNDS(gen_->data_, gen_->data_size_);
  
  CAPABILITY char* substr = CHERI_SAFE_MALLOC(char, len + 1);
  for (int i = 0; i < len; i++) {
    CHERI_CHECK_BOUNDS(gen_->data_ + gen_->pos_, 1);
    CHERI_CHECK_BOUNDS(substr + i, 1);
    substr[i] = gen_->data_[gen_->pos_];
    gen_->pos_ = (gen_->pos_ + 1) % gen_->data_size_;
  }
  substr[len] = '\0';
  
  return substr;
}
