# 52Pi UPS Gen 6 Battery Monitor

## Overview

This script monitors the battery voltage and current of a 52Pi UPS V6 device via I2C communication. It automatically triggers a system shutdown when the battery voltage drops below a critical threshold to prevent data loss.

---

## Dependencies

```python
from smbus2 import SMBus      # I2C communication library
import time                   # Time delays
import subprocess             # System command execution
import logging                # Event logging
```

---

## Configuration Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `LOG_FILE` | `"/var/log/battery_monitor.log"` | Path to log file |
| `DEVICE_ADDRESS` | `0x17` | I2C device address of the UPS |
| `BATTERY_VOLTAGE_REG` | `0x12` | Register address for battery voltage |
| `BATTERY_CURRENT_REG` | `0x1A` | Register address for battery current |
| `INPUT_VOLTAGE_REG` | `0x10` | Register address for input/charger voltage |
| `INPUT_CURRENT_REG` | `0x18` | Register address for input/charger current |
| `BATTERY_VOLTAGE_THRESHOLD` | `3700` | Minimum voltage per cell in mV |
| `SHUTDOWN_COMMAND` | `"sudo sync ; sudo init 0"` | System shutdown command |

---

## Core Functions

### `read_word_register(register_address)`

Reads a 16-bit signed value from the specified I2C register.

**Parameters:**
- `register_address` — The I2C register to read from

**Returns:** Signed 16-bit integer value

**Logic:**
- Reads word data from device at `DEVICE_ADDRESS`
- Converts unsigned 16-bit to signed (values > 32767 are adjusted by subtracting 65536)

---

### `read_battery_status()`

Retrieves current battery voltage and current readings.

**Returns:** Tuple of `(battery_voltage, battery_current)` in mV and mA

---

### `read_input_status()`

Retrieves charger/input voltage and current readings.

**Returns:** Tuple of `(input_voltage, input_current)` in mV and mA

---

### `check_battery_status()`

Main monitoring logic that checks battery health and triggers shutdown if necessary.

**Algorithm:**

1. **Initial Read** — Read battery and input status, log values
2. **Threshold Check** — Compare `battery_voltage` against `BATTERY_VOLTAGE_THRESHOLD * 2` (accounts for 2 series cells)
3. **Verification Loop** — If below threshold:
   - Enter retry loop (3 attempts)
   - Re-read voltage each second
   - Increment `badBattery` counter if still low
   - Reset and abort if voltage recovers
4. **Shutdown Decision** — If `badBattery > 0` after verification, execute `SHUTDOWN_COMMAND`

---

### `main()`

Infinite monitoring loop with 60-second intervals.

**Behavior:**
- Runs `check_battery_status()` every 60 seconds
- Graceful exit on `KeyboardInterrupt` (Ctrl+C)
- Ensures I2C bus cleanup via `finally` block

---

## Execution Flow

```
┌─────────────────┐
│   Initialize    │
│   SMBus(1)      │
└────────┬────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Read Battery &  │────▶│  Log Readings   │
│ Input Status    │     └─────────────────┘
└─────────────────┘                │
         │                         ▼
         │              ┌─────────────────┐
         │              │ Voltage < 7400? │
         │              │ (3700 × 2)      │
         │              └─────────────────┘
         │                         │
    No ──┴─────────────────────────┘
         │ Yes
         ▼
┌─────────────────┐
│ Retry 3 Times   │
│ (1s intervals)  │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌─────────┐
│ Still │ │ Recovers│
│ Low   │ │         │
└───┬───┘ └───┬─────┘
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│Shutdown │ │ Continue│
│ Initiated│ │ Loop   │
└─────────┘ └─────────┘
```

---

## Usage

```bash
sudo python3 battery_monitor.py
```

**Note:** Requires root privileges for I2C access and shutdown command execution.

---

## Logging Format

```
2024-01-15 14:30:45,123 - Battery Voltage: 7500 mV, Current: 500 mA -- Input Voltage: 5200 mV, Current: 1000 mA.
2024-01-15 14:30:45,124 - Battery voltage 3650 mV is below 3700 mV. Checking again...
2024-01-15 14:30:46,125 - Battery voltage 3640 mV is still below 3700 mV - badBat = 1
2024-01-15 14:30:47,126 - Battery voltage 3630 mV is still below 3700 mV - badBat = 2
2024-01-15 14:30:48,127 - Battery voltage 3620 mV is still below 3700 mV - badBat = 3
2024-01-15 14:30:48,128 - Battery voltage 3620 mV is below 3700 mV. Initiating shutdown.
```
