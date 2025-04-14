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

// 设备文件
#define I2C_DEV "/dev/i2c-1"
#define I2C_ADDR 0x17

// 结构体定义
typedef struct __attribute__((packed)) {
    uint8_t WHO_AM_I; // 固定为0xA6
    uint8_t version; // 版本号(只读)
    uint32_t uuid0; // 唯一ID
    uint32_t uuid1;
    uint32_t uuid2;

    uint16_t output_voltage; // 输出电压(5V)
    uint16_t input_voltage; // 输入电压
    uint16_t battery_voltage; // 电池电压
    uint16_t mcu_voltage; // MCU电压
    uint16_t output_current; // 输出电流(5V)
    uint16_t input_current; // 输入电流
    int16_t battery_current; // 电池电流(负数为消耗,正数为充电)
    int8_t temperature; // 温度

    // cr - 控制寄存器
    union {
        struct {
            uint8_t auto_start_mode : 1; // 来电自启动模式
            uint8_t python_load : 1; // 加载Python代码
            uint8_t python_exec : 1; // 运行Python代码
            uint8_t python_read_return: 1; // 读取Python输出的日志
            uint8_t rsv1 : 4; // 预留未来
        };
        uint8_t cr1; // 用于访问整个字节
    };
    uint8_t cr2;

    // sr - 状态寄存器
    union {
        struct {
            uint8_t sw_status : 1; // 5V OUTPUT 状态(0=关闭,1=开启)
            uint8_t fast : 1; // 是否处于快充模式(0=12V快充正常,1=慢充/没插入外部电源)
            uint8_t charge : 1; // 是否处于充电状态(0=充电,1=放电)
            uint8_t input_low : 1; // 输入电压低(0=正常,1=低)
            uint8_t output_low : 1; // 5V OUTPUT 低(0=正常,1=低)
            uint8_t battery_low : 1; // 电池电压低(0=正常,1=低)
            uint8_t adc_mismatch : 1; // ADC误差过大 (INA219对比MCU数据) - 由INA219采样时计算
            uint8_t battery_fail : 1; // 电池故障
        };
        uint8_t sr1; // 用于访问整个字节
    };
    union {
        struct {
            uint8_t python_exec_toobig : 1; // Python代码太大了
            uint8_t rsv2 : 7;
        };
        uint8_t sr2; // 用于访问整个字节
    };

    uint16_t battery_protection_voltage; // 电池保护电压
    uint16_t shutdown_countdown; // 关机倒计时
    uint16_t auto_start_voltage; // 来电自启动电池电压阈值
    uint16_t pika_output_len; // Python 输出缓冲大小
    uint16_t ota_request; // 请求OTA
    uint64_t runtime; // 运行累计时间
    uint16_t charge_detect_interval_s; // 充电芯片触发间隔(秒,可读写)
    union {
        struct {
            uint8_t i2c_ack : 1; // 当I2C通信发生时点亮
            uint8_t bat_charge : 1; // 当电池正在充电时点亮
            uint8_t bat_discharge : 1; // 当电池正在放电时点亮
            uint8_t fault_report : 1; // 有故障时点亮
            uint8_t ok_report : 1; // 正常工作时点亮
            uint8_t rsv3 : 3;
        };
        uint8_t led_ctl; // 用于访问整个字节
    };
} DeviceStatus;

// 调试打印函数
void debug_print(DeviceStatus* status) {
    printf("🌟 读取设备状态信息 🌟\n");

    // 打印每个字段
    printf("WHO_AM_I:                0x%02X\n", status->WHO_AM_I);
    printf("版本号:                  0x%02X\n", status->version);
    printf("UUID:                    0x%08X 0x%08X 0x%08X\n", status->uuid0, status->uuid1, status->uuid2);
    printf("输出电压:                %d mV\n", status->output_voltage);
    printf("输入电压:                %d mV\n", status->input_voltage);
    printf("电池电压:                %d mV\n", status->battery_voltage);
    printf("MCU电压:                 %d mV\n", status->mcu_voltage);
    printf("输出电流:                %d mA\n", status->output_current);
    printf("输入电流:                %d mA\n", status->input_current);
    printf("电池电流:                %d mA\n", status->battery_current);
    printf("温度:                    %d °C\n", status->temperature);

    printf("控制寄存器1 (cr1):       0x%02X\n", status->cr1);
    printf("    来电自启动模式       : %d\n", status->auto_start_mode);
    printf("    加载Python代码       : %d\n", status->python_load);
    printf("    运行Python代码       : %d\n", status->python_exec);
    printf("    读取Python输出日志   : %d\n", status->python_read_return);
    printf("    预留未来             : %d\n", status->rsv1);

    printf("控制寄存器2 (cr2):       0x%02X\n", status->cr2);

    printf("状态寄存器1 (sr1):       0x%02X\n", status->sr1);
    printf("    5V输出状态           : %s\n", status->sw_status ? "开启" : "关闭");
    printf("    快充模式             : %s\n", status->fast ? "慢充" : "快充");
    printf("    充电状态             : %s\n", status->charge ? "放电" : "充电");
    printf("    输入电压低           : %s\n", status->input_low ? "低" : "正常");
    printf("    输出电压低           : %s\n", status->output_low ? "低" : "正常");
    printf("    电池电压低           : %s\n", status->battery_low ? "低" : "正常");
    printf("    ADC误差              : %s\n", status->adc_mismatch ? "有" : "正常");
    printf("    电池故障             : %s\n", status->battery_fail ? "有" : "无");

    printf("状态寄存器2 (sr2):       0x%02X\n", status->sr2);
    printf("    Python代码过大       : %s\n", status->python_exec_toobig ? "是" : "否");

    printf("电池保护电压:           %d mV\n", status->battery_protection_voltage);
    printf("关机倒计时:             %d s\n", status->shutdown_countdown);
    printf("来电自启动电池电压阈值: %d mV\n", status->auto_start_voltage);
    printf("Python 输出缓冲大小:    %d B\n", status->pika_output_len);
    printf("请求OTA:                0x%04X\n", status->ota_request);
    printf("累计运行时间:           %llu 毫秒\n", status->runtime);
    printf("充电芯片触发间隔:       %d 秒\n", status->charge_detect_interval_s);
    printf("LED 控制:               0x%02X\n", status->led_ctl);

    printf("LED状态解析\n");
    // LED控制解析
    printf("    I2C通信发生时点亮   : %d\n", status->i2c_ack);
    printf("    电池充电时点亮       : %d\n", status->bat_charge);
    printf("    电池放电时点亮       : %d\n", status->bat_discharge);
    printf("    故障时点亮           : %d\n", status->fault_report);
    printf("    正常工作时点亮       : %d\n", status->ok_report);
}

int main() {
    int fd;
    DeviceStatus status; // 存储设备状态的结构体

    // 打开I2C设备文件
    if ((fd = open(I2C_DEV, O_RDWR)) < 0) {
        perror("打开I2C设备失败");
        return -1;
    }

    // 设置I2C从机地址
    if (ioctl(fd, I2C_SLAVE, I2C_ADDR) < 0) {
        perror("设置I2C从机地址失败");
        close(fd);
        return -1;
    }

    printf("🔄 开始读取设备数据...\n");
    
    // 使用SMBus分多次读取数据
    for (int offset = 0; offset < sizeof(DeviceStatus); offset += 32) {
        int len = 32;
        if (offset + len > sizeof(DeviceStatus)) {
            len = sizeof(DeviceStatus) - offset; // 最后一部分数据
        }

        // 使用SMBus读取数据
        union i2c_smbus_data data;
        struct i2c_smbus_ioctl_data args = {
            .read_write = I2C_SMBUS_READ,
            .command = offset,
            .size = I2C_SMBUS_I2C_BLOCK_DATA,
            .data = &data
        };

        // 设置要读取的字节数
        data.block[0] = len;
        
        // 执行SMBus读取操作
        if (ioctl(fd, I2C_SMBUS, &args) < 0) {
            perror("SMBus读取失败");
            close(fd);
            return -1;
        }

        // 将读取的数据存储到结构体
        memcpy((uint8_t*)&status + offset, data.block + 1, len);
        printf("📝 从地址0x%02X读取到数据: %d 字节\n", offset, len);
    }

    // 打印设备状态信息
    debug_print(&status);

    // 关闭I2C设备文件
    close(fd);
    return 0;
}
