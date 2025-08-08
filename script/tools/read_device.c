#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <linux/i2c.h>
#include <string.h>
#include <i2c/smbus.h>

// Device file
#define I2C_DEV "/dev/i2c-1"
#define I2C_ADDR 0x17

// Define the structure
typedef struct __attribute__((packed)) {
    uint8_t WHO_AM_I; // Fixed to 0xA6
    uint8_t version; // Version (Read only)
    uint32_t uuid0; // Universal unique ID
    uint32_t uuid1;
    uint32_t uuid2;

    uint16_t output_voltage; // Output voltage(5V)
    uint16_t input_voltage; // Input voltage
    uint16_t battery_voltage; // Battery Voltage
    uint16_t mcu_voltage; // MCU voltage
    uint16_t output_current; // Output current (5V)
    uint16_t input_current; // Input current
    int16_t battery_current; // Battery current (Negative value is for discharging, positive value is for charging)
    int8_t temperature; // Temperature of MCU

    // cr - control registers
    union {
        struct {
            uint8_t auto_start_mode : 1; // auto start mode
            uint8_t rsv1 : 7; // Reserved
        };
        uint8_t cr1; // Use to access full byte.
    };
    uint8_t cr2; // Reserved Control Register 2

    // sr - status registers
    union {
        struct {
            uint8_t sw_status : 1; // 5V OUTPUT status (0=Off,1=On)
            uint8_t fast : 1; // Fast charging status (0=slow charging/no external power, 1=12V fast charging)
            uint8_t charge : 1; // Charge/discharge status (0=charging, 1=discharging)
            uint8_t input_low : 1; // Input voltage low (0=normal, 1=low)
            uint8_t output_low : 1; // 5V output low (0=normal, 1=low)
            uint8_t battery_low : 1; // Battery voltage low (0=normal, 1=low)
            uint8_t adc_mismatch : 1; // ADC mismatch (0=normal, 1=INA219 vs MCU sampling difference exceeded)
            uint8_t battery_fail : 1; // Battery failure (0=normal, 1=failure)
        };
        uint8_t sr1; // Used to access the entire byte
    };
    union {
        struct {
            uint8_t python_exec_toobig : 1; // Python code is too big
            uint8_t rsv2 : 7; // Reserved
        };
        uint8_t sr2; // Used to access the entire byte
    };

    uint16_t battery_protection_voltage; // Used to setting the battery protection voltage
    uint16_t shutdown_countdown; // Used to setting shutdown countdown in seconds
    uint16_t auto_start_voltage; // Automatic power-on voltage threshold setting for battery
    uint16_t rsv; // Reserved (Read/Write)
    uint16_t ota_request; // OTA request (Write-only)
    uint64_t runtime; // Accumulated operating time
    uint16_t charge_detect_interval_s; // Charging chip trigger interval (seconds, readable and writable).
    union {
        struct {
            uint8_t i2c_ack : 1; // Light up when I2C communication occurs
            uint8_t bat_charge : 1; // Light up when the battery is charging
            uint8_t bat_discharge : 1; // Light up when the battery is discharging
            uint8_t fault_report : 1; // Light up when there is a fault
            uint8_t ok_report : 1; // Light up during normal operation
            uint8_t rsv3 : 3; // Reserved
        };
        uint8_t led_ctl; // Used to access the entire byte
    };
} DeviceStatus;

// Debug print function
void debug_print(DeviceStatus* status) {
    printf("🌟 Read Device Status Information🌟\n");

    // 打印每个字段
    printf("WHO_AM_I:             0x%02X\n", status->WHO_AM_I);
    printf("Version:              0x%02X\n", status->version);
    printf("UUID:                 0x%08X 0x%08X 0x%08X\n", status->uuid0, status->uuid1, status->uuid2);
    printf("Output Voltage:       %u mV\n", status->output_voltage);
    printf("Input Voltage:        %u mV\n", status->input_voltage);
    printf("Battery Voltage:      %u mV\n", status->battery_voltage);
    printf("MCU Voltage:          %u mV\n", status->mcu_voltage);
    printf("Output Current:       %u mA\n", status->output_current);
    printf("Input Current:        %u mA\n", status->input_current);
    printf("Battery Current:      %d mA\n", status->battery_current);
    printf("Temperature:          %d °C\n", status->temperature);

    printf("Control Register 1 (cr1):       0x%02X\n", status->cr1);
    printf("    Power-on auto-start mode :  %d\n", status->auto_start_mode);

    // printf("Control Register 2 (cr2):       0x%02X\n", status->cr2);

    printf("Status Register 1 (sr1):       0x%02X\n", status->sr1);
    printf("    5V Output status     : %s\n", status->sw_status ? "ON" : "OFF");
    printf("    Fast Charge Mode     : %s\n", status->fast ? "Fast Charge" : "Slow Charge/No External Power");
    printf("    Charging Status      : %s\n", status->charge ? "Discharging" : "Charging");
    printf("    Input Voltage Low    : %s\n", status->input_low ? "LOW" : "Normal");
    printf("    Output Voltage LOW   : %s\n", status->output_low ? "LOW" : "Normal");
    printf("    Battery Voltage LOW  : %s\n", status->battery_low ? "LOW" : "Normal");
    printf("    ADC error            : %s\n", status->adc_mismatch ? "YES" : "Normal");
    printf("    Battery failure      : %s\n", status->battery_fail ? "YES" : "NO");

    //printf("Status Register 2 (sr2):       0x%02X\n", status->sr2);
    //printf("    Python Code is too big : %s\n", status->python_exec_toobig ? "YES" : "NO");

    printf("Battery protection voltage : %u mV\n", status->battery_protection_voltage);
    printf("Shutdown Countdown :  %u s\n", status->shutdown_countdown);
    printf("Power-on auto-start battery voltage threshold : %u mV\n", status->auto_start_voltage);
    printf("Reserved Register :    0x%04X\n", status->rsv);
    printf("Request OTA(Over-The-Air update) :   0x%04X\n", status->ota_request);
    printf("Accumulated operating time :  %llu microseconds\n", status->runtime);
    printf("Charging chip trigger interval :     %u seconds\n", status->charge_detect_interval_s);
    printf("LED Control:               0x%02X\n", status->led_ctl);

    printf("LED Status Parsing\n");
    // LED control parsing
    printf("    Light up when I2C communication occurs   : %d\n", status->i2c_ack);
    printf("    Light up when the battery is charging    : %d\n", status->bat_charge);
    printf("    Light up when the battery is discharging : %d\n", status->bat_discharge);
    printf("    Light up when there is a fault           : %d\n", status->fault_report);
    printf("    Light up during normal operation         : %d\n", status->ok_report);
}

int main() {
    int fd;
    DeviceStatus status; // structure of device status storage

    // Open I2C device file
    if ((fd = open(I2C_DEV, O_RDWR)) < 0) {
        perror("Could not open I2C device. ");
        return -1;
    }

    // Setting I2C slave address
    if (ioctl(fd, I2C_SLAVE, I2C_ADDR) < 0) {
        perror("Setting I2C slave failure.");
        close(fd);
        return -1;
    }

    printf("🔄 Start reading device status...\n");

    // Use SMBus read the data multiple times
    for (int offset = 0; offset < sizeof(DeviceStatus); offset += 32) {
        int len = 32;
        if (offset + len > sizeof(DeviceStatus)) {
            len = sizeof(DeviceStatus) - offset; // last part of data
        }

        // Use SMBus to read data
        union i2c_smbus_data data;
        struct i2c_smbus_ioctl_data args = {
            .read_write = I2C_SMBUS_READ,
            .command = offset,
            .size = I2C_SMBUS_I2C_BLOCK_DATA,
            .data = &data
        };

        // Set the number of bytes to read
        data.block[0] = len;

        // Execute SMBus to read data
        if (ioctl(fd, I2C_SMBUS, &args) < 0) {
            perror("SMBus read failed.");
            close(fd);
            return -1;
        }

        // Store reading data to the data structure.
        memcpy((uint8_t*)&status + offset, data.block + 1, len);
        printf("📝 Read from: 0x%02X data size: %d byte\n", offset, len);
    }

    // Print device status
    debug_print(&status);

    // Close I2C device
    close(fd);
    return 0;
}
