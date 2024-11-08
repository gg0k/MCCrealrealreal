import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# Datos del problema
IDSS = 10e-3  # Corriente IDSS en Amperios
VP = -3  # Voltaje pinch-off (V_P) en Volts
RD = 2e3  # Resistencia de drenaje (R_D) en Ohms
VDD = 15  # Voltaje de alimentación (V_DD) en Volts
RS = 240  # Resistencia de la fuente (R_S) en Ohms

# Función no lineal para la corriente ID en función de VGS
def equation(ID):
    VGS = -ID * RS  # Voltaje puerta-fuente
    return IDSS * (1 - VGS / VP)**2 - ID

# Encontramos la corriente IDQ iterativamente
IDQ_guess = 5e-3  # Suposición inicial
IDQ = fsolve(equation, IDQ_guess)[0]

# Calculo de V_GSQ (Voltaje puerta-fuente en el punto quiescente)
VGSQ = -IDQ * RS

# Calculo de V_DSQ (Voltaje drenaje-fuente en el punto quiescente)
VDSQ = VDD - IDQ * (RD + RS)

print(IDQ, VGSQ, VDSQ)

# Definimos el rango de VDS y VGS
VDS_range = np.linspace(0, VDD, 200)
VGS_values = [-2, -3, -4, -5, -6]  # Algunos valores de VGS para las curvas

# Función para la curva característica de ID en función de VDS
def ID_vs_VDS(VDS, VGS):
    if VGS >= VP:
        return 0  # En corte
    else:
        if VDS <= VGS - VP:  # Región lineal
            return IDSS * ((1 - VGS / VP)**2) * (VDS / (VGS - VP))
        else:  # Región de saturación
            return IDSS * (1 - VGS / VP)**2

# Calculamos las curvas características de salida (ID vs VDS)
ID_curves = []
for VGS in VGS_values:
    ID_curves.append([ID_vs_VDS(VDS, VGS) for VDS in VDS_range])

# Recta de carga
VDS_line = np.linspace(0, VDD, 200)
ID_line = (VDD - VDS_line) / (RD + RS)

# Gráfico de la característica de salida
plt.figure(figsize=(10, 6))
for i, VGS in enumerate(VGS_values):
    plt.plot(VDS_range, ID_curves[i], label=f'VGS = {VGS} V')

plt.plot(VDS_line, ID_line, 'r--', label='Recta de carga (Punto Q)')
plt.scatter(VDSQ, IDQ, color='red', zorder=5, label=f'Punto Q (VDSQ={VDSQ:.2f} V, IDQ={IDQ*1e3:.2f} mA)')

plt.title('Curva característica de salida (ID vs VDS)')
plt.xlabel('VDS (V)')
plt.ylabel('ID (A)')
plt.grid(True)
plt.legend()
plt.show()

# Gráfico de VGS vs ID
VGS_range = np.linspace(-6, 0, 200)
ID_vs_VGS = [IDSS * (1 - VGS / VP)**2 if VGS < VP else 0 for VGS in VGS_range]

plt.figure(figsize=(8, 6))
plt.plot(VGS_range, ID_vs_VGS, label='ID vs VGS')
plt.scatter(VGSQ, IDQ, color='red', zorder=5, label=f'Punto Q (VGSQ={VGSQ:.2f} V, IDQ={IDQ*1e3:.2f} mA)')

plt.title('Curva de transferencia (ID vs VGS)')
plt.xlabel('VGS (V)')
plt.ylabel('ID (A)')
plt.grid(True)
plt.legend()
plt.show()
