CC=gcc
CFLAGS=-Wall -Wextra -fPIC $(shell python3-config --cflags)
LDFLAGS=-shared $(shell python3-config --ldflags --embed 2>/dev/null || python3-config --ldflags)

# OS specific shared library extension
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	SHARED_EXT=dylib
else
	SHARED_EXT=so
endif

LIBRARY=libsolder_defect.$(SHARED_EXT)
EXAMPLE=example
PROJECT_ROOT=../..

all: $(LIBRARY) $(EXAMPLE)

$(LIBRARY): solder_defect.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

$(EXAMPLE): example.c $(LIBRARY)
	$(CC) -Wall -o $@ $< -L. -lsolder_defect

# Builds the library and runs the Python unit tests for the C bindings.
# Must be run from the project root: make -C src/c_bindings test
test: $(LIBRARY)
	cd $(PROJECT_ROOT) && python3 -m unittest tests.test_c_bindings -v

clean:
	rm -f $(LIBRARY) $(EXAMPLE)

.PHONY: all test clean
