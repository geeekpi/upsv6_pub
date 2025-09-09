from UPS import TFTModule as tft
from UPS import Device

# Init TFT module
tft.init()


def test_drawPixel():
    tft.drawPixel(10, 10, 0xF800)  # red pixel
    Device.sleep(200)
    tft.fillScreen(0x0000)  #  clear screen 

def test_drawLine():
    tft.drawLine(0, 0, 100, 100, 0x07E0)  # green cross line
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawFastVLine():
    tft.drawFastVLine(50, 0, 100, 0x001F)  #  blue vertical line
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawFastHLine():
    tft.drawFastHLine(0, 50, 100, 0xFFE0)  # yellow horizontal line  
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawRect():
    tft.drawRect(20, 20, 60, 60, 0xF81F)  # pink rectangle  
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawCircle():
    tft.drawCircle(50, 50, 30, 0x07FF)  # cyan circle 
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_fillRect():
    tft.fillRect(30, 30, 40, 40, 0x7E0F)  # purple filled rectangle  
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawTriangle():
    tft.drawTriangle(50, 10, 10, 90, 90, 90, 0x000F)  # deep blue trangle  
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_fillTriangle():
    tft.fillTriangle(50, 10, 10, 90, 90, 90, 0xF0F0)  # light pink filled trangle  
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawString():
    tft.drawString(10, 10, "Size 1", 0xF800, 0x0000, 1)  # red，size 1
    tft.drawString(10, 30, "Size 2", 0x07E0, 0x0000, 2)  # green，size 2
    tft.drawString(10, 60, "Size 3", 0x001F, 0x0000, 3)  # blue，size 3
    tft.drawString(10, 100, "Size 4", 0xFFE0, 0x0000, 4)  # yellow，size 4
    tft.drawString(10, 160, "FanSe 5", 0xFFFF, 0x07FF, 5)  # white，size 4

# run all test
while True:
    test_drawPixel()
    Device.sleep(1000)
    test_drawLine()
    Device.sleep(1000)
    test_drawFastVLine()
    Device.sleep(1000)
    test_drawFastHLine()
    Device.sleep(1000)
    test_drawRect()
    Device.sleep(1000)
    test_drawCircle()
    Device.sleep(1000)
    test_fillRect()
    Device.sleep(1000)
    test_drawTriangle()
    Device.sleep(1000)
    test_fillTriangle()
    Device.sleep(1000)
    test_drawString()
    Device.sleep(1000)


