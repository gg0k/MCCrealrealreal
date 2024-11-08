import math
import time
from machine import Pin, I2C
import utime
import _thread
from ADS1115 import *

ADS1115_ADDRESS = 0x48

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
adc = ADS1115(ADS1115_ADDRESS, i2c=i2c)

adc.setVoltageRange_mV(ADS1115_RANGE_6144)
adc.setConvRate(ADS1115_860_SPS)
adc.setCompareChannels(ADS1115_COMP_0_GND)
adc.setMeasureMode(ADS1115_CONTINUOUS)

while True:
    start = time.ticks_us()
    adc_value = adc.getResult_V()
    print(adc_value)
    elapsed_time = time.ticks_diff(time.ticks_us(), start)
    if (1000-elapsed_time)>0:
        utime.sleep_us(int(1000-elapsed_time))
    
