# 52Pi UPS V6 User Manual  

## Description of the I2C Data Reading Script

This Python script is designed to read and display data from an I2C device (specifically a 52Pi UPS V6) using the `smbus2` library. It continuously reads various registers from the device and prints the raw data to the console, formatted with ANSI colors for better readability.

## Features
- **Device Communication**: Communicates with the I2C device at address `0x17` using the I2C bus number `1`.
- **Register Reading**: Supports reading 8-bit, 16-bit, and 32-bit registers.
- **Data Formatting**: Formats and prints the data with appropriate units (e.g., mV for voltage, mA for current, ℃ for temperature).
- **Continuous Output**: Continuously reads and displays data every 2 seconds until interrupted by the user.
- **Graceful Shutdown**: Closes the I2C bus connection when interrupted by a keyboard interrupt (Ctrl+C).

## Register Definitions
- **WHO_AM_I**: Fixed register value (`0xA6`) for device identification.
- **VERSION**: Device version information.
- **UID0, UID1, UID2**: Unique device identifiers (32-bit each).
- **OUTPUT_VOLTAGE, INPUT_VOLTAGE, BATTERY_VOLTAGE, MCU_VOLTAGE**: Voltage readings in millivolts.
- **OUTPUT_CURRENT, INPUT_CURRENT, BATTERY_CURRENT**: Current readings in milliamps.
- **TEMPERATURE**: Temperature reading in degrees Celsius.

## Functions
- **read_byte_register**: Reads an 8-bit register value.
- **read_word_register**: Reads a 16-bit register value.
- **read_dword_register**: Reads a 32-bit register value.
- **read_all_registers**: Aggregates data from all relevant registers into a dictionary.

## Execution Flow
1. Initializes the I2C bus connection.
2. Continuously reads data from the device registers.
3. Formats and prints the data to the console.
4. Waits for 2 seconds before repeating the process.
5. Closes the I2C bus connection when interrupted by the user.

## Usage
To run this script, ensure you have the `smbus2` library installed and the I2C device connected to the appropriate I2C bus. Execute the script, and it will display the raw data from the device in a formatted manner. Press Ctrl+C to stop the script and close the I2C connection gracefully.

## Install dependencies packages and library
```bash 
sudo apt update 
sudo apt upgrade -y 
sudo apt -y install i2c-tools 
sudo apt -y install virtualenv 
virtualenv -p python3 venv 
cd venv 
source bin/activate 
pip install smbus2 
```

## Output Demo


## About script folder

<pre>
.
├── enable_ota.py
├── encrypt_tool.c
├── examples
│   ├── test_color.py
│   ├── test_drawCircle.py
│   ├── test_drawFastVLine.py
│   ├── test_drawLine.py
│   ├── test_drawPixel.py
│   ├── test_drawRect.py
│   ├── test_drawString.py
│   ├── test_drawTriangle.py
│   ├── test_fillRect.py
│   ├── test_fillScreen.py
│   ├── test_fillTriangle.py
│   └── tfttest.py
├── factory_update.c
├── get_py_output.c
├── main.py
├── Makefile
├── read_device_basic_demo.py
├── read_device.c
├── read_device.py
├── README.md
├── rpi.py
├── upload_pyscript.c
├── upsv6-user-app-demo-code.png
└── user_write_tool.c
</pre>


