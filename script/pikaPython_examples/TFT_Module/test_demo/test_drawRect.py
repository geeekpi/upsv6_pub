from UPS import TFTModule as tft
from UPS import Device 

# init display 
tft.init()

# loop
while True:
    # fill screen with white color
    tft.fillScreen(0xFFFF)

    # delay for 200 ms
    Device.sleep(200)

    # for loop
    for x in range(0, 240, 10):
        for y in range(0, 240, 10):
            # drawRect(x, y, width, hight, color)
            tft.drawRect(x, y, 20, 20, 0x6058)
            Device.sleep(2)

