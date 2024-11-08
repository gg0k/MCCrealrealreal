import serial
import time
import threading

# Configurar el puerto serial con un timeout
ser = serial.Serial('COM7', 115200, timeout=1)

# Variables globales
c = 0
h = 0
sum = 0
start_time1 = time.time()


def serial_read():
    global c, h, sum, start_time1
    print("Hilo iniciado...")

    while True:
        start_time = time.time()
        try:

            # Leer datos del puerto serial
            data = ser.readline().decode('utf-8').strip()

            # Procesar datos si no es 1.679
            if data and (float(data) != 1.679):
                print("Data procesada:", data)
        except Exception as e:
            print(f"Error al leer datos: {e}")

        ept = time.time() - start_time
        sum += ept
        h += 1
        c += 1

        if c >= 1000:
            print("Promedio de tiempo:", sum / 1000)
            sum = 0
            c = 0

        ept1 = time.time() - start_time1
        if ept1 >= 5:
            start_time1 = time.time()
            print("Promedio en 5 segundos:", h / 5)
            h = 0


# Crear el hilo y comenzarlo
serial_thread = threading.Thread(target=serial_read, daemon=True)
serial_thread.start()

# Verificar si el hilo sigue vivo
while True:
    if not serial_thread.is_alive():
        print("El hilo terminó inesperadamente")
        break
    time.sleep(1)  # Esperar 1 segundo antes de verificar de nuevo
