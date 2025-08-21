PREFIX?=/home/iiswc/workspace/sqlite-bench/build
OBJDIR=$(PREFIX)

SRCS=$(wildcard *.c)
OBJS=$(SRCS:%.c=$(OBJDIR)/%.o)
HDRS=$(wildcard *.h)
TARGET=sqlite-bench

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	LDFLAGS=-lpthread -ldl -lm $(CFLAGS)
else
	LDFLAGS=-lpthread -ldl -lm -static $(CFLAGS)
endif


$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o ${PREFIX}/$(TARGET) $(LDFLAGS)

$(OBJDIR)/%.o: %.c | $(OBJDIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJS): $(HDRS)

bench: $(TARGET) clean-db
	${PREFIX}/$(TARGET)

clean:
	rm -f $(OBJDIR)/*.o

clean-db:
	rm -f dbbench_sqlite3*

$(OBJDIR):
	mkdir -p $(OBJDIR)

.PHONY: bench clean clean-db
