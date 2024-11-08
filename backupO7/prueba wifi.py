import socket
import time

# Dirección IP y puerto del ESP32
host = '192.168.1.108'  # Reemplaza con la dirección IP del ESP32
port = 80

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))

try:
    start_time = time.time()
    data_count = 0

    while True:
        current_time = time.perf_counter()
        data = s.recv(1024).decode().strip()
        last_time = time.perf_counter()
        time_diff = last_time - current_time
        if data:
            values = data.split('\n')
            for value in values:
                if value:
                    parts = value.split(':')
                    if len(parts) == 1:
                        lectura = float(parts[0])
                        data_count += 1
                        print(f"Lectura ADC: {lectura}")

        # Calcular la tasa de datos
        elapsed_time = time.time() - start_time
        if elapsed_time >= 1.0:
            print(f"Tasa de datos: {data_count} por segundo")
            data_count = 0
            start_time = time.time()

except KeyboardInterrupt:
    print("Interrupción por el usuario")
finally:
    s.close()
    print("Socket cerrado")
