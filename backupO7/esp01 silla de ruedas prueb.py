import requests
import tkinter as tk
from tkinter import messagebox

# Dirección IP del ESP
ESP_IP = "http://192.168.1.106"

# Función para enviar comandos a los motores
def control_motor(motor, action):
    url = f"{ESP_IP}/motor"
    params = {'motor': motor, 'action': action}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print(f"Motor {motor} acción: {action}")
        else:
            print("Error:", response.text)
            messagebox.showerror("Error", f"No se pudo realizar la acción: {response.text}")
    except requests.exceptions.RequestException as e:
        print("Error de conexión:", e)
        messagebox.showerror("Error de conexión", f"No se pudo conectar a {ESP_IP}")

# Funciones para controlar el movimiento del vehículo
def adelante():
    control_motor("1", "backward")
    control_motor("2", "backward")

def atras():
    control_motor("1", "forward")
    control_motor("2", "forward")

def derecha():
    control_motor("1", "backward")
    control_motor("2", "stop")

def izquierda():
    control_motor("1", "stop")
    control_motor("2", "backward")

def detener():
    control_motor("1", "stop")
    control_motor("2", "stop")

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Control de Vehículo RC")

# Botones de control
frame = tk.Frame(root)
frame.pack(pady=20)

tk.Button(frame, text="Adelante", command=adelante, width=10).grid(row=0, column=1, padx=10, pady=5)
tk.Button(frame, text="Izquierda", command=izquierda, width=10).grid(row=1, column=0, padx=10, pady=5)
tk.Button(frame, text="Detener", command=detener, bg="red", fg="white", font=("Arial", 12, "bold"), width=10).grid(row=1, column=1, padx=10, pady=5)
tk.Button(frame, text="Derecha", command=derecha, width=10).grid(row=1, column=2, padx=10, pady=5)
tk.Button(frame, text="Atrás", command=atras, width=10).grid(row=2, column=1, padx=10, pady=5)

# Ejecutar la interfaz gráfica
root.mainloop()

