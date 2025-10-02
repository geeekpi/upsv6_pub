import smbus2
import struct
from typing import NamedTuple
from dataclasses import dataclass

# Device configuration
I2C_DEV = 3  # /dev/i2c-3
I2C_ADDR = 0x17


@dataclass
class DeviceStatus:
    # Define the fields corresponding to the C structure
    WHO_AM_I: int  # Fixed to 0xA6
    version: int  # Version number (read-only)
    uuid0: int  # Unique ID
    uuid1: int
    uuid2: int

    output_voltage: int  # Output voltage (5V)
    input_voltage: int  # Input voltage
    battery_voltage: int  # Battery voltage
    mcu_voltage: int  # MCU voltage
    output_current: int  # Output current (5V)
    input_current: int  # Input current
    battery_current: int  # Battery current (negative value indicates consumption, positive value indicates charging)
    temperature: int  # Temperature

    cr1: int  # Control register 1
    cr2: int  # Control register 2

    sr1: int  # Status register 1
    sr2: int  # Status register 2

    battery_protection_voltage: int  # Battery protection voltage
    shutdown_countdown: int  # Shutdown countdown
    auto_start_voltage: int  # Battery voltage threshold for auto-start on incoming calls
    pika_output_len: int  # Python output buffer size
    ota_request: int  # Request OTA
    runtime: int  # Cumulative runtime time
    charge_detect_interval_s: int  # Charging chip trigger interval
    led_ctl: int  # LED control


def debug_print(status: DeviceStatus):
    """Print device status information"""
    print("🌟 Read device status information 🌟\n")

    # Print each field
    print(f"WHO_AM_I: 0x{status.WHO_AM_I:02X}")
    print(f"Version number: 0x{status.version:02X}")
    print(f"UUID: 0x{status.uuid0:08X} 0x{status.uuid1:08X} 0x{status.uuid2:08X}")
    print(f"Output voltage: {status.output_voltage} mV")
    print(f"Input voltage: {status.input_voltage} mV")
    print(f"Battery voltage: {status.battery_voltage} mV")
    print(f"MCU voltage: {status.mcu_voltage} mV")
    print(f"Output current: {status.output_current} mA")
    print(f"Input current: {status.input_current} mA")
    print(f"Battery current: {status.battery_current} mA")
    print(f"Temperature: {status.temperature} °C")

    print(f"Control register 1 (cr1): 0x{status.cr1:02X}")
    print(f"Incoming call auto-start mode: {(status.cr1 >> 0) & 1}")
    print(f"Loading Python code: {(status.cr1 >> 1) & 1}")
    print(f"Running Python code: {(status.cr1 >> 2) & 1}")
    print(f"Reading Python output log: {(status.cr1 >> 3) & 1}")
    print(f"Reserved for future use: {(status.cr1 >> 4) & 0xF}")

    print(f"Control register 2 (cr2): 0x{status.cr2:02X}")

    print(f"Status register 1 (sr1): 0x{status.sr1:02X}")
    print(f"5V output status : {'On' if (status.sr1 >> 0) & 1 else 'Off'}")
    print(
        f" Fast charge mode: {'Slow charge' if (status.sr1 >> 1) & 1 else 'Fast charge'}"
    )
    print(f" Charging status: {'Discharging' if (status.sr1 >> 2) & 1 else 'Charging'}")
    print(f" Input voltage low: {'Low' if (status.sr1 >> 3) & 1 else 'Normal'}")
    print(f" Output voltage low: {'Low' if (status.sr1 >> 4) & 1 else 'Normal'}")
    print(f" Battery voltage low: {'Low' if (status.sr1 >> 5) & 1 else 'Normal'}")
    print(f" ADC error: {'Yes' if (status.sr1 >> 6) & 1 else 'Normal'}")
    print(f"Battery failure: {'Yes' if (status.sr1 >> 7) & 1 else 'No'}")

    print(f"Status register 2 (sr2): 0x{status.sr2:02X}")
    print(f"Python code too large: {'Yes' if (status.sr2 >> 0) & 1 else 'No'}")

    print(f"Battery protection voltage: {status.battery_protection_voltage} mV")
    print(f"Shutdown countdown: {status.shutdown_countdown} s")
    print(
        f"Incoming call auto-start battery voltage threshold: {status.auto_start_voltage} mV"
    )
    print(f"Python output buffer size: {status.pika_output_len} B")
    print(f"OTA request: 0x{status.ota_request:04X}")
    print(f"Cumulative running time: {status.runtime} milliseconds")
    print(f"Charging chip trigger interval: {status.charge_detect_interval_s} seconds")
    print(f"LED control: 0x{status.led_ctl:02X}")

    print("LED status analysis")
    # LED control analysis
    print(f" Turns on when I2C communication occurs: {(status.led_ctl >> 0) & 1}")
    print(f" Turns on when the battery is charging: {(status.led_ctl >> 1) & 1}")
    print(f" Turns on when the battery is discharging: {(status.led_ctl >> 2) & 1}")
    print(f" Turns on when a fault occurs: {(status.led_ctl >> 3) & 1}")
    print(
        f" Turns on when the device is operating normally: {(status.led_ctl >> 4) & 1}"
    )


def read_device_status() -> DeviceStatus:
    """Read device status"""
    # Define structure format (little endian, consistent with C structure)
    # B: uint8_t, H: uint16_t, I: uint32_t, Q: uint64_t, h: int16_t, b: int8_t
    fmt = "<"  # Little endian
    fmt += "B"  # WHO_AM_I
    fmt += "B"  # version
    fmt += "III"  # uuid0-2
    fmt += "HHHHHH"  # output_voltage, input_voltage, battery_voltage, mcu_voltage, output_current, input_current
    fmt += "h"  # battery_current
    fmt += "b"  # temperature
    fmt += "BB"  # cr1, cr2
    fmt += "BB"  # sr1, sr2
    fmt += "HHHHH"  # battery_protection_voltage, shutdown_countdown, auto_start_voltage, pika_output_len, ota_request
    fmt += "Q"  # runtime
    fmt += "H"  # charge_detect_interval_s
    fmt += "B"  # led_ctl

    # Calculate structure size
    struct_size = struct.calcsize(fmt)
    print(f"Structure size: {struct_size} bytes")

    # Initialize the I2C bus
    bus = smbus2.SMBus(I2C_DEV)

    # Read data in multiple passes, up to 32 bytes each
    data = bytearray()
    for offset in range(0, struct_size, 32):
        # Calculate the length of this read
        read_len = min(32, struct_size - offset)

        try:
            # Read block data using SMBus
            block_data = bus.read_i2c_block_data(I2C_ADDR, offset, read_len)

            # Add to data buffer
            data.extend(block_data)
            print(f"📝 Read data from address 0x{offset:02X}: {len(block_data)} bytes")
        except Exception as e:
            print(f"❌ Error reading address 0x{offset:02X}: {e}")
            # Pad with zeros to ensure data length is correct
            data.extend(bytes([0] * read_len))

    # Check data length is correct
    if len(data) < struct_size:
        print(
            f"⚠️ Insufficient data, expected {struct_size} bytes, received {len(data)} bytes"
        )
        # Pad with zeros
        data.extend(bytes([0] * (struct_size - len(data))))

    # Unpack data into a structure
    try:
        unpacked = struct.unpack(fmt, data[:struct_size])
        return DeviceStatus(*unpacked)
    except Exception as e:
        print(f"❌ Error unpacking data: {e}")
        print(f"Data length: {len(data)} bytes")
        print(f"Format string: {fmt} (expected {struct_size} bytes)")
        raise


if __name__ == "__main__":
    print("🔄 Start reading device data...")
    try:
        status = read_device_status()
        debug_print(status)
    except Exception as e:
        print(f"❌ Error reading device data: {e}")
