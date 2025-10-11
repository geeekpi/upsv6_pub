#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <stdint.h>
#include <string.h>
#include <stddef.h>
#include <time.h>

#define TESTMODE		// if enabled -> no flashing to flash memory, only I2C communication and terminal output
                        //  used for tweaking the progress bar, deHarro
#ifdef TESTMODE
	#define DEVICE_ADDR 0x17
#else
	#define DEVICE_ADDR 0x18
#endif

#define I2C_DEVICE "/dev/i2c-1"
#define MAX_BUF_LEN 1024

// 🎨 Progress bar length
#define PROGRESS_BAR_WIDTH 50

// 📦 Device status structure
typedef struct {
    uint8_t WHO_AM_I;
    uint8_t version;
    uint32_t uuid0;
    uint32_t uuid1;
    uint32_t uuid2;
    uint8_t ctrl;
    uint8_t rsv1[100];
} DeviceStatus;

// 📊 Byte size formatter
const char* bytes_to_human(double bytes) {
    const char* suffixes[] = {"B", "KB", "MB", "GB"};
    int i = 0;
    while (bytes >= 1024 && i < 3) {
        bytes /= 1024;
        i++;
    }
    static char output[20];
    sprintf(output, "%.2f %s", bytes, suffixes[i]);
    return output;
}

int open_i2c_device(const char *device, int addr) {
    printf("🔌 Opening I2C device %s...", device);
    int fd = open(device, O_RDWR);
    if (fd < 0) {
        perror("❌ Open failed");
        return -1;
    }
    printf("✅ Success (fd=%d)\n", fd);
    
    printf("📡 Setting slave address 0x%02X...", addr);
    if (ioctl(fd, I2C_SLAVE, addr) < 0) {
        perror("❌ Address setting failed");
        close(fd);
        return -1;
    }
    printf("✅ Success\n");
    return fd;
}

int read_device_status(int fd, DeviceStatus *status) {
    printf("\n🔍 Reading device status...");
    uint8_t reg_addr = 0;
    if (write(fd, &reg_addr, 1) != 1) {
        perror("❌ Register address write failed");
        return -1;
    }
    
    ssize_t read_bytes = read(fd, status, sizeof(DeviceStatus));
    if (read_bytes != sizeof(DeviceStatus)) {
        printf("❌ Read failed (expected %zu bytes, got %zd)\n", 
              sizeof(DeviceStatus), read_bytes);
        return -1;
    }
    printf("✅ Success\n");
    printf("   🆔 WHO_AM_I: 0x%02X\n", status->WHO_AM_I);
    printf("   📦 Firmware version: v%d\n", status->version);
    return 0;
}

int write_register_and_data(int fd, uint8_t ctrl, uint8_t *data, size_t size) {
    static clock_t last_time = 0;
    clock_t now = clock();
    double elapsed = (double)(now - last_time) / CLOCKS_PER_SEC;
    
    uint8_t buffer[size + 2];
    buffer[0] = offsetof(DeviceStatus, ctrl);
    buffer[1] = ctrl;
    memcpy(buffer + 2, data, size);

    printf("\n✏️  Writing data...");
#ifndef TESTMODE			// no I2C writing in TESTMODE
    ssize_t written = write(fd, buffer, size + 2);
    if (written != size + 2) {
        printf("\n❌ Write failed (expected %zu bytes, wrote %zd)\n", size+2, written);
        return -1;
    }
#endif
    
    // Calculate transfer speed
    if (elapsed > 0) {
        double speed = size / elapsed / 1024;
        printf("✅ Success | Speed: %.2f B/s\n", speed);
    } else {
        printf("✅ Success\n");
    }
    last_time = now;
    return 0;
}

// Calculate the nearest multiple of 16
size_t round_up_to_multiple_of_16(size_t len)
{
    return (len + 15) & ~15;
}

// print progressbar ---------------------------------------------------------------- deHarro
// by Yusuf Savaş
// taken from https://gist.github.com/amullins83/24b5ef48657c08c4005a8fab837b7499?permalink_comment_id=4554839#gistcomment-4554839
void print_progress(size_t count, size_t max) 
{
    const int bar_width = PROGRESS_BAR_WIDTH;

    float progress = (float)count / max;
    int bar_length = progress * bar_width;

    printf("\r\033[42;30m Progress: %.1f%% \033[0m [", progress * 100);
    for (int i = 0; i < bar_length; ++i) {
        printf("#");
    }
    for (int i = bar_length; i < bar_width; ++i) {
        printf(" ");
    }
    printf("]");

    fflush(stdout);
}
// \print progressbar ---------------------------------------------------------------- deHarro

int main(int argc, char *argv[]) {

    printf("\033[2;J");			// clear screen

    printf("\n🚀 Firmware Flasher Starting!\n");
    printf("============================\n");

    if (argc != 2) {
        fprintf(stderr, "❌ Usage: %s <encrypted_file>\n", argv[0]);
        return EXIT_FAILURE;
    }

    // Open I2C device
    int fd = open_i2c_device(I2C_DEVICE, DEVICE_ADDR);
    if (fd < 0) return EXIT_FAILURE;

    // Read device status
    DeviceStatus status;
    if (read_device_status(fd, &status) < 0) {
        close(fd);
        return EXIT_FAILURE;
    }

    // Verify device ID
    printf("\n🔎 Verifying device...");
    if (status.WHO_AM_I != 0xA6) {
        printf("❌ Invalid device ID (expected 0xA6, got 0x%02X)\n", status.WHO_AM_I);
        close(fd);
        return EXIT_FAILURE;
    }
    printf("✅ Validation passed\n");

    // Prepare control register
    uint8_t ctrl = status.ctrl | 0x01;
    printf("\n🎛 Control register set: 0x%02X\n", ctrl);

    // Open encrypted file
    printf("\n📂 Opening encrypted file %s...", argv[1]);
    FILE *enc_file = fopen(argv[1], "rb");
    if (!enc_file) {
        perror("❌ File open failed");
        close(fd);
        return EXIT_FAILURE;
    }
    
    // Get file size
    fseek(enc_file, 0, SEEK_END);
    long file_size = ftell(enc_file);
    fseek(enc_file, 0, SEEK_SET);
    printf("✅ Success | Size: %s\n", bytes_to_human(file_size));

    uint8_t buffer[MAX_BUF_LEN];
    size_t bytes_read, total = 0;
    time_t start_time = time(NULL);

    printf("\n🔥 Starting flash process!\n");
    while ((bytes_read = fread(buffer, 1, MAX_BUF_LEN, enc_file)) > 0) {

	printf("\033[2;K");	// clear line to let progress bar stay fixed on last line, deHarro

        printf("\n----------------------\n");
        printf("📦 Processing block | Size: %zu bytes\n", bytes_read);

        // Validate block size
        if (bytes_read % 16 != 0) {
            // printf("❌ Invalid block size (must be multiple of 16)\n");
            bytes_read = round_up_to_multiple_of_16(bytes_read);
            // fclose(enc_file);
            // close(fd);
            // return EXIT_FAILURE;
        }

        // Write data
        if (write_register_and_data(fd, ctrl, buffer, bytes_read) < 0) {
            fclose(enc_file);
            close(fd);
            return EXIT_FAILURE;
        }
        total += bytes_read;

        // Show progress	------------------------------------------------------
	// workaround for passing static local pointer as return value, deHarro
	char totalBytes[20];
	strncpy(totalBytes, bytes_to_human(total), sizeof(bytes_to_human(total)));

	printf("📊Progress: %s / %s\n", totalBytes, bytes_to_human(file_size));

        print_progress(total, file_size);	// print semigrafic progressbar, deHarro

#ifndef TESTMODE
        // Wait for device ready
        int retry = 0;
        printf("\n⏳ Waiting for device...");
        while (++retry <= 5) {
            usleep(500000);
            printf("\n   ⌚ Attempt #%d...", retry);
            
            if (read_device_status(fd, &status) < 0) {
                fclose(enc_file);
                close(fd);
                return EXIT_FAILURE;
            }
            
            if ((status.ctrl & 0x04) && !(status.ctrl & 0x02)) {
                printf("✅ Device ready!");
                break;
            }
            
            if (retry == 5) {
                printf("❌ Device timeout");
                fclose(enc_file);
                close(fd);
                return EXIT_FAILURE;
            }
        }
#else
	sleep(1);
#endif
    }

    // Send boot command
    printf("\n\n🚀 Sending boot command...");
    uint8_t boot_cmd[2] = {offsetof(DeviceStatus, ctrl), 0x80};
    if (write(fd, boot_cmd, 2) != 2) {
        perror("❌ Boot command failed");
    } else {
        printf("✅ Command sent!");
    }

    // Statistics
    time_t end_time = time(NULL);
    double total_time = difftime(end_time, start_time);
    printf("\n\n🎉 Flashing complete!");
    printf("\n===============================");
    printf("\n📝 Statistics:");
    printf("\n   Total data: %s", bytes_to_human(total));
    printf("\n   Time elapsed: %.2f seconds", total_time);
    printf("\n   Average speed: %.2f KB/s", (total/1024.0)/total_time);
    printf("\n===============================\n");

    fclose(enc_file);
    close(fd);
    return EXIT_SUCCESS;
}
