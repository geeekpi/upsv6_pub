/* apt install libi2c-dev */
/* gcc xxx.c -li2c -o xxx */
/* 本脚本用途是上传PikaPython脚本 */

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <linux/i2c.h>
#include <i2c/smbus.h>  // smbus API

// I2C device and slave address
static const char *I2C_DEVICE = "/dev/i2c-1";
static const int SLAVE_ADDR = 0x17;

// Register addresses (using const variables)
static const uint8_t CR1_ADDR             = 0x1D;
static const uint8_t PIKA_OUTPUT_LEN_ADDR = 0x28;

// CR1 register bit flags (all uppercase for better visibility)
static const uint8_t BIT_AUTO_START_MODE    = (1 << 0); // BIT0
static const uint8_t BIT_PYTHON_LOAD        = (1 << 1); // BIT1
static const uint8_t BIT_PYTHON_EXEC        = (1 << 2); // BIT2
static const uint8_t BIT_PYTHON_READ_RETURN = (1 << 3); // BIT3

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "🔴 Usage: %s <python_script_file>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    // Read Python script file
    printf("🔵 Opening Python script file: %s\n", argv[1]);
    FILE *fp = fopen(argv[1], "rb");
    if (!fp) {
        perror("🔴 Failed to open Python script file");
        exit(EXIT_FAILURE);
    }
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    char *python_code = malloc(file_size);
    if (!python_code) {
        perror("🔴 Memory allocation failed");
        fclose(fp);
        exit(EXIT_FAILURE);
    }
    size_t read_size = fread(python_code, 1, file_size, fp);
    fclose(fp);
    if (read_size != file_size) {
        fprintf(stderr, "🔴 File read error: expected %ld bytes, got %zu bytes\n", file_size, read_size);
        free(python_code);
        exit(EXIT_FAILURE);
    }
    printf("🟢 Successfully read Python script (%ld bytes)\n", file_size);

    // Open I2C device
    printf("🔵 Opening I2C device: %s\n", I2C_DEVICE);
    int i2c_fd = open(I2C_DEVICE, O_RDWR);
    if (i2c_fd < 0) {
        perror("🔴 Failed to open I2C device");
        free(python_code);
        exit(EXIT_FAILURE);
    }
    // Set I2C slave address
    printf("🔵 Setting I2C slave address: 0x%02X\n", SLAVE_ADDR);
    if (ioctl(i2c_fd, I2C_SLAVE, SLAVE_ADDR) < 0) {
        perror("🔴 Failed to set I2C slave address");
        free(python_code);
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }

    // -------------------------
    // 1. Backup CR1 register
    printf("🔵 Reading original CR1 register value...\n");
    int orig_cr1 = i2c_smbus_read_byte_data(i2c_fd, CR1_ADDR);
    if (orig_cr1 < 0) {
        perror("🔴 Failed to read original CR1 value");
        free(python_code);
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }
    printf("🟢 Original CR1 register value: 0x%02X\n", orig_cr1);

    // Combined transfer: first write CR1 (set python_load flag), then transfer Python script data
    printf("🔵 Preparing combined transfer (set python_load flag + send script data)\n");
    struct i2c_rdwr_ioctl_data packets;
    struct i2c_msg messages[2];

    // Message 1: Write CR1 register address and new value (set python_load flag)
    uint8_t msg1[2];
    msg1[0] = CR1_ADDR;
    msg1[1] = orig_cr1 | BIT_PYTHON_LOAD;
    messages[0].addr  = SLAVE_ADDR;
    messages[0].flags = 0; // Write operation
    messages[0].len   = sizeof(msg1);
    messages[0].buf   = msg1;

    // Message 2: Write Python script data
    messages[1].addr  = SLAVE_ADDR;
    messages[1].flags = 0; // Write operation
    messages[1].len   = file_size;
    messages[1].buf   = (uint8_t *)python_code;

    packets.msgs = messages;
    packets.nmsgs = 2;
    if (ioctl(i2c_fd, I2C_RDWR, &packets) < 0) {
        perror("🔴 Combined transfer (code loading) failed");
        free(python_code);
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }
    printf("🟢 Combined transfer successful: Set python_load flag and sent %ld bytes of Python script\n", file_size);

    // After loading, automatically send STOP signal. Wait a bit, then check if python_load flag is cleared
    printf("⏳ Waiting for device to process data (1s)...\n");
    sleep(1);

    // Check if PYTHON_LOAD flag has been cleared using smbus to read CR1
    printf("🔵 Checking CR1 status after loading...\n");
    int check_cr1 = i2c_smbus_read_byte_data(i2c_fd, CR1_ADDR);
    if (check_cr1 < 0) {
        perror("🔴 Failed to check CR1 status");
        free(python_code);
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }
    printf("🟢 CR1 register value after loading: 0x%02X\n", check_cr1);
    if (check_cr1 & BIT_PYTHON_LOAD) {
        fprintf(stderr, "🔴 Error: PYTHON_LOAD flag is still set!\n");
        free(python_code);
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }
    printf("🟢 PYTHON_LOAD flag cleared, loading successful!\n");

    // -------------------------
    // 3. Trigger code execution: Set PYTHON_EXEC flag
    printf("🔵 Setting PYTHON_EXEC flag to trigger execution...\n");
    int exec_cr1 = check_cr1 | BIT_PYTHON_EXEC;
    if (i2c_smbus_write_byte_data(i2c_fd, CR1_ADDR, exec_cr1) < 0) {
        perror("🔴 Failed to set PYTHON_EXEC flag");
        free(python_code);
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }
    printf("🟢 PYTHON_EXEC flag set, CR1 updated to: 0x%02X\n", exec_cr1);

    // Wait 5 seconds for device to execute Python code
    printf("⏳ Waiting 5 seconds for Python code execution...\n");
    sleep(5);

    // -------------------------
    // 4. Read output length (using smbus API to read 2 bytes)
    printf("🔵 Reading output length...\n");
    uint8_t len_buf[2];
    int ret = i2c_smbus_read_i2c_block_data(i2c_fd, PIKA_OUTPUT_LEN_ADDR, 2, len_buf);
    if (ret < 0) {
        perror("🔴 Failed to read output length");
        free(python_code);
        close(i2c_fd);
        exit(EXIT_FAILURE);
    }
    uint16_t output_len = (len_buf[1] << 8) | len_buf[0];
    printf("🟢 Detected Python output length: %d bytes\n", output_len);

    printf("🔵 Fetching output...\n");
    if (output_len == (uint8_t)-1) {
        close(i2c_fd);
        return EXIT_FAILURE;
    }

    if (output_len > 0) {
        uint8_t *output = malloc(output_len);
        if (!output) {
            perror("🔴 Memory allocation failed");
            close(i2c_fd);
            return EXIT_FAILURE;
        }

        // Set read flag
        printf("🔵 Setting PYTHON_READ_RETURN flag...\n");
        if (i2c_smbus_write_byte_data(i2c_fd, CR1_ADDR, BIT_PYTHON_READ_RETURN) != 0) {
            free(output);
            close(i2c_fd);
            return EXIT_FAILURE;
        }

        // Read output in chunks
        printf("🔵 Reading output in chunks...\n");
        int total_read = 0;
        while (total_read < output_len) {
            int to_read = output_len - total_read > 32 ? 32 : output_len - total_read;
            printf("🔹 Reading chunk of %d bytes (total read: %d/%d)\n", to_read, total_read, output_len);
            int read = i2c_smbus_read_i2c_block_data(i2c_fd, 0x00, to_read, output + total_read);
            
            if (read <= 0) break;
            total_read += read;
        }

        printf("\n🟢 Script output (%d bytes):\n", total_read);
        fwrite(output, 1, total_read, stdout);
        printf("\n");
        
        free(output);
    } else {
        printf("🟢 No output\n");
    }

    // -------------------------
    // 5. Restore original CR1 register value (using smbus API to write single byte)
    printf("🔵 Restoring original CR1 register value...\n");
    if (i2c_smbus_write_byte_data(i2c_fd, CR1_ADDR, orig_cr1) < 0) {
        perror("🔴 Failed to restore original CR1 value");
    } else {
        printf("🟢 Successfully restored original CR1 value: 0x%02X\n", orig_cr1);
    }

    free(python_code);
    close(i2c_fd);
    printf("🟢 Program completed successfully!\n");
    return 0;
}
