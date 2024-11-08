import network
import socket
import machine
import utime
import _thread
from ADS1115 import *
from machine import Pin, I2C,Timer

ADS1115_ADDRESS = 0x48

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
adc = ADS1115(ADS1115_ADDRESS, i2c=i2c)

adc.setVoltageRange_mV(ADS1115_RANGE_6144)
adc.setConvRate(ADS1115_860_SPS)
adc.setCompareChannels(ADS1115_COMP_0_GND)
adc.setMeasureMode(ADS1115_CONTINUOUS) 

# Configuración de WiFi
ssid = 'valeria'
password = 'vale1970'

# Conectar a la red WiFi
station = network.WLAN(network.STA_IF)
station.active(True)

if not station.isconnected():
    station.connect(ssid, password)
    while not station.isconnected():
        pass

print('Conexión exitosa')
print(station.ifconfig())

# Crear un socket y escuchar en el puerto 80
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('Esperando una conexión...')

# Variable global para almacenar el cliente
client_socket = None
data_buffer = []

def read_adc(timer):
    global data_buffer
    adc_value = adc.getResult_V()
    utime.sleep_us(250)
    
    data_buffer.append(adc_value)
    if len(data_buffer) >= 10:  # Enviar datos en bloques de 10
        send_data()

def send_data():
    global client_socket, data_buffer
    if client_socket:
        try:
            data_str = ",".join(f"{val:.5f}" for val in data_buffer) + "\n"
            client_socket.send(data_str.encode())
            data_buffer = []  # Limpiar el buffer después de enviar
        except:
            client_socket = None  # Resetear el cliente en caso de error

# Configurar el temporizador para leer el ADC cada 1ms (1000Hz)
timer = Timer(0)
timer.init(period=1, mode=Timer.PERIODIC, callback=read_adc)

while True:
    cl, addr = s.accept()
    print('Cliente conectado desde', addr)
    client_socket = cl
    while client_socket:
        utime.sleep_ms(1)  # Evitar el uso intensivo de la CPU