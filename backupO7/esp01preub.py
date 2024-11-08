import requests
import time


ESP_IP = "http://192.168.1.110"  # IP del ESP01

def control_pin(pin, state):
    url = f"{ESP_IP}/control"
    params = {'pin': pin, 'state': state}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        print(f"Pin {pin} turned {state}")
    else:
        print("Error:", response.text)

# Ejemplos para encender y apagar los pines
control_pin(0, "ON")   # Enciende el pin 0
time.sleep(1)
control_pin(1, "ON")   # Enciende el pin 1
time.sleep(1)
control_pin(3, "ON")  # Apaga el pin 3
time.sleep(1)
control_pin(0, "OFF")   # Enciende el pin 0
time.sleep(1)
control_pin(1, "OFF")   # Enciende el pin 1
time.sleep(1)
control_pin(3, "OFF")  # Apaga el pin 3
time.sleep(1)