// Copyright (c) 2011 The LevelDB Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file. See the AUTHORS file for names of contributors.

#include "bench.h"

static void raw_calloc(Raw *raw_) {
  if (raw_ == NULL) {
    return;
  }
  
  CHERI_CHECK_BOUNDS(raw_, sizeof(Raw));
  
  raw_->data_size_ = kNumData;
  raw_->data_ = CHERI_SAFE_CALLOC(double, raw_->data_size_);
  raw_->pos_ = 0;
}

static void raw_realloc(Raw *raw_) {
  if (raw_ == NULL || raw_->data_ == NULL) {
    return;
  }
  
  CHERI_CHECK_BOUNDS(raw_, sizeof(Raw));
  CHERI_CHECK_BOUNDS(raw_->data_, raw_->data_size_ * sizeof(double));
  
  size_t new_size = raw_->data_size_ * 2;
  double* new_data = CHERI_SAFE_REALLOC(raw_->data_, double, new_size);
  
  raw_->data_ = new_data;
  raw_->data_size_ = new_size;
}

void raw_clear(Raw *raw_) {
  if (raw_ == NULL) {
    return;
  }
  
  CHERI_CHECK_BOUNDS(raw_, sizeof(Raw));
  
  if (raw_->data_) {
    CHERI_CHECK_BOUNDS(raw_->data_, raw_->data_size_ * sizeof(double));
    free(raw_->data_);
  }
  raw_calloc(raw_);
}

void raw_add(Raw *raw_, double value) {
  if (raw_ == NULL) {
    return;
  }
  
  CHERI_CHECK_BOUNDS(raw_, sizeof(Raw));
  
  if (!raw_->data_) {
    raw_calloc(raw_);
  }
  
  if (raw_->data_size_ <= raw_->pos_) {
    raw_realloc(raw_);
    if (!raw_->data_) {
      return;
    }
  }
  
  CHERI_CHECK_BOUNDS(raw_->data_ + raw_->pos_, sizeof(double));
  raw_->data_[raw_->pos_] = value;
  raw_->pos_++;
}

char* raw_to_string(Raw *raw_) {
  if (raw_ == NULL) {
    return NULL;
  }
  
  CHERI_CHECK_BOUNDS(raw_, sizeof(Raw));
  
  if (!raw_->data_) {
    raw_calloc(raw_);
  }
  
  if (!raw_->data_) {
    return NULL;
  }
  
  CHERI_CHECK_BOUNDS(raw_->data_, raw_->data_size_ * sizeof(double));
  
  size_t r_size = 1024;
  char *r = CHERI_SAFE_MALLOC(char, r_size);
  r[0] = '\0';
  
  char buf[MAX_BUF_LEN];
  
  for (int i = 0; i < raw_->pos_; i++) {
    CHERI_CHECK_BOUNDS(raw_->data_ + i, sizeof(double));
    int written = snprintf(buf, sizeof(buf), "%.4f\n", raw_->data_[i]);
    if (written < 0 || (size_t)written >= sizeof(buf)) {
      free(r);
      return NULL;
    }
    
    CHERI_CHECK_BOUNDS(buf, written + 1);
    
    if (r_size <= strlen(r) + strlen(buf)) {
      size_t new_size = r_size * 2;
      char* new_r = CHERI_SAFE_REALLOC(r, char, new_size);
      r = new_r;
      r_size = new_size;
    }
    
    CHERI_CHECK_BOUNDS(r, strlen(r) + strlen(buf) + 1);
    strcat(r, buf);
  }
  
  return r;
}

void raw_print(FILE *stream, Raw *raw_) {
  if (raw_ == NULL || stream == NULL) {
    return;
  }
  
  CHERI_CHECK_BOUNDS(raw_, sizeof(Raw));
  
  if (!raw_->data_) {
    raw_calloc(raw_);
  }
  
  if (!raw_->data_) {
    return;
  }
  
  CHERI_CHECK_BOUNDS(raw_->data_, raw_->data_size_ * sizeof(double));
  
  fprintf(stream, "num,time\n");
  for (int i = 0; i < raw_->pos_; i++) {
    CHERI_CHECK_BOUNDS(raw_->data_ + i, sizeof(double));
    fprintf(stream, "%d,%.4f\n", i, raw_->data_[i]);
  }
}
