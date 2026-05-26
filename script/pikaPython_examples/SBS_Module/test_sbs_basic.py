from UPS import SBS, I2C, Device


SBS.init(I2C, 0x0a)

if not SBS.ping():
    print("No SBS device found!")
else:
    while True:
        addr = SBS.getAddr() 
        print("Addr: ", addr)
        v = SBS.voltageMv()
        Device.sleep(5000)
        print("Voltage:", v, "mV")
        c = SBS.currentMa()
        print("Current:", c, "mA")
        Device.sleep(5000)
        ac = SBS.averageCurrentMa()
        print("Average Current:", ac, "mA")
        Device.sleep(5000)
        if SBS.isDischarging():
            print("Discharging...")
        else:
            print("Charging....")
        Device.sleep(5000)
        rsoc = SBS.relativeStateOfChargePercent()
        print("RSOC:", rsoc, "%")
        Device.sleep(5000)
        ascp = SBS.absoluteStateOfChargePercent()
        print("ASCP:", ascp, "%")
        Device.sleep(5000)
        t = SBS.temperatureC10()
        if t < 0:
            t = SBS.temperatureC10()    
        else:
            print("Temp:", t/10.0, "C")
        Device.sleep(5000)

