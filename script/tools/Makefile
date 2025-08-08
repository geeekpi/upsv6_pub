# Compiler
CC = gcc
CFLAGS = -O0
LIBS = -li2c -lcrypto
TARGETS = read_device firmware_uploader

all: check_deps $(TARGETS)

check_deps:
	@for pkg in libi2c-dev libssl-dev; do \
		if ! dpkg -l | grep -q $${pkg}; then \
			echo "Installing $${pkg}..."; \
			sudo apt-get install -y $${pkg}; \
		fi \
	done

# 统一用 $(LIBS) 链接所有目标
$(TARGETS): %: %.c
	$(CC) $(CFLAGS) $< -o $@ $(LIBS)

clean:
	rm -f $(TARGETS)

.PHONY: all check_deps clean
