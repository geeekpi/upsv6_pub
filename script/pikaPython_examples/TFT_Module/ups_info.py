from UPS import TFTModule as tft
from UPS import Device

tft.init()

WHITE = 0xFFFF
RED = 0xF800 
GREEN = 0x7E0
BLUE = 0x001F
YELLOW = 0xFFE0
MAGENTA = 0xF81F
CYAN = 0x07FF


    tft.fillScreen(WHITE)
    Device.sleep(200)

    # (x, y, string, front coloer, background color, font size)
    tft.drawString(25, 40 , 'HELLO UPSv6', RED, WHITE, 3)
    tft.drawString(5, 80 , 'UPSv6 Monitor', CYAN, WHITE, 3)
    tft.fillRect(0, 120, 240, 20, RED)
    tft.fillRect(0, 140, 240, 20, YELLOW)
    tft.fillRect(0, 160, 240, 20, BLUE)
    tft.fillRect(0, 180, 240, 20, GREEN)
    tft.fillRect(0, 200, 240, 20, CYAN)
    tft.fillRect(0, 220, 240, 20, MAGENTA)
    Device.sleep(5000)

while True:
    ov = str(Device.getOutputVoltage())
    iv = str(Device.getInputVoltage())
    bv = str(Device.getBatteryVoltage())
    mv = str(Device.getMcuVoltage())

    oc = str(Device.getOutputCurrent())
    ic = str(Device.getInputCurrent())
    bc = str(Device.getBatteryCurrent())
    te = str(Device.getTemperature())

    Device.sleep(200)


    tft.fillScreen(WHITE)
    Device.sleep(200)
    tft.fillRect(0, 0, 240, 20, RED)
    tft.drawString(80, 50, 'OUTPUT', BLUE, WHITE, 3)
    if ov < 5100:
        tft.drawString(80, 110, ov, RED, WHITE, 4)
        tft.drawString(110, 160, 'mV', RED, WHITE, 4)
    else:
        tft.drawString(80, 110, ov, GREEN, WHITE, 4)
        tft.drawString(110, 160, 'mV', RED, WHITE, 4)
    tft.fillRect(0, 220, 240, 20, RED)
    Device.sleep(5000)

    tft.fillScreen(WHITE)
    Device.sleep(200)
    tft.fillRect(0, 0, 240, 20, GREEN)
    tft.drawString(80, 50, 'INPUT', BLUE, WHITE, 3)
    if iv < 12000:
        tft.drawString(80, 110, iv, RED, WHITE, 4)
        tft.drawString(110, 160, 'mV', RED, WHITE, 4)
        tft.fillRect(0, 200, 240, 20, RED)
    else:
        tft.drawString(80, 110, iv, GREEN, WHITE, 4)
        tft.drawString(110, 160, 'mV', RED, WHITE, 4)
        tft.fillRect(0, 220, 240, 20, GREEN)
    Device.sleep(5000)

    tft.fillScreen(WHITE)
    Device.sleep(200)
    tft.fillRect(0, 0, 240, 20, RED)
    tft.drawString(80, 50, 'BATTERY', BLUE, WHITE, 3)
    if bv < 7400:
        tft.drawString(80, 110, bv, RED, WHITE, 4)
        tft.drawString(110, 160, 'mV', RED, WHITE, 4)
    else:
        tft.drawString(80, 110, bv, GREEN, WHITE, 4)
        tft.drawString(110, 160, 'mV', RED, WHITE, 4)
    tft.fillRect(0, 220, 240, 20, RED)
    Device.sleep(5000)

    tft.fillScreen(WHITE)
    Device.sleep(200)
    tft.drawString(20, 50, 'MCU Voltage', BLUE, WHITE, 3)
    if mv < 3200:
        tft.drawString(80, 110, mv, RED, WHITE, 4)
        tft.drawString(110, 160, 'mV', RED, WHITE, 4)
        tft.fillRect(0, 200, 240, 20, RED)
    else:
        tft.drawString(80, 110, mv, GREEN, WHITE, 4)
        tft.drawString(110, 160, 'mV', RED, WHITE, 4)
        tft.fillRect(0, 200, 240, 20, GREEN)
    Device.sleep(5000)

    tft.fillScreen(WHITE)
    Device.sleep(200)
    tft.fillRect(0, 0, 240, 20, CYAN)
    tft.drawString(20, 50, 'OUTPUT CURR', CYAN, WHITE, 3)
    tft.drawString(80, 110, oc, MAGENTA, WHITE, 4)
    tft.drawString(110, 160, 'mA', CYAN, WHITE, 4)
    tft.fillRect(0, 220, 240, 20, CYAN)
    Device.sleep(5000)

    tft.fillScreen(WHITE)
    Device.sleep(200)
    tft.fillRect(0, 0, 240, 20, CYAN)
    tft.drawString(20, 50, 'INPUT CURR', CYAN, WHITE, 3)
    tft.drawString(80, 110, ic, MAGENTA, WHITE, 4)
    tft.drawString(110, 160, 'mA', CYAN, WHITE, 4)
    tft.fillRect(0, 220, 240, 20, MAGENTA)
    Device.sleep(5000)

    tft.fillScreen(WHITE)
    Device.sleep(200)
    tft.fillRect(0, 0, 240, 20, CYAN)
    tft.drawString(20, 50, 'BATTERY CURR', RED, WHITE, 3)
    tft.drawString(80, 110, bc, RED, WHITE, 4)
    tft.drawString(110, 160, 'mA', RED, WHITE, 4)
    tft.fillRect(0, 220, 240, 20, CYAN)
    Device.sleep(5000)

    tft.fillScreen(WHITE)
    Device.sleep(200)
    tft.fillRect(0, 0, 240, 20, GREEN)
    tft.drawString(40, 50, 'Temperature', RED, WHITE, 3)
    tft.drawString(80, 110, te, RED, WHITE, 4)
    tft.drawString(110, 160, 'C\'', RED, WHITE, 4)
    tft.fillRect(0, 220, 240, 20, GREEN)
    Device.sleep(5000)
