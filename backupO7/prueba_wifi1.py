import socket
import time


# Dirección IP del ESP32 (reemplaza con la dirección IP del ESP32)
esp32_ip = '192.168.1.109'
port = 80

# Conectar al ESP32 usando sockets
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((esp32_ip, port))
print(f"Conectado al ESP32 en {esp32_ip}:{port}")

# Recibir datos continuamente y procesarlos
try:
    while True:
        start_time_freq = time.time()
        data = s.recv(1024)  # Recibir datos en bloques de hasta 1024 bytes
        elapsed_time_fre = time.time() - start_time_freq
        try:
            if data:
                data_str = data.decode('utf-8')
                data_str = data_str.strip()
                data_list = data_str.split(',')
                # Convertir cada valor a float (si es necesario trabajar con números)
                data_list = [float(x) for x in data_list]
                print(data_list)
                print(elapsed_time_fre)
                #print(data.decode())  # Decodificar y mostrar los datos recibidos
            else:
                pass
        except:
            pass
except KeyboardInterrupt:
    print("Conexión terminada")
finally:
    s.close()
