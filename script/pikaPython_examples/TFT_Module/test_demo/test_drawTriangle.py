from UPS import TFTModule as tft 
from UPS import Device as dvc

# init display
tft.init()

# loop 
while True:
    # fill screen with white color
    tft.fillScreen(0xFFFF)

    # delay for 200 ms
    dvc.sleep(200)

    # drawTriangle(x0, y0, x1, y1, x2, y2, color)
    tft.drawTriangle(20, 20, 60, 120, 140, 120, 0xFBE0)

    # draw different color
    tft.drawTriangle(220, 20, 180, 120, 100, 120, 0x0FB0)

    # delay for 500 ms
    dvc.sleep(500)
