# Importar librerias
import time
from machine import Pin, I2C, ADC
import utime
from ADS1115 import *

# Asignar adress del ads1115
ADS1115_ADDRESS = 0x48

# Asignar pines para comunicacion i2c
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
adc_ads = ADS1115(ADS1115_ADDRESS, i2c=i2c)

# Configuración del rango de voltaje y modo de medición
adc_ads.setVoltageRange_mV(ADS1115_RANGE_6144)
adc_ads.setConvRate(ADS1115_860_SPS)
adc_ads.setCompareChannels(ADS1115_COMP_0_GND)
adc_ads.setMeasureMode(ADS1115_CONTINUOUS)

# Configuración del switch en el pin 15
switch = Pin(15, Pin.IN, Pin.PULL_UP)

#asignar pin para adc
adc_esp = ADC(Pin(34))

# Calibración del ADC del ESP32 (si es necesario)
adc_esp.atten(ADC.ATTN_11DB)  # Rango de 0 a 3.6V
adc_esp.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits


def leer_adc0_ads():
    # Leer canal A0 del ADS1115
    return adc_ads.getResult_V()

def leer_adc_esp():
    # Leer ADC interno del ESP32 en el pin 34
    return adc_esp.read() * (3.1 / 4095)  # Convertir lectura a voltios

while True:
    start = time.ticks_us()

    # Si el switch está presionado, leer también del ADC interno
    if switch.value() == 0:
        # mandar la lectura del ads1115 y del adc, separados por una coma, con 2 decimales cada uno
        # al final agregar \n
        print("{:.2f},{:.2f}\n".format(leer_adc0_ads(),leer_adc_esp()))

    else:
        print("{:.4f}\n".format(leer_adc0_ads()))


    elapsed_time = time.ticks_diff(time.ticks_us(), start)
    
    # Ajustar el retardo para que la lectura sea de 1ms
    if (1000 - elapsed_time) > 0:
        utime.sleep_us(int(1000 - elapsed_time))


