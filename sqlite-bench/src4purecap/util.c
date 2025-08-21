// Copyright (c) 2011 The LevelDB Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file. See the AUTHORS file for names of contributors.

#include "bench.h"

uint64_t now_micros() {
  struct timeval tv;
  gettimeofday(&tv, NULL);

  return (uint64_t)(tv.tv_sec * 1000000 + tv.tv_usec);
}

/*
 * https://stackoverflow.com/questions/4770985/how-to-check-if-a-string-starts-with-another-string-in-c 
 */
bool starts_with(const char* str, const char* pre) {
  if (str == NULL || pre == NULL) {
    return false;
  }
  
  CHERI_CHECK_BOUNDS(str, 1);
  CHERI_CHECK_BOUNDS(pre, 1);
  
  size_t lenpre = strlen(pre);
  size_t lenstr = strlen(str);
  
  CHERI_CHECK_BOUNDS(str, lenstr + 1);
  CHERI_CHECK_BOUNDS(pre, lenpre + 1);

  return lenstr < lenpre ? false : !strncmp(pre, str, lenpre);
}

char* trim_space(const char* s) {
  if (s == NULL) {
    return NULL;
  }
  
  CHERI_CHECK_BOUNDS(s, 1);
  size_t len = strlen(s);
  CHERI_CHECK_BOUNDS(s, len + 1);

  size_t start = 0;
  while (start < len && isspace(s[start])) {
    start++;
  }
  
  size_t limit = len;
  while (limit > start && isspace(s[limit - 1])) {
    limit--;
  }

  size_t new_len = limit - start;
  char* res = CHERI_SAFE_CALLOC(char, new_len + 1);
  
  if (new_len > 0) {
    CHERI_CHECK_BOUNDS(s + start, new_len);
    CHERI_CHECK_BOUNDS(res, new_len);
    memcpy(res, s + start, new_len);
  }
  res[new_len] = '\0';

  return res;
}
