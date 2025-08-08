from UPS import TFTModule as tft
from UPS import Device as time 

# initial display
tft.init()

# loop
while True:
    # fill screen with white color
    tft.fillScreen(0xFFFF)

    # delay for 200 ms
    time.sleep(200)

    # fillRect(x, y, width, height, color)
    for x in range(80, 140):
        for y in range(80,140):
            tft.fillRect(x, y, 60, 60, 0xFB00)
            time.sleep(2)

