Here is the English version of the markdown documentation based on the wiki content:

---

# SBS Module for UPS Gen 6

**Product SKU**: EP-0256

## Description

The SBS (Smart Battery System) Module is an advanced battery management solution designed specifically for the UPS Gen 6 platform. This module implements the industry-standard SBS communication protocol to provide intelligent monitoring and control of lithium battery packs. By integrating precision analog front-end circuitry with a compliant SBS firmware stack, it delivers real-time battery telemetry including voltage, current, state of charge, and runtime estimation. The module supports I2C communication interfaces compatible with both PikaPython embedded environments and native Raspberry Pi I2C buses, making it versatile for various development scenarios. With open-source firmware architecture, users benefit from transparent battery management algorithms while maintaining flexibility for customization. The module ensures safe and efficient battery operation through balanced charging capabilities and configurable I2C addressing, making it an ideal power management companion for UPS Gen 6 battery expansion boards.

## Features

- **Balanced Charging Protection**: Lithium battery charging incorporates cell balancing functionality to prevent battery damage and extend pack longevity
- **SBS Protocol Compliance**: Device firmware adheres to Smart Battery System (SBS) communication standards for interoperability
- **UPS Gen 6 Compatibility**: Fully compatible with UPS Gen 6 battery expansion boards for seamless integration
- **Flexible I2C Communication**: Supports I2C protocol communication compatible with both PikaPython environments and native Raspberry Pi I2C interfaces for reading battery voltage, current, and status parameters
- **Open-Source Firmware**: SBS firmware is open-source, enabling transparency and customization
- **Enhanced Battery Management**: Provides safer and more convenient battery management capabilities
- **Configurable I2C Address**: I2C communication address selectable via jumper configuration
- **High-Precision Acquisition**: Utilizes high-precision operational amplifiers for voltage and current sensing, delivering accurate readings
- **Intelligent Runtime Estimation**: Smart algorithms estimate remaining battery runtime, providing battery percentage and charge/discharge state indication

## Installation & Setup

### Auto Setup

1. Download the setup shell script from GitHub: [https://github.com/geeekpi/sbs_battery_for_UPS_Gen6](https://github.com/geeekpi/sbs_battery_for_UPS_Gen6)
2. Execute the `setup.sh` shell script

### Quick Start

```bash
# Download the script
curl -O https://example.com/install_sbs_battery.sh
chmod +x install_sbs_battery.sh

# Run full installation
sudo ./install_sbs_battery.sh

# Reboot to activate
sudo reboot

# After reboot, check battery status
batt
```

For more information, please visit: [https://github.com/geeekpi/sbs_battery_for_UPS_Gen6](https://github.com/geeekpi/sbs_battery_for_UPS_Gen6)

---

## Manual Compilation Guide

### Overview

This guide explains how to compile the SBS (Smart Battery System) battery driver as an external kernel module on Raspberry Pi 5, create a Device Tree overlay to instantiate the device, and configure automatic loading at boot time — all without recompiling the entire kernel.

### Prerequisites

- Raspberry Pi 5 (or compatible model, such as Raspberry Pi 4B, etc.)
- Running Raspberry Pi OS with kernel headers installed
- I2C interface enabled
- SBS-compatible battery connected via I2C (default address: `0x0a`)

---

### Part A: Compile External Kernel Module (Out-of-Tree)

#### Step A0: Install Required Kernel Headers

You must install kernel headers that exactly match your running kernel:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y "linux-headers-$(uname -r)"
```

> **Important**: The build directory must be `/lib/modules/$(uname -r)/build`

Verify the kernel build directory:

```bash
KDIR=/lib/modules/$(uname -r)/build
readlink -f "$KDIR"
ls -l "$KDIR"
```

#### Step A1: Obtain Kernel Source Code

Clone the Raspberry Pi Linux repository to extract the `sbs-battery.c` source file:

```bash
git clone --depth=1 -b rpi-6.12.y https://github.com/raspberrypi/linux ~/linux
```

> **Note**: This step is only to obtain the `sbs-battery.c` source file. The actual compilation uses the headers' build tree, so minor version differences between the source tree and your running kernel are generally acceptable. However, API changes may cause compilation failures.

#### Step A2: Create External Module Directory and Makefile

Create a working directory for the external module:

```bash
mkdir -p ~/kmods/sbs
cd ~/kmods/sbs

# Copy the source file from cloned repository
cp ~/linux/drivers/power/supply/sbs-battery.c .

# Create the Makefile
cat > Makefile << 'EOF'
obj-m += sbs-battery.o
EOF
```

#### Step A3: Compile Using Kernel Headers

Compile the module using the kernel headers' build directory:

```bash
KDIR=/lib/modules/$(uname -r)/build

# Clean previous builds
make -C "$KDIR" M="$PWD" clean

# Compile the module
make -C "$KDIR" M="$PWD" modules
```

Expected output files:

- `sbs-battery.ko` — The loadable kernel module
- `Module.symvers` — Module symbol versions
- `modules.order` — Module load order

#### Step A4: Manual Loading Verification

Test the compiled module by manually loading it:

```bash
sudo insmod sbs-battery.ko

# Verify module is loaded
lsmod | grep sbs
```

---

### Part B: Create Device Tree Overlay

#### Step B0: Identify I2C Controller Device Tree Path

Before creating the overlay, you must identify the correct Device Tree path for your I2C controller.

For Raspberry Pi 5, the path is:

```
/axi/pcie@1000120000/rp1/i2c@74000
```

To find the DT path for your specific setup:

```bash
OF=$(readlink -f /sys/class/i2c-dev/i2c-1/device/of_node)
echo "DT_PATH=${OF#/sys/firmware/devicetree/base}"
```

> **Note**: For other Pi models, you will need to determine the appropriate path individually.

#### Step B1: Overlay File Requirements

| Requirement | Specification |
|-------------|---------------|
| Filename suffix | Must end with `-overlay.dts` |
| Source directive | Must include `/plugin/;` |
| DTC flag | Must use `@` flag during compilation |
| Output | `.dtbo` file placed in `/boot/firmware/overlays/` |

#### Step B2: Create Overlay Content

Create the Device Tree overlay file `sbs-battery-overlay.dts`:

```dts
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2712";

    fragment@0 {
        target-path = "/axi/pcie@1000120000/rp1/i2c@74000";

        __overlay__ {
            status = "okay";
            #address-cells = <1>;
            #size-cells = <0>;

            sbs-battery@a {
                compatible = "sbs,sbs-battery";
                reg = <0x0a>;           /* I2C address default is 0x0A */
                status = "okay";
            };
        };
    };
};
```

Address notation explanation:

- `battery@a` — Node name (hexadecimal without prefix, following DT convention)
- `reg = <0x0a>` — Actual I2C device address (`0x0a` = 10 in decimal)

It is recommended to keep the node name consistent with the `reg` value for clarity.

#### Step B3: Compile and Install Overlay

Compile the Device Tree overlay:

```bash
dtc -@ -I dts -O dtb -o sbs-battery.dtbo sbs-battery-overlay.dts
```

Install the compiled overlay to the system overlays directory:

```bash
sudo install -D -m 0644 sbs-battery.dtbo /boot/firmware/overlays/
```

#### Step B4: Enable the Overlay

Edit the Raspberry Pi configuration file to enable the overlay:

```bash
sudo nano /boot/firmware/config.txt
```

Add the following line in the `[all]` section (or appropriate section):

```ini
[all]
dtoverlay=sbs-battery
```

---

### Part C: Configure Automatic Module Loading

#### Step C1: Install Module to Standard Path

Install the compiled module to the standard kernel modules directory and update dependencies:

```bash
# Install module to extra directory
sudo install -D -m 0644 ~/kmods/sbs/sbs-battery.ko \
    /lib/modules/$(uname -r)/extra/sbs-battery.ko

# Update module dependencies
sudo depmod -a
```

> **Recommendation**: If you previously loaded the module manually with `insmod`, remove it first to ensure clean verification of automatic loading:
> ```bash
> sudo rmmod sbs-battery
> ```

#### Step C2: Reboot and Verify

Reboot the system to test automatic loading:

```bash
sudo reboot
```

After reboot, verify the module loaded automatically:

```bash
# Check if module is loaded
lsmod | grep sbs

# Check kernel messages for SBS/battery related logs
dmesg | grep -i -E 'sbs|battery|power_supply'

# Check power supply class devices
ls /sys/class/power_supply/

# Verify I2C device detection (should show 1-000a for I2C bus 1, address 0x0a)
ls /sys/bus/i2c/devices | grep '1-000a'
```

---

## Battery Status Queries

### upower Command Reference

#### Enumerate Power Devices

```bash
upower -e
```

Purpose: Lists all power device paths recognized by the UPower daemon.

#### Inspect Device Information

```bash
upower -i /org/freedesktop/UPower/devices/battery_sbs_1_000a
```

### Quick Status Scripts

#### Essential Info Only (Panel/Conky Friendly)

```bash
upower -i $(upower -e | grep battery) | grep -E "state|percentage|time to|energy-rate|temperature"
```

#### Custom Battery Info Script

```bash
cat > ~/.local/bin/batt << 'EOF'
#!/bin/bash
DEVICE="/org/freedesktop/UPower/devices/battery_sbs_1_000a"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get data
RAW=$(upower -i "$DEVICE")
STATE=$(echo "$RAW" | grep "state:" | awk '{print $2}')
PERCENT=$(echo "$RAW" | grep "percentage:" | awk '{print $2}' | tr -d '%')
VOLTAGE=$(echo "$RAW" | grep "voltage:" | awk '{print $2}')
TEMP=$(echo "$RAW" | grep "temperature:" | awk '{print $2 " " $3}')
POWER=$(echo "$RAW" | grep "energy-rate:" | awk '{print $2 " " $3}')
ENERGY=$(echo "$RAW" | grep "energy:" | awk '{print $2 " " $3}')

# State color
case "$STATE" in
    charging) COLOR=$GREEN; ICON="🔌" ;;
    discharging) COLOR=$YELLOW; ICON="🔋" ;;
    fully-charged) COLOR=$GREEN; ICON="⚡" ;;
    *) COLOR=$NC; ICON="❓" ;;
esac

# Output
echo -e "${COLOR}${ICON} 52Pi UPSPack-2S${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "State:       ${COLOR}${STATE}${NC}"
echo "Level:       ${PERCENT}%"
echo "Voltage:     ${VOLTAGE}V"
echo "Power:       ${POWER}"
echo "Energy:      ${ENERGY}"
echo "Temp:        ${TEMP}"
echo ""
echo "Device:      sbs-1-000a (I2C 0x0a)"
EOF

chmod +x ~/.local/bin/batt
```

Usage:

```bash
batt
```

#### Mini Monitor (Auto-Refresh)

```bash
# Watch live (updates every 2 seconds)
watch -n 2 'upower -i /org/freedesktop/UPower/devices/battery_sbs_1_000a | grep -E "state|percentage|voltage|temp|energy-rate"'
```

---
