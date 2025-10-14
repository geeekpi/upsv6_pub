import pygame
import sys
from smbus2 import SMBus
import math
import time

# Device address
DEVICE_ADDRESS = 0x17

# Define registers address
VERSION_REG = 0x01
OUTPUT_VOLTAGE_REG = 0x0E
INPUT_VOLTAGE_REG = 0x10
OUTPUT_CURRENT_REG = 0x16
INPUT_CURRENT_REG = 0x18

# Initialize SMBus
bus = SMBus(1)  # 1 means I2C no.1 bus

# Read 16-bit register
def read_word_register(register_address):
    value = bus.read_word_data(DEVICE_ADDRESS, register_address)
    if value > 32767:
        value -= 65536
    return value

# Calculate power
def calculate_power(voltage_mv, current_ma):
    voltage_v = voltage_mv / 1000.0
    current_a = current_ma / 1000.0
    return voltage_v * current_a  # Result in watts

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((800, 400))
pygame.display.set_caption("Power Gauges")

# Define colors
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)
RED = (255, 0, 0)

# Draw the gauge background
def draw_gauge_background(x_offset, title):
    pygame.draw.circle(screen, CYAN, (200 + x_offset, 200), 130, 2)
    max_power = 30  # Maximum power is 30W for the gauge
    num_ticks = int(max_power / 0.5)  # Number of ticks
    for i in range(num_ticks + 1):
        angle = math.radians(270 - (i / num_ticks * 180))  # 0 point at the bottom
        x1 = 200 + 120 * math.cos(angle) + x_offset
        y1 = 200 + 120 * math.sin(angle)
        x2 = 200 + 124 * math.cos(angle) + x_offset
        y2 = 200 + 124 * math.sin(angle)
        pygame.draw.line(screen, CYAN, (x1, y1), (x2, y2), 1)
        if i % 5 == 0:  # Only display every 5th tick
            font = pygame.font.SysFont(None, 16)
            img = font.render(f"{i * 0.5:.1f}", True, CYAN)
            text_width, text_height = font.size(f"{i * 0.5:.1f}")
            text_x = 200 + (135 + 3) * math.cos(angle) + x_offset - text_width / 2
            text_y = 200 + (135 + 3) * math.sin(angle) - text_height / 2
            screen.blit(img, (text_x, text_y))

    # Draw title
    font = pygame.font.SysFont(None, 24)
    img = font.render(title, True, CYAN)
    screen.blit(img, (200 + x_offset - img.get_width() / 2, 10))

# Draw the needle
def draw_needle(x_offset, power):
    max_power = 30  # Maximum power is 100W for the gauge
    angle = 270 - (power / max_power * 180)  # 0 point at the bottom
    angle_rad = math.radians(angle)
    x = 200 + 120 * math.cos(angle_rad) + x_offset
    y = 200 + 120 * math.sin(angle_rad)
    pygame.draw.line(screen, RED, (200 + x_offset, 200), (x, y), 2)

# Main loop
def main():
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Read power values
        input_voltage_mv = read_word_register(INPUT_VOLTAGE_REG)
        input_current_ma = read_word_register(INPUT_CURRENT_REG)
        input_power_w = calculate_power(input_voltage_mv, input_current_ma)
        
        output_voltage_mv = read_word_register(OUTPUT_VOLTAGE_REG)
        output_current_ma = read_word_register(OUTPUT_CURRENT_REG)
        output_power_w = calculate_power(output_voltage_mv, output_current_ma)
        
        # Update the gauges
        screen.fill(BLACK)
        draw_gauge_background(0, "INPUT")
        draw_gauge_background(400, "OUTPUT")
        draw_needle(0, input_power_w)
        draw_needle(400, output_power_w)
        pygame.display.flip()
        clock.tick(0.5)  # Update every 2 seconds

if __name__ == "__main__":
    main()
