import smbus2
import struct
from typing import NamedTuple
from dataclasses import dataclass

# 设备配置
I2C_DEV = 3  # /dev/i2c-3
I2C_ADDR = 0x17

@dataclass
class DeviceStatus:
    # 定义与C语言结构体对应的字段
    WHO_AM_I: int  # 固定为0xA6
    version: int  # 版本号(只读)
    uuid0: int  # 唯一ID
    uuid1: int
    uuid2: int

    output_voltage: int  # 输出电压(5V)
    input_voltage: int  # 输入电压
    battery_voltage: int  # 电池电压
    mcu_voltage: int  # MCU电压
    output_current: int  # 输出电流(5V)
    input_current: int  # 输入电流
    battery_current: int  # 电池电流(负数为消耗,正数为充电)
    temperature: int  # 温度

    cr1: int  # 控制寄存器1
    cr2: int  # 控制寄存器2

    sr1: int  # 状态寄存器1
    sr2: int  # 状态寄存器2

    battery_protection_voltage: int  # 电池保护电压
    shutdown_countdown: int  # 关机倒计时
    auto_start_voltage: int  # 来电自启动电池电压阈值
    pika_output_len: int  # Python 输出缓冲大小
    ota_request: int  # 请求OTA
    runtime: int  # 运行累计时间
    charge_detect_interval_s: int  # 充电芯片触发间隔
    led_ctl: int  # LED控制

def debug_print(status: DeviceStatus):
    """打印设备状态信息"""
    print("🌟 读取设备状态信息 🌟\n")
    
    # 打印每个字段
    print(f"WHO_AM_I:                0x{status.WHO_AM_I:02X}")
    print(f"版本号:                  0x{status.version:02X}")
    print(f"UUID:                    0x{status.uuid0:08X} 0x{status.uuid1:08X} 0x{status.uuid2:08X}")
    print(f"输出电压:                {status.output_voltage} mV")
    print(f"输入电压:                {status.input_voltage} mV")
    print(f"电池电压:                {status.battery_voltage} mV")
    print(f"MCU电压:                 {status.mcu_voltage} mV")
    print(f"输出电流:                {status.output_current} mA")
    print(f"输入电流:                {status.input_current} mA")
    print(f"电池电流:                {status.battery_current} mA")
    print(f"温度:                    {status.temperature} °C")

    print(f"控制寄存器1 (cr1):       0x{status.cr1:02X}")
    print(f"    来电自启动模式       : {(status.cr1 >> 0) & 1}")
    print(f"    加载Python代码       : {(status.cr1 >> 1) & 1}")
    print(f"    运行Python代码       : {(status.cr1 >> 2) & 1}")
    print(f"    读取Python输出日志   : {(status.cr1 >> 3) & 1}")
    print(f"    预留未来             : {(status.cr1 >> 4) & 0xF}")

    print(f"控制寄存器2 (cr2):       0x{status.cr2:02X}")

    print(f"状态寄存器1 (sr1):       0x{status.sr1:02X}")
    print(f"    5V输出状态           : {'开启' if (status.sr1 >> 0) & 1 else '关闭'}")
    print(f"    快充模式             : {'慢充' if (status.sr1 >> 1) & 1 else '快充'}")
    print(f"    充电状态             : {'放电' if (status.sr1 >> 2) & 1 else '充电'}")
    print(f"    输入电压低           : {'低' if (status.sr1 >> 3) & 1 else '正常'}")
    print(f"    输出电压低           : {'低' if (status.sr1 >> 4) & 1 else '正常'}")
    print(f"    电池电压低           : {'低' if (status.sr1 >> 5) & 1 else '正常'}")
    print(f"    ADC误差              : {'有' if (status.sr1 >> 6) & 1 else '正常'}")
    print(f"    电池故障             : {'有' if (status.sr1 >> 7) & 1 else '无'}")

    print(f"状态寄存器2 (sr2):       0x{status.sr2:02X}")
    print(f"    Python代码过大       : {'是' if (status.sr2 >> 0) & 1 else '否'}")

    print(f"电池保护电压:           {status.battery_protection_voltage} mV")
    print(f"关机倒计时:             {status.shutdown_countdown} s")
    print(f"来电自启动电池电压阈值: {status.auto_start_voltage} mV")
    print(f"Python 输出缓冲大小:    {status.pika_output_len} B")
    print(f"请求OTA:                0x{status.ota_request:04X}")
    print(f"累计运行时间:           {status.runtime} 毫秒")
    print(f"充电芯片触发间隔:       {status.charge_detect_interval_s} 秒")
    print(f"LED 控制:               0x{status.led_ctl:02X}")

    print("LED状态解析")
    # LED控制解析
    print(f"    I2C通信发生时点亮   : {(status.led_ctl >> 0) & 1}")
    print(f"    电池充电时点亮       : {(status.led_ctl >> 1) & 1}")
    print(f"    电池放电时点亮       : {(status.led_ctl >> 2) & 1}")
    print(f"    故障时点亮           : {(status.led_ctl >> 3) & 1}")
    print(f"    正常工作时点亮       : {(status.led_ctl >> 4) & 1}")

def read_device_status() -> DeviceStatus:
    """读取设备状态"""
    # 定义结构体格式 (小端，与C结构体一致)
    # B: uint8_t, H: uint16_t, I: uint32_t, Q: uint64_t, h: int16_t, b: int8_t
    fmt = '<'  # 小端
    fmt += 'B'  # WHO_AM_I
    fmt += 'B'  # version
    fmt += 'III'  # uuid0-2
    fmt += 'HHHHHH'  # output_voltage, input_voltage, battery_voltage, mcu_voltage, output_current, input_current
    fmt += 'h'  # battery_current
    fmt += 'b'  # temperature
    fmt += 'BB'  # cr1, cr2
    fmt += 'BB'  # sr1, sr2
    fmt += 'HHHHH'  # battery_protection_voltage, shutdown_countdown, auto_start_voltage, pika_output_len, ota_request
    fmt += 'Q'  # runtime
    fmt += 'H'  # charge_detect_interval_s
    fmt += 'B'  # led_ctl
    
    # 计算结构体大小
    struct_size = struct.calcsize(fmt)
    print(f"结构体大小: {struct_size} 字节")
    
    # 初始化I2C总线
    bus = smbus2.SMBus(I2C_DEV)
    
    # 分多次读取数据，每次最多32字节
    data = bytearray()
    for offset in range(0, struct_size, 32):
        # 计算本次读取的长度
        read_len = min(32, struct_size - offset)
        
        try:
            # 使用SMBus读取块数据
            block_data = bus.read_i2c_block_data(I2C_ADDR, offset, read_len)
            
            # 添加到数据缓冲区
            data.extend(block_data)
            print(f"📝 从地址0x{offset:02X}读取到数据: {len(block_data)} 字节")
        except Exception as e:
            print(f"❌ 读取地址0x{offset:02X}时出错: {e}")
            # 填充0以保证数据长度正确
            data.extend(bytes([0] * read_len))
    
    # 检查数据长度是否正确
    if len(data) < struct_size:
        print(f"⚠️ 数据不足，期望 {struct_size} 字节，实际 {len(data)} 字节")
        # 填充0
        data.extend(bytes([0] * (struct_size - len(data))))
    
    # 解包数据到结构体
    try:
        unpacked = struct.unpack(fmt, data[:struct_size])
        return DeviceStatus(*unpacked)
    except Exception as e:
        print(f"❌ 解包数据时出错: {e}")
        print(f"数据长度: {len(data)} 字节")
        print(f"格式字符串: {fmt} (需要 {struct_size} 字节)")
        raise

if __name__ == '__main__':
    print("🔄 开始读取设备数据...")
    try:
        status = read_device_status()
        debug_print(status)
    except Exception as e:
        print(f"❌ 读取设备数据时出错: {e}")