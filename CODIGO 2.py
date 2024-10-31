"""Segundo codigo usado, se le agrego funcion en base al tiempo, y aglunso algoritmos, se usa para ver los datos guardados"""


# PyQt5 para gui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QLabel, QSizePolicy, QSlider, QSpacerItem, QVBoxLayout, QWidget,
                             QCheckBox)

# Qt pyqtgraph para graficos, compatible con widgents de PyQt5
from pyqtgraph.Qt import QtCore

# pyqt para graficos y numpy para operaciones matematicas
import pyqtgraph as pg
import numpy as np

# thread para ejecuciones paralelas, sys para modificar archivos del sistema operativo, serial para comunicacion serial
import threading
import sys
import serial

# scipy para procesado de señal
from scipy.signal import butter, lfilter, iirnotch

# time para cronometrar partes del codigo
import time

# os para interactuar con archivos y datetime para fecha
import os
from datetime import datetime


# funcion creacion del archivo
def create_file(file_name):
    # valores hacia la carpeta datos, si no existe se crea
    directory = os.path.join(os.getcwd(), 'datos')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # fecha y hora actual
    current_time = datetime.now().strftime("%H%M_%d%m")

    # ruta completa del archivo
    file_path = os.path.join(directory, f"{current_time}_{file_name}.txt")

    print(f"Creating file: {file_path}")

    # abrir archivo en modo append para agregar datos
    file = open(file_path, 'a')
    return file


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
        self.minimum = minimum
        self.maximum = maximum
        self.slider.setValue(int(((float(initial_value)) - self.minimum) * (99 / (self.maximum - self.minimum))))

        self.horizontalLayout.addWidget(self.slider)
        self.spacerItem1 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addSpacerItem(self.spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.resize(self.sizeHint())

        self.minimum = minimum  # valor minimo para slider
        self.maximum = maximum  # valor maximo para slider
        self.slider.valueChanged.connect(self.setlabelvalue)  # conectar con funcion de cambio de label
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
    def __init__(self,filename,port=None):
        super(Scope, self).__init__()

        self.horizontalLayout = QHBoxLayout(self)

        # Crear Layout para GUI
        self.horizontalLayoutSliders = QHBoxLayout(self)
        self.horizontalLayautcheckmarks = QHBoxLayout(self)
        self.verticalLayoutcontrols = QVBoxLayout(self)

        # Checkboxes
        self.lowpass_checkbox = QCheckBox("Lowpass Filter", self)
        self.lowpass_checkbox.setChecked(True)
        self.horizontalLayautcheckmarks.addWidget(self.lowpass_checkbox)
        self.highpass_checkbox = QCheckBox("Highpass Filter", self)
        self.highpass_checkbox.setChecked(True)
        self.horizontalLayautcheckmarks.addWidget(self.highpass_checkbox)
        self.notch_checkbox = QCheckBox("Notch Filter", self)
        self.notch_checkbox.setChecked(True)
        self.horizontalLayautcheckmarks.addWidget(self.notch_checkbox)
        self.verticalLayoutcontrols.addLayout(self.horizontalLayautcheckmarks)

        # Create sliders
        self.xRange_slider = Slider(1, 2000, 1000)
        self.xRange_slider.setFixedSize(50, 300)  # Fixed size for slider
        self.horizontalLayoutSliders.addWidget(self.xRange_slider)
        self.lowpass_slider = Slider(0, 150, 30)
        self.lowpass_slider.setFixedSize(50, 300)  # Fixed size for slider
        self.horizontalLayoutSliders.addWidget(self.lowpass_slider)
        self.highpass_slider = Slider(0.00001, 5, 5)
        self.highpass_slider.setFixedSize(50, 300)  # Fixed size for slider
        self.horizontalLayoutSliders.addWidget(self.highpass_slider)
        self.notch_slider = Slider(30, 100, 50)
        self.notch_slider.setFixedSize(50, 300)  # Fixed size for slider
        self.horizontalLayoutSliders.addWidget(self.notch_slider)


        self.verticalLayoutcontrols.addLayout(self.horizontalLayoutSliders)

        controls_container = QWidget()
        controls_container.setLayout(self.verticalLayoutcontrols)
        controls_container.setFixedSize(300,500)  # Set a fixed size for the controls container
        self.horizontalLayout.addWidget(controls_container)



        # Crear el espacio donde va a estar el grafico
        self.win = pg.GraphicsLayoutWidget(show=True, title="ECG Scope")
        self.verticalLayoutgraphs = QHBoxLayout(self)
        self.verticalLayoutgraphs.addWidget(self.win)
        self.horizontalLayout.addLayout(self.verticalLayoutgraphs)
        self.win.resize(1280, 720)
        self.win.setWindowTitle('Real-time ECG Data')

        # Agregar el grafico principal
        self.main_plot = self.win.addPlot(title="ECG Signal")

        self.y_min = 1.1  # maximos y minimos del eje y
        self.y_max = 2.5
        self.main_plot.setYRange(self.y_min, self.y_max)

        self.main_plot.setLabel('left', 'ECG Value', '')
        self.main_plot.setLabel('bottom', 'Time', 's')
        self.Fs = 680  # setear la frecuencia de sampleo, cuantos datos le llegan por segundo
        self.sample_interval = 1 / self.Fs  # intervalo de sampleo

        self.graph = self.main_plot.plot()  # Crear objeto para el main plot

        self.win.nextRow()  # mover constructor del grafico a la siguiente columna
        self.fft_plot = self.win.addPlot(title="FFT of Raw Data")  # crear segunda grafica para fft
        self.fft_plot.setLabel('left', 'Magnitude', '')
        self.fft_plot.setLabel('bottom', 'Frequency', 'Hz')



        self.c = 0  # Contador para viewer
        self.buffer_size = 2000  # tamaño del buffer para datos
        self.data = np.zeros(self.buffer_size)  # Inicializar un array de 0's [0,0,0, . . . ,0,0,0]
        self.ptr = 0  # puntero para el buffer (posicion)

        self.c1 = 0  # Contador para viewer
        self.buffer_size1 = 1000  # tamaño del buffer para datos
        self.data1 = np.zeros(self.buffer_size)  # Inicializar un array de 0's [0,0,0, . . . ,0,0,0]
        self.ptr1 = 0  # puntero para el buffer (posicion)


        self.fft_sample_size = 1000  # tamaño de muestra para fft
        self.fft_padding = 5  # padding para calculos (agrega puntos a la señal)
        self.fft_freq = np.fft.rfftfreq(self.fft_sample_size * self.fft_padding,
                                        1 / self.Fs)  # Calcular frecuencias del fft
        self.fft_graph = self.fft_plot.plot()  # crear objeto para el fft
        self.fft_graph_fft_mag = np.zeros(int((
                                                      self.fft_sample_size * self.fft_padding) / 2) + 1)
        # array
        # para almacentar valores de magnitud (para graficar)



        self.a_low = None
        self.b_low = None
        self.a_high = None
        self.b_high = None
        self.a_notch = None
        self.b_notch = None
        self.lowpass_cutoff = None
        self.highpass_cutoff = None
        self.notch_freq = None

        self.last_state = 0
        self.start_time = 0
        self.change_time = 0  # Almacena el momento de cambio a 1 o -1


        self.current_time=0
        self.filen=filename
        #print(port)
        #  Codigo normal, requiere puerto serial
        if port:
            # Inicializar puerto serial y thread
            # timer a 100ms  conectada con funcion update

            #file_name = input("Enter the name of the text file: ")
            file_name = "prueba1"

            self.file = create_file(file_name)
            self.port = port
            self.ser = serial.Serial(self.port, baudrate=115200, timeout=1)
            self.serial_thread = threading.Thread(target=self.serial_read, daemon=True)
            self.plot_timer = QtCore.QTimer()
            self.plot_timer.timeout.connect(self.update_plot)
            self.plot_timer.start(100)

        # Codigo para viewer, necesita lista de datos
        else:
            # inicializar lista, thread y timer de 2ms conectada con funcion update
            #file_name = input("Enter the name of the text file for simulation: ")
            file_name = f'{self.filen}.txt'
            self.simulation_file_path = os.path.join('datos', file_name)


            self.simulation_thread = threading.Thread(target=self.simulate_data, daemon=True)
            self.plot_timer = QtCore.QTimer()
            self.plot_timer.timeout.connect(self.update_plot)
            self.plot_timer.start(1)

        # Conectar sliders A FUNCION DE ACTUALIZACION
        self.lowpass_checkbox.stateChanged.connect(self.update_filters)
        self.highpass_checkbox.stateChanged.connect(self.update_filters)
        self.notch_checkbox.stateChanged.connect(self.update_filters)
        self.xRange_slider.slider.valueChanged.connect(self.update_x_range)
        self.lowpass_slider.slider.valueChanged.connect(self.update_filters)
        self.highpass_slider.slider.valueChanged.connect(self.update_filters)
        self.notch_slider.slider.valueChanged.connect(self.update_filters)

        # actualizar filtros y x rango con valores iniciales
        self.update_filters()
        self.update_x_range()

    def funcion_uno(self):
        # Simula la primera acción
        print("Función 1 ejecutada")

    def funcion_dos(self):
        # Simula la segunda acción
        print("Función 2 ejecutada")

    def funcion_3(self):
        # Simula la tercera acción
        print("Función 3 ejecutada")

    def funcion_1(self):
        print("Ejecutando función 1")

    def funcion_menos1(self):
        print("Ejecutando función -1")

    # Funcion con la que empieza el scope, comienza los threads
    def start(self):
        if hasattr(self, 'serial_thread'):  # hasattr verifica si la funcion tiene el atributo serial thread
            self.serial_thread.start()
        else:
            self.simulation_thread.start()
        app.exec_()

    # Funcion de leer data por lista
    def simulate_data(self):



        data_count = 0
        boolean=True
        first_one=False
        current_time_pol=0
        with open(self.simulation_file_path, 'r') as file:
            while True:

                line = file.readline().strip()
                if not line:
                    file.seek(0)
                    line = file.readline().strip()
                try:
                    self.current_time, value = map(float, line.split(','))
                    if first_one==False:
                        current_time_pol=self.current_time
                        first_one=True

                except ValueError:
                    continue

                if self.ptr < self.buffer_size:
                    self.data[self.ptr] = value
                    self.ptr += 1
                    data_count += 1


                else:
                    self.data[:-1] = self.data[1:]
                    self.data[-1] = value
                    data_count += 1
                self.c += 1

                if self.c >= 1000:
                    self.c = 0

                elapsed_time = self.current_time - current_time_pol
                if elapsed_time >= 5.0:
                    print(f"Tasa de datos: {data_count / 5} por segundo")
                    self.Fs = int(data_count / 5)
                    #self.fft_freq = np.fft.rfftfreq(self.fft_sample_size * self.fft_padding, 1 / self.Fs)
                    data_count = 0
                    current_time_pol=self.current_time


                    #start_time = time.time()






                if boolean:
                    QtCore.QThread.msleep(1000)
                    boolean=False
                else:
                    QtCore.QThread.usleep(800)



    # Funcion de leer data por el puerto serial
    def serial_read(self):
        self.ser.reset_input_buffer()
        really_start_time = time.time()
        start_time = time.time()


        data_count = 0

        while True:
            line = self.ser.readline().decode('utf-8').strip()
            self.current_time = time.time()-really_start_time




            for value in line.split(','):

                try:
                    value = float(value)
                    if self.ptr < self.buffer_size:
                        self.data[self.ptr] = value
                        self.ptr += 1
                        data_count += 1
                        self.file.write(f"{self.current_time:.4f},{value}\n")
                        self.file.flush()
                    else:
                        self.data[:-1] = self.data[1:]
                        self.data[-1] = value
                        data_count += 1
                        self.file.write(f"{self.current_time:.4f},{value}\n")
                        self.file.flush()
                except Exception as e:
                        print(f"Error al leer datos: {e}")

            elapsed_time = time.time() - start_time
            if elapsed_time >= 5.0:
                print(f"Tasa de datos: {data_count/5} por segundo")
                self.Fs = int(data_count/5)
                self.fft_freq = np.fft.rfftfreq(self.fft_sample_size * self.fft_padding,1 / self.Fs)
                data_count = 0
                start_time = time.time()


    def update_plot(self):
        filtered_data = self.apply_filters(
            self.data[:self.ptr] if self.ptr < self.buffer_size else self.data)






        #print("start_time0: ", self.current_time)
        # Estado 0 mantenido


        time_values = np.linspace(0+self.current_time, (self.ptr / self.Fs)+self.current_time, self.ptr)

        self.graph.setData(time_values, filtered_data)
        #self.graph2.setData(, np.mean(filtered_data))
        self.main_plot.setXRange(time_values[0], time_values[-1])

        if self.ptr >= self.fft_sample_size:
            self.calc_fft(filtered_data[-self.fft_sample_size:])




    # Actualizar el rango x desde el slider, cambiar el tamaño del buffer,
    def update_x_range(self):
        new_buffer_size = int(self.xRange_slider.x)
        if new_buffer_size != self.buffer_size:
            self.buffer_size = new_buffer_size
            self.fft_sample_size = new_buffer_size
            self.data = np.zeros(self.buffer_size)
            self.ptr = 0
            self.fft_freq = np.fft.rfftfreq(self.fft_sample_size * self.fft_padding, 1 / self.Fs)
            self.fft_graph_fft_mag = np.zeros(int((self.fft_sample_size * self.fft_padding) / 2) + 1)

    def detect_alpha_peak(self,fft_values, freq_range, alpha_range=(8, 12)):
        # Extraer las frecuencias y potencias dentro del rango alfa
        alpha_indices = np.where((freq_range >= alpha_range[0]) & (freq_range <= alpha_range[1]))
        alpha_power = np.mean(fft_values[alpha_indices])

        # Comparar con las potencias fuera de la banda alfa
        non_alpha_power = np.mean(fft_values[np.setdiff1d(range(len(freq_range)), alpha_indices)])

        # Definir el umbral de detección (ajustable)
        threshold = 20 * non_alpha_power
        #print(threshold)

        if alpha_power > threshold:
            return True, alpha_power
        else:
            return False, alpha_power



    # Funcion para actualizar los coeficientes de los filtros digitales por medio de los sldiers
    # noinspection PyTupleAssignmentBalance
    def update_filters(self):
        self.lowpass_cutoff = self.lowpass_slider.x
        self.highpass_cutoff = self.highpass_slider.x
        self.notch_freq = self.notch_slider.x
        # frecuencia de corte debe estar entre 0 y la mitad de la frecuencia de sampleo
        # Filtro butterworth
        # orden del filtro, frecuencia de corte normalizada y el tipo
        # La Q del filtro notch es el factor de calidad, un valor mas alto significa un rechazo mas estrecho
        if 0 < self.lowpass_cutoff < 0.5 * self.Fs and 0 < self.highpass_cutoff < 0.5 * self.Fs:
            self.b_low, self.a_low = butter(5, self.lowpass_cutoff / (0.5 * self.Fs), btype='low')
            self.b_high, self.a_high = butter(5, self.highpass_cutoff / (0.5 * self.Fs), btype='high')
            self.b_notch, self.a_notch = iirnotch(self.notch_freq / (0.5 * self.Fs), 1)

    # Funcion para aplicar filtros a los datos
    def apply_filters(self, data):
        filtered_data = data
        if self.highpass_checkbox.isChecked():
            filtered_data = lfilter(self.b_high, self.a_high, filtered_data)
        if self.lowpass_checkbox.isChecked():
            filtered_data = lfilter(self.b_low, self.a_low, filtered_data)
        if self.notch_checkbox.isChecked():
            filtered_data = lfilter(self.b_notch, self.a_notch, filtered_data)
        return filtered_data

    # Funcion para caluclar y graficar la fft
    def calc_fft(self, data):
        data = data - np.mean(data)  # Eliminar componente dc

        # Moudela la señal con una ventana de hamming, para suavizala y evitar "leakage"
        ham = np.hamming(self.fft_sample_size)
        y_ham = data * ham
        fft_values = 4 / self.fft_sample_size * np.abs(
            np.fft.rfft(y_ham, self.fft_sample_size * self.fft_padding)
        )

        # Detección de pico alfa
        peak_detected, alpha_power = self.detect_alpha_peak(fft_values, self.fft_freq)

        # Graficar FFT
        self.fft_graph.setData(self.fft_freq, fft_values)

        # Resaltar si se detecta pico alfa (puedes agregar una indicación visual)
        if peak_detected:
            print(f"Alfa detectada: Potencia = {alpha_power:.4f}, {self.current_time}")
            self.main_plot.setTitle(f"¡Pico Alfa Detectado! Potencia = {alpha_power:.4f}")
        else:
            self.main_plot.setTitle("Sin pico alfa detectado")

    def exit(self):
        self.ser.close()
        self.file.close()  # Cerrar el archivo al salir
        sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    scope = Scope("220257_2810_EEG")
    scope.show()
    scope.start()




