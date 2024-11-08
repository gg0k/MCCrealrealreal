# PyQt5 para gui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QSizePolicy, QSlider, QSpacerItem, QVBoxLayout, QWidget

# Qt pyqtgraph para graficos, compatible con widgents de PyQt5
from pyqtgraph.Qt import QtCore

# pyqt para graficos y numpy para operaciones matematicas
import pyqtgraph as pg
import numpy as np

# thread para ejecuciones paralelas, sys para modificar archivos del sistema operativo, serial para comunicacion serial
import threading
import sys
import serial


# time para cronometrar partes del codigo
import time


# custom slider class, hereda QWidget
# noinspection PyUnresolvedReferences
class Slider(QWidget):
    def __init__(self, minimum, maximum, initial_value, parent=None):
        super(Slider, self).__init__(parent=parent)
        self.verticalLayout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QHBoxLayout()
        self.spacerItem = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addSpacerItem(self.spacerItem)
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Vertical)
        self.slider.setValue(int(initial_value))
        self.horizontalLayout.addWidget(self.slider)
        self.spacerItem1 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addSpacerItem(self.spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.resize(self.sizeHint())

        self.minimum = minimum  # valor minimo para slider
        self.maximum = maximum  # valor maximo para slider
        self.slider.valueChanged.connect(self.setlabelvalue)  # conectar el valor del slider con el
        self.x = None  # inicializar variable para el valor del slider
        self.setlabelvalue(self.slider.value())

    # value=(0-99). setLabelValue mapea el valor entre los valores minimos y maximos
    # Y actualiza el label
    def setlabelvalue(self, value):
        self.x = self.minimum + (float(value) / (self.slider.maximum() - self.slider.minimum())) * (
                self.maximum - self.minimum)
        self.label.setText("{0:.4g}".format(self.x))


# custom clase Scope, hereda QWidget
# noinspection PyArgumentList
class Scope(QWidget):
    # Inicializar clase
    # noinspection PyUnresolvedReferences
    def __init__(self, puerto):
        super(Scope, self).__init__()


        self.highpass_cutoff = None
        self.notch_freq = None
        self.horizontalLayout = QHBoxLayout(self)
        # Crear sider para rango X
        self.xRange_slider = Slider(1, 1000, 100)
        self.horizontalLayout.addWidget(self.xRange_slider)
        # Crear sider para filtro pasa bajas, altas y filtro notch (50/60hz)

        self.highpass_slider = Slider(0.00001, 10, 0.00001)
        self.horizontalLayout.addWidget(self.highpass_slider)
        self.notch_slider = Slider(10, 100, 20)
        self.horizontalLayout.addWidget(self.notch_slider)

        # Crear el espacio donde va a estar el grafico
        self.win = pg.GraphicsLayoutWidget(show=True, title="ECG Scope")
        self.verticalLayoutgraphs = QHBoxLayout(self)
        self.verticalLayoutgraphs.addWidget(self.win)
        self.horizontalLayout.addLayout(self.verticalLayoutgraphs)
        self.win.resize(1280, 720)
        self.win.setWindowTitle('Real-time ECG Data')

        # Agregar el grafico principal de V(t)
        self.main_plot = self.win.addPlot(title="ECG Signal")
        self.y_min = 1.26  # maximos y minimos del eje y
        self.y_max = 2.35
        self.main_plot.setYRange(self.y_min, self.y_max)
        self.main_plot.setLabel('left', 'ECG Value', '')
        self.main_plot.setLabel('bottom', 'Time', 's')
        self.Fs = 250  # setear la frecuencia de sampleo, cuantos datos le llegan por segundo
        self.sample_interval = 1 / self.Fs  # intervalo de sampleo (4m)

        self.graph = self.main_plot.plot()  # Crear objeto para el main plot
        self.graph_pos = 0  # posicion del grafico (no se usa?)


        self.buffer_size = 1000  # tamaño del buffer para datos
        self.data = np.zeros(self.buffer_size)  # Inicializar un array de datos con 0
        self.ptr = 0  # puntero para el buffer (posicion)


        # array para almacentar valores de magnitud (para graficar)

        # Inicializar puerto serial y crear un thread para leerlo
        self.port = puerto
        self.ser = serial.Serial(self.port, baudrate=115200, timeout=1)
        self.serial_thread = threading.Thread(target=self.serial_read,
                                              daemon=True)  # deamon para que se ejecute y finalice durante el programa

        # Timer para actualizar el grafico cada 100ms, conectar el timer a la funcion update
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(100)




    # Funcion con la que empieza el scope
    def start(self):
        self.serial_thread.start()  # Comienza la lectura de la señal por el thread
        app.exec_()  # inicia la aplicacion

    # Funcion de leer data por el puerto serial
    def serial_read(self):
        self.ser.reset_input_buffer()  # Resetear el input buffer
        start_time = time.time()
        data_count = 0  # inicio del conteo para calcular la velocidad de los datos
        while True:
            line = self.ser.readline().decode('utf-8').strip()  # leer y decodificar linea desde puerto serial
            for value in line.split(','):  # dividir la linea en varios valores separados por ",'s"
                try:
                    value = float(value)
                    if self.ptr < self.buffer_size:  # si el puntero es menor al tamaño del buffer puntero < 1000
                        self.data[self.ptr] = value  # guardarlo en el buffer
                        self.ptr += 1  # incremento del puntero del buffer
                        data_count += 1  # incremento del conteo de datos
                    else:
                        self.data[:-1] = self.data[1:]  # mover el buffer
                        self.data[-1] = value  # guardar nuevo valor en el final
                        data_count += 1  # incremento del conteo de datos
                except ValueError:
                    pass
            # Calcular el tiempo transcurrido, si paso 1 segundo, data_count es la nuevo frecuencia de muestreo

            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                print(f"Tasa de datos: {data_count} por segundo")
                self.Fs = data_count
                data_count = 0
                start_time = time.time()


    # Funcion para actualizar la grafica, primero se aplican los filtros, se pasa los datos a la grafica
    # Se posiciona el rango x, entre 0 y 1000 p 100 y 1000
    # y si hay suficiente data se calcula el fft
    def update_plot(self):
        data = self.data[:self.ptr] if self.ptr < self.buffer_size else self.data
        self.graph.setData(data)
        self.main_plot.setXRange(max(0, self.ptr - self.buffer_size), self.ptr)


    # Actualizar el rango x desde el slider, cambiar el tamaño del buffer,
    def update_x_range(self):
        new_buffer_size = int(self.xRange_slider.x)
        if new_buffer_size != self.buffer_size:
            self.buffer_size = new_buffer_size
            self.data = np.zeros(self.buffer_size)

    # Funcion para actualizar los coeficientes de los filtros digitales por medio de los sldiers
    # noinspection PyTupleAssignmentBalance

    def exit(self):
        self.serial.close()
        sys.exit()


# Main program
if __name__ == '__main__':
    app = QApplication(sys.argv)
    port = 'COM6'  # Asignar puerto serial del sistema
    scope = Scope(port)
    scope.show()
    scope.start()
