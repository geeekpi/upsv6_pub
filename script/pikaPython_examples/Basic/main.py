"""
This script demonstrates the usage of PikaStdLib and UPS Device.
It checks memory usage and prints relevant information.
"""

import PikaStdLib
from UPS import Device

def check_memory():
    """
    Checks and prints the maximum memory usage.
    """
    memory_checker = PikaStdLib.MemChecker()
    print('mem used max:')
    memory_checker.max()


def get_runtime():
    """
    Print Device run time information 
    """
    return Device.getRuntime()


while True:
    print("hello UPSv6:")
    check_memory()
    run_time = get_runtime()
    print(run_time)
    Device.sleep(5000)
