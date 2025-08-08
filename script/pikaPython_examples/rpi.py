#!/usr/bin/env python3
import smbus
import time
import os
import sys
import argparse

# Device constants 📟
DEVICE_ADDR = 0x17
PIKA_PUSH_REG = 58
PIKA_CODE_PTR_REG = 54
PIKA_POP_REG = 59
PIKA_PUTS_PTR_REG = 56
CR1_REG_ADDR = 0x1D
PYTHON_EXEC_BIT = 2

# Default retry settings 🔁
DEFAULT_MAX_RETRY = 30
DEFAULT_RETRY_DELAY_MS = 10  # Default delay in milliseconds
MIN_RETRY_DELAY_MS = 1       # Minimum delay

def set_bit(value, bit):
    return value | (1 << bit)

def clear_bit(value, bit):
    return value & ~(1 << bit)

def check_bit(value, bit):
    return (value >> bit) & 1

class RetryConfig:
    def __init__(self, max_retry=DEFAULT_MAX_RETRY, retry_delay_ms=DEFAULT_RETRY_DELAY_MS):
        self.max_retry = max(max_retry, 1)
        self.retry_delay = max(retry_delay_ms / 1000.0, MIN_RETRY_DELAY_MS / 1000.0)  # Convert to seconds
        self.max_sub_retry = max(max_retry // 10, 1)

def read_byte_data_with_retry(bus, address, register, retry_config):
    last_exception = None
    for attempt in range(retry_config.max_retry):
        try:
            return bus.read_byte_data(address, register)
        except Exception as e:
            last_exception = e
            print(f"[WARN] Read attempt {attempt + 1} failed 🚫 Retrying...")
            time.sleep(retry_config.retry_delay)
    raise last_exception  # Raise last exception after retries

def write_byte_with_retry(bus, addr, reg, value, retry_config, byte=True, readback=0):
    """Write byte or word with retries and optional read-back check"""
    retry_count = 0
    while retry_count < retry_config.max_retry:
        try:
            if byte:
                bus.write_byte_data(addr, reg, value)
            else:
                bus.write_word_data(addr, reg, value)

            for _ in range(retry_config.max_sub_retry):
                if byte:
                    read_value = bus.read_byte_data(addr, reg)
                else:
                    read_value = bus.read_word_data(addr, reg)

                if read_value == readback:
                    return True  # Success ✅
                time.sleep(retry_config.retry_delay)

            print(f"[WARN] Read-back mismatch after write, retrying... 🔄")
            retry_count += 1
            time.sleep(retry_config.retry_delay)

        except Exception as e:
            retry_count += 1
            print(f"[ERROR] Write attempt {retry_count} failed: {e}")
            time.sleep(retry_config.retry_delay)
            if retry_count >= retry_config.max_retry:
                raise e
    return False  # All retries failed ❌

def upload_and_execute(bus, filename, retry_config):
    """ Upload and execute file on the device"""
    if os.path.getsize(filename) > 4096:
        print("❌ Error: File size exceeds 4096 bytes!")
        sys.exit(1)

    try:
        who_am_i = bus.read_byte_data(DEVICE_ADDR, 0x00)
        if who_am_i != 0xA6:
            print(f"🚨 Device verification failed! Got 0x{who_am_i:02X}, expected 0xA6")
            sys.exit(1)

        print("✅ Device verified successfully!")

        with open(filename, "rb") as f:
            data = f.read()

        print(f"📤 Starting upload of {len(data)} bytes...")

        for idx, byte in enumerate(data):
            try:
                write_byte_with_retry(bus, DEVICE_ADDR, PIKA_PUSH_REG, byte, retry_config, readback=byte)
                ptr_value = idx | 0x8000
                readback_value = (~ptr_value) & 0x7FFF  # 取反并确保最高位为0
                write_byte_with_retry(bus, DEVICE_ADDR, PIKA_CODE_PTR_REG, ptr_value, retry_config, byte=False, readback=readback_value)
                print(f"🟢 Uploaded byte {idx+1}/{len(data)}", end='\r')
            except Exception as e:
                print(f"\n❌ Upload failed at byte {idx}: {e}")
                sys.exit(1)

        print(f"\n🎉 Upload complete: {len(data)} bytes transferred.")

        old_cr1 = bus.read_byte_data(DEVICE_ADDR, CR1_REG_ADDR)
        print(f"[INFO] Current CR1 = 0x{old_cr1:02X} 🧾")

        new_cr1 = set_bit(old_cr1, PYTHON_EXEC_BIT)
        print(f"[INFO] New CR1 (with exec bit set) = 0x{new_cr1:02X} ⚙️")

        success = write_byte_with_retry(bus, DEVICE_ADDR, CR1_REG_ADDR, new_cr1, retry_config, byte=True, readback=old_cr1)
        if not success:
            print("❗ CR1 write failed — auto-clear check failed ❌")
            return False

        print("🚀 Upload and execution triggered successfully!")

    except Exception as e:
        print(f"💥 Fatal error during upload and execute: {str(e)}")
        sys.exit(1)

def read_output(bus, retry_config):
    """Read output from the device after execution"""
    try:
        who_am_i = read_byte_data_with_retry(bus, DEVICE_ADDR, 0x00, retry_config)
        if who_am_i != 0xA6:
            raise ValueError(f"❌ WHO_AM_I mismatch: expected 0xA6, got 0x{who_am_i:02X}")

        output_len = bus.read_word_data(DEVICE_ADDR, 0x27)
        print(f"📝 Output length: {output_len} bytes")

        if output_len == 0:
            print("📭 No data to read.")
            return

        result = bytearray()
        for idx in range(output_len):
            ptr_value = idx | 0x8000
            readback_value = (~ptr_value) & 0x7FFF  # 取反并确保最高位为0
            if not write_byte_with_retry(bus, DEVICE_ADDR, PIKA_PUTS_PTR_REG, ptr_value, retry_config, byte=False, readback=readback_value):
                raise RuntimeError(f"❌ Failed to set output pointer to 0x{ptr_value:04X}")
            result.append(read_byte_data_with_retry(bus, DEVICE_ADDR, PIKA_POP_REG, retry_config))

        # Clear buffer
        if not write_byte_with_retry(bus, DEVICE_ADDR, PIKA_PUTS_PTR_REG, 0xFFFF, retry_config, byte=False, readback=0x00AA):
            raise RuntimeError("❌ Failed to clear output buffer")

        print("📤 Device output:\n" + ''.join(chr(b) for b in result))

    except Exception as e:
        print(f"⚠️ Error while reading output: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='🧪 Communication tool for I2C devices')
    parser.add_argument('-u', '--upload', metavar='FILE', help='📤 Upload and execute specified binary file')
    parser.add_argument('-r', '--read', action='store_true', help='📥 Read output from device')
    parser.add_argument('--max-retry', type=int, default=DEFAULT_MAX_RETRY, help=f'Max retry attempts (default: {DEFAULT_MAX_RETRY})')
    parser.add_argument('--retry-delay', type=int, default=DEFAULT_RETRY_DELAY_MS, help=f'Retry delay in ms (min {MIN_RETRY_DELAY_MS}, default {DEFAULT_RETRY_DELAY_MS})')

    args = parser.parse_args()

    if not args.upload and not args.read:
        parser.print_help()
        sys.exit(1)

    args.max_retry = max(args.max_retry, 1)
    args.retry_delay = max(args.retry_delay, MIN_RETRY_DELAY_MS)
    retry_config = RetryConfig(args.max_retry, args.retry_delay)

    print(f"⚙️ Retry settings: max={retry_config.max_retry}, sub={retry_config.max_sub_retry}, delay={retry_config.retry_delay*1000:.1f}ms")

    bus = smbus.SMBus(1)
    try:
        if args.upload:
            upload_and_execute(bus, args.upload, retry_config)
        if args.read:
            read_output(bus, retry_config)
    finally:
        bus.close()

if __name__ == "__main__":
    main()
