from UPS import TFTModule as tft 
from UPS import Device

# init tft display
tft.init()

# loop
while True:
    # clean screen and fill with white color
    tft.fillScreen(0xFFFF)

    # delay for 500 ms
    Device.sleep(500)

    # draw pixel 
    for x in range(0,240):
        for y in range(0,240):
            # drawPixel(pos x, pos y, color) # RGB565 - RRRRRGGGGGGBBBBB 
            tft.drawPixel(x, y, 0x07E0)
            Device.sleep(2)

