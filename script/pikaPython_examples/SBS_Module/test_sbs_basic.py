from UPS import SBS, I2C, Device


SBS.init(I2C, 0x0a)

if not SBS.ping():
    print("No SBS device found!")
else:
    while True:
        print("\n--- Voltage ---")
        v = SBS.voltageMv()
        print("Voltage:", v, "mV")

        print("--- Current ---")
        c = SBS.currentMa()
        print("Current:", c, "mA")
        print("Discharging:", SBS.isDischarging())

        print("--- SOC ---")
        rsoc = SBS.relativeStateOfChargePercent()
        print("RSOC:", rsoc, "%")

        print("--- Temp ---")
        t = SBS.temperatureC10()
        print("Temp:", t/10.0, "C")

        print("-" * 30)
        Device.sleep(5000)

