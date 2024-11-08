import matplotlib.pyplot as plt
import numpy as np

# Lista de datos
data = [
    0, 0, 0, 0, 63, 56, 33, 11, 0, 0, 5, 69, 80, 41, 7, 19, 83, 5, 0, 72, 87, 88, 86,
    51, 0, 31, 87, 89, 8, 16, 87, 6, 1, 71, 43, 14, 82, 87, 86, 72, 88, 40, 12, 85,
    33, 65, 70, 56, 69, 86, 87, 87, 62, 13, 50, 69, 76, 0, 31, 34, 0, 0, 13, 84, 0,
    0, 43, 85, 85, 22, 37, 0, 0, 0, 0, 10, 0, 4, 77, 35, 0, 0, 0, 0, 0, 0, 29, 89,
    9, 21, 30, 57, 83, 79, 86, 51, 84, 88, 87, 80, 86, 75, 67, 58, 14, 86, 88, 86,
    86, 41, 36, 88, 76, 0, 0, 60, 88, 76, 3, 76, 62, 22, 89, 37, 0, 0, 32, 5, 2, 72,
    25, 3, 68, 86, 43, 23, 86, 86, 55, 88, 44, 37, 89, 89, 89, 85, 62, 20, 0, 31, 0,
    5, 18, 39, 19, 6, 84, 36, 19, 0, 0, 0, 0, 71, 20, 2, 8, 0, 15, 29, 25, 5, 87, 89,
    88, 80, 88, 86, 89, 86, 88, 5, 7, 0, 35, 88, 86, 85, 25, 53, 86, 78, 58, 33, 36,
    10, 73, 42, 0, 36, 17, 29, 84, 64, 87, 59, 0, 0, 10, 89
]


# Cálculo de la media acumulativa de los últimos 20 valores
mean_values_last_20 = [np.mean(data[max(0, i-19):i+1]) for i in range(len(data))]

percentage_mapped_mean_values = [
    ((value - min(mean_values_last_20[max(0, i-19):i+1])) /
     (max(mean_values_last_20[max(0, i-19):i+1]) - min(mean_values_last_20[max(0, i-19):i+1])) * 100)
    if max(mean_values_last_20[max(0, i-19):i+1]) != min(mean_values_last_20[max(0, i-19):i+1]) else 0
    for i, value in enumerate(mean_values_last_20)
]

# Muestra los primeros 20 valores de la lista transformada como ejemplo


# Graficar los datos y las medias acumulativas de los últimos 20 valores
plt.figure(figsize=(14, 7))

# Gráfica de los datos originales
plt.plot(data, label="Datos Originales", color="gray", alpha=0.7, linestyle="--")

# Gráfica de las medias acumulativas de los últimos 20 valores
plt.plot(mean_values_last_20, label="Media Acumulativa (Últimos 20)", color="b")

plt.plot(percentage_mapped_mean_values, label="percentage", color="r")
# Configuraciones adicionales de la gráfica
plt.title("Datos Originales y Media Acumulativa de los Últimos 20 Valores")
plt.xlabel("Cantidad de datos considerados")
plt.ylabel("Valor")
plt.legend()
plt.grid(True)
plt.show()
