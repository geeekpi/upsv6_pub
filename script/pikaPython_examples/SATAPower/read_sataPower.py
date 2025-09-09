from UPS import SATAPower as sp

name_space = ['12V Output Voltage', '12V Output Current', 'Battery Input Voltage', 'Battery Input Current', '5V Output Voltage', '5V Output Current','3.3V Output Voltage', '3.3V Output Current']
units = ['mV', 'mA', 'mV', 'mA', 'mV', 'mA','mV', 'mA']

while True:
    """
    print(sp.getInput())    # Battery input voltage and input current
    print(sp.getOutput12()) # 12V output voltage and output current 
    print(sp.getOutput5())  # 5V  output voltage and output current
    print(sp.getOutput3V3()) # 3V3 output voltage and output current 
    print(sp.getAllInfo())  # All information in one list-like array.
    """
    for i in range(8):
        print(name_space[i],end=' ')
        print("Value is: %d" % sp.getAllInfo()[i], end=' ')
        print(units[i])

    print("-"*50)

