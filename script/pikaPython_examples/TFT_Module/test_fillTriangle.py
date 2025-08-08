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

    # fillTriangle(int x0, int y0, int x1, int y1, int x3, int y3, int color)
    tft.fillTriangle(10, 20, 120, 210, 210, 20, 0xFB00)
    time.sleep(500)
    tft.fillTriangle(10, 200, 120, 20, 210, 210, 0x07E0)
    time.sleep(500)
    tft.fillTriangle(10, 220, 120, 10, 210, 210, 0x001E)
    time.sleep(500)

