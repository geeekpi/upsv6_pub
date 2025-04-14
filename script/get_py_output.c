/* apt install libi2c-dev */
/* gcc xxx.c -li2c -o xxx */
/* 本脚本用途是获取PikaPython运行输出 */

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <stdint.h>
#include <i2c/smbus.h>  // smbus API

// I2C设备与从机地址
static const char *I2C_DEVICE = "/dev/i2c-1";
static const int SLAVE_ADDR = 0x17;

// 寄存器地址（采用常量变量）
static const uint8_t CR1_ADDR             = 0x1D;
static const uint8_t PIKA_OUTPUT_LEN_ADDR = 0x28;

// CR1寄存器各个位标志
static const uint8_t BIT_PYTHON_READ_RETURN = (1 << 3); // BIT3

int main() {
    // 1. 打开I2C设备
    int i2c_fd = open(I2C_DEVICE, O_RDWR);
    if (i2c_fd < 0) {
        perror("无法打开I2C设备");
        return EXIT_FAILURE;
    }

    // 2. 设置从机地址
    if (ioctl(i2c_fd, I2C_SLAVE, SLAVE_ADDR) < 0) {
        perror("无法设置从机地址");
        close(i2c_fd);
        return EXIT_FAILURE;
    }

    // 原始CR1要读出来以便恢复
    int orig_cr1 = i2c_smbus_read_byte_data(i2c_fd, CR1_ADDR);
    if (orig_cr1 < 0) {
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }

    uint8_t len_buf[2];
    int ret = i2c_smbus_read_i2c_block_data(i2c_fd, PIKA_OUTPUT_LEN_ADDR, 2, len_buf);
    if (ret < 0) {
        perror("读取输出长度失败");
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }
    uint16_t output_len = (len_buf[1] << 8) | len_buf[0];
    printf("检测到 Python 输出长度: %d 字节\n", output_len);

    printf("获取输出...\n");
    if (output_len == (uint8_t)-1) {
        close(i2c_fd);
        return EXIT_FAILURE;
    }

    if (output_len > 0) {
        uint8_t *output = malloc(output_len);
        if (!output) {
            perror("内存分配失败");
            close(i2c_fd);
            return EXIT_FAILURE;
        }

        // 设置读取标志
        if (i2c_smbus_write_byte_data(i2c_fd, CR1_ADDR, orig_cr1 | BIT_PYTHON_READ_RETURN) != 0) {
            free(output);
            close(i2c_fd);
            return EXIT_FAILURE;
        }

        // 分块读取输出
        int total_read = 0;
        while (total_read < output_len) {
            int to_read = output_len - total_read > 32 ? 32 : output_len - total_read;
            int read = i2c_smbus_read_i2c_block_data(i2c_fd, 0x00, to_read, output + total_read);
            
            if (read <= 0) break;
            total_read += read;
        }

        printf("\n脚本输出(%d字节):\n", total_read);
        fwrite(output, 1, total_read, stdout);
        printf("\n");
        
        free(output);
    } else {
        printf("无输出\n");
    }

    // 5. 恢复原始 CR1 寄存器值（使用 smbus API 写入单字节）
    if (i2c_smbus_write_byte_data(i2c_fd, CR1_ADDR, orig_cr1) < 0) {
        perror("恢复原始 CR1 值失败");
    } else {
        printf("成功恢复原始 CR1 值: 0x%02X\n", orig_cr1);
    }

    close(i2c_fd);
    return EXIT_SUCCESS;
}
