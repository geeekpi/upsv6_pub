from UPS import TFTModule as tft 
from UPS import Device 


# init tft display
tft.init()

# loop
while True:
    # clear screen with white color
    tft.fillScreen(0xFFFF)

    # delay for 200 microseconds
    Device.sleep(200)

    # drawline 
    for x in range(0, 240, 10):
        for y in range(0, 240, 10):
            # drawLine(startx, starty, endx, endy, color)
            tft.drawLine(x, y, x+10, y+10, 0x001C)

            # delay for a while
            Device.sleep(2)
