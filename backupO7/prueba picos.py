# Datos de ejemplo
data = [
    0, 0, 0, 0, 63, 54, 60, 59, 28, 29, 23, 20, 29, 60, 43, 45, 59, 55, 44, 16, 25, 32, 40, 41, 55,
    45, 22, 33, 29, 12, 3, 16, 25, 32, 35, 56, 66, 60, 67, 64, 29, 35, 50, 57, 60, 60, 52, 56, 50,
    49, 59, 46, 39, 37, 35, 25, 42, 50, 23, 32, 42, 25, 13, 28, 29, 3, 9, 40, 55, 45, 40, 53, 40, 47,
    50, 50, 45, 48, 61, 41, 47, 53, 36, 11, 13, 50, 57, 53, 60, 64, 60, 57, 51, 59, 47, 60, 64, 45,
    46, 36, 68, 38, 14, 46, 50, 50, 43, 24, 61, 58, 16, 15, 10, 0, 33, 50, 39, 17, 11, 34, 46, 49, 38,
    55, 49, 33, 44, 25, 42, 56, 36, 55, 14, 24, 14, 1, 11, 71, 64, 12, 11, 58, 58, 44, 3, 0, 19, 34,
    17, 64, 26, 37, 39, 8, 28, 42, 43, 50, 47, 32, 47, 1, 23, 61, 35, 53, 62, 56, 56, 60, 51, 50, 49,
    47, 47, 40, 45, 23, 22, 27, 37, 43, 40, 40, 43, 50, 41, 40, 40, 31, 15, 5, 10, 39, 40, 39, 15, 8,
    49, 47, 47, 50, 50, 50, 41, 49, 50, 44, 36, 49, 11, 43, 59, 32, 44, 55, 61, 22, 4, 33, 24, 1, 29,
    40, 39, 37, 43, 50, 50, 41, 46, 45, 50, 50, 50, 52, 50, 50, 50, 50, 50, 47, 46, 53, 39, 41, 50, 41,
    40, 40, 37, 31, 37, 36, 4, 0, 49, 64, 36, 37, 31, 47, 59, 44, 60, 75, 44, 49, 50, 42, 23, 20, 13, 1,
    0, 0, 10, 42, 11, 72, 86, 36, 18, 24, 38, 35, 30, 38, 37, 55, 56, 27, 30, 42, 50, 49, 45, 41, 44,
    26, 45, 54, 59, 58, 65, 70, 40, 37, 10, 0, 40, 30, 0, 8, 0, 0, 0, 14, 54, 51, 35, 44, 58, 24, 33,
    34, 12, 47, 56, 55, 69, 65, 45, 13, 6, 29, 27
]


# Función para detectar picos prolongados
def detectar_picos_prolongados(data, threshold=20, min_prolongado=3):
    picos_prolongados = []
    i = 0

    while i < len(data):
        if data[i] < threshold:
            # Contar cuántos valores consecutivos están por debajo del umbral
            count = 1
            while i + 1 < len(data) and data[i + 1] < threshold:
                count += 1
                i += 1

            # Si se detecta un pico prolongado, agregarlo a la lista
            if count >= min_prolongado:
                picos_prolongados.append((i - count + 1, i + 1))  # Guardar el rango del pico

        i += 1

    return picos_prolongados


# Detectar picos prolongados
picos = detectar_picos_prolongados(data)

# Mostrar los picos detectados
if picos:
    print("Picos prolongados detectados en los siguientes intervalos:")
    for inicio, fin in picos:
        print(f"Desde el índice {inicio} hasta el índice {fin}: {data[inicio:fin]}")
else:
    print("No se detectaron picos prolongados.")