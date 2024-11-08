import serial
import time


ser = serial.Serial('COM6', baudrate=115200, timeout=1)

while True:
    line = ser.readline().decode('utf-8').strip()
    print(line)



