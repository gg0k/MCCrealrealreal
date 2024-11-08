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
    def __init__(self, port=None):
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
        self.highpass_checkbox.setChecked(False)
        self.horizontalLayautcheckmarks.addWidget(self.highpass_checkbox)
        self.notch_checkbox = QCheckBox("Notch Filter", self)
        self.notch_checkbox.setChecked(True)
        self.horizontalLayautcheckmarks.addWidget(self.notch_checkbox)
        self.verticalLayoutcontrols.addLayout(self.horizontalLayautcheckmarks)

        # Crear slider para rango X
        self.xRange_slider = Slider(1, 1000, 1000)
        self.horizontalLayoutSliders.addWidget(self.xRange_slider)
        # Crear sider para filtro pasa bajas, altas y filtro notch (50/60hz)
        self.lowpass_slider = Slider(35, 150, 100)
        self.horizontalLayoutSliders.addWidget(self.lowpass_slider)
        self.highpass_slider = Slider(0.00001, 1, 0.00001)
        self.horizontalLayoutSliders.addWidget(self.highpass_slider)
        self.notch_slider = Slider(40, 50, 45)
        self.horizontalLayoutSliders.addWidget(self.notch_slider)

        self.verticalLayoutcontrols.addLayout(self.horizontalLayoutSliders)
        self.horizontalLayout.addLayout(self.verticalLayoutcontrols)

        # Crear el espacio donde va a estar el grafico
        self.win = pg.GraphicsLayoutWidget(show=True, title="ECG Scope")
        self.verticalLayoutgraphs = QHBoxLayout(self)
        self.verticalLayoutgraphs.addWidget(self.win)
        self.horizontalLayout.addLayout(self.verticalLayoutgraphs)
        self.win.resize(1280, 720)
        self.win.setWindowTitle('Real-time ECG Data')

        # Agregar el grafico principal
        self.main_plot = self.win.addPlot(title="ECG Signal")
        self.y_min = 1.26  # maximos y minimos del eje y
        self.y_max = 2.35
        self.main_plot.setYRange(self.y_min, self.y_max)
        self.main_plot.setLabel('left', 'ECG Value', '')
        self.main_plot.setLabel('bottom', 'Time', 's')
        self.Fs = 250  # setear la frecuencia de sampleo, cuantos datos le llegan por segundo
        self.sample_interval = 1 / self.Fs  # intervalo de sampleo

        self.graph = self.main_plot.plot()  # Crear objeto para el main plot
        self.graph_pos = 0  # posicion del grafico

        self.win.nextRow()  # mover constructor del grafico a la siguiente columna
        self.fft_plot = self.win.addPlot(title="FFT of Raw Data")  # crear segunda grafica para fft
        self.fft_plot.setLabel('left', 'Magnitude', '')
        self.fft_plot.setLabel('bottom', 'Frequency', 'Hz')

        self.c = 0  # Contador para viewer
        self.buffer_size = 1000  # tamaño del buffer para datos
        self.data = np.zeros(self.buffer_size)  # Inicializar un array de 0's [0,0,0, . . . ,0,0,0]
        self.ptr = 0  # puntero para el buffer (posicion)

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

        #  Codigo normal, requiere puerto serial
        if port:
            # Inicializar puerto serial y thread
            # timer a 100ms  conectada con funcion update
            file_name = input("Enter the name of the text file: ")
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
            self.lista_data = [1.62, 1.61, 1.45, 1.33, 1.38, 1.5, 1.64, 1.58, 1.38, 1.33, 1.44, 1.62, 1.61, 1.38, 1.33,
                               1.38, 1.57, 1.63, 1.52, 1.38, 1.33, 1.44, 1.62, 1.61, 1.51, 1.33, 1.35, 1.51, 1.64, 1.61,
                               1.44, 1.32, 1.38, 1.58, 1.64, 1.51, 1.33, 1.35, 1.45, 1.63, 1.57, 1.37, 1.33, 1.44, 1.62,
                               1.56, 1.44, 1.32, 1.39, 1.58, 1.63, 1.56, 1.37, 1.33, 1.45, 1.63, 1.63, 1.5, 1.33, 1.35,
                               1.52, 1.63, 1.61, 1.43, 1.33, 1.39, 1.52, 1.64, 1.56, 1.36, 1.34, 1.39, 1.59, 1.62, 1.5,
                               1.33, 1.34, 1.45, 1.63, 1.6, 1.42, 1.33, 1.36, 1.53, 1.64, 1.6, 1.42, 1.32, 1.39, 1.59,
                               1.64, 1.56, 1.36, 1.34, 1.46, 1.63, 1.6, 1.42, 1.33, 1.4, 1.36, 1.36, 1.46, 1.63, 1.59,
                               1.41, 1.32, 1.36, 1.53, 1.64, 1.55, 1.35, 1.32, 1.4, 1.6, 1.62, 1.48, 1.33, 1.34, 1.47,
                               1.64, 1.6, 1.41, 1.33, 1.36, 1.54, 1.64, 1.55, 1.41, 1.33, 1.41, 1.6, 1.62, 1.55, 1.35,
                               1.34, 1.48, 1.64, 1.62, 1.47, 1.32, 1.37, 1.55, 1.64, 1.54, 1.35, 1.34, 1.41, 1.64, 1.59,
                               1.4, 1.33, 1.37, 1.55, 1.64, 1.54, 1.4, 1.33, 1.41, 1.61, 1.59, 1.4, 1.33, 1.42, 1.61,
                               1.64, 1.54, 1.35, 1.34, 1.49, 1.64, 1.59, 1.39, 1.33, 1.37, 1.56, 1.64, 1.54, 1.34, 1.33,
                               1.42, 1.62, 1.62, 1.53, 1.34, 1.35, 1.49, 1.64, 1.62, 1.46, 1.32, 1.37, 1.56, 1.64, 1.58,
                               1.39, 1.33, 1.43, 1.56, 1.64, 1.5, 1.64, 1.52, 1.34, 1.35, 1.43, 1.62, 1.61, 1.45, 1.32,
                               1.35, 1.5, 1.64, 1.58, 1.45, 1.32, 1.38, 1.62, 1.63, 1.52, 1.33, 1.35, 1.5, 1.64, 1.58,
                               1.45, 1.32, 1.38, 1.57, 1.63, 1.57, 1.37, 1.33, 1.44, 1.63, 1.61, 1.51, 1.33, 1.35, 1.51,
                               1.64, 1.61, 1.44, 1.32, 1.39, 1.58, 1.64, 1.57, 1.37, 1.33, 1.45, 1.58, 1.63, 1.51, 1.33,
                               1.36, 1.45, 1.63, 1.61, 1.43, 1.33, 1.35, 1.52, 1.64, 1.57, 1.44, 1.33, 1.39, 1.59, 1.63,
                               1.56, 1.37, 1.34, 1.46, 1.64, 1.61, 1.5, 1.33, 1.36, 1.52, 1.64, 1.56, 1.43, 1.33, 1.4,
                               1.59, 1.63, 1.56, 1.37, 1.34, 1.46, 1.63, 1.63, 1.49, 1.33, 1.36, 1.53, 1.63, 1.6, 1.42,
                               1.55, 1.36, 1.34, 1.46, 1.64, 1.6, 1.42, 1.33, 1.36, 1.54, 1.64, 1.55, 1.41, 1.33, 1.41,
                               1.6, 1.64, 1.55, 1.35, 1.34, 1.47, 1.64, 1.63, 1.48, 1.33, 1.36, 1.54, 1.64, 1.54, 1.41,
                               1.33, 1.41, 1.61, 1.62, 1.48, 1.33, 1.36, 1.48, 1.64, 1.59, 1.41, 1.33, 1.37, 1.55, 1.64,
                               1.54, 1.4, 1.33, 1.41, 1.61, 1.62, 1.54, 1.35, 1.34, 1.48, 1.64, 1.59, 1.4, 1.33, 1.37,
                               1.56, 1.64, 1.54, 1.4, 1.33, 1.42, 1.62, 1.62, 1.53, 1.34, 1.34, 1.49, 1.64, 1.62, 1.47,
                               1.33, 1.37, 1.56, 1.64, 1.59, 1.39, 1.33, 1.38, 1.56, 1.64, 1.53, 1.34, 1.33, 1.43, 1.62,
                               1.62, 1.46, 1.34, 1.35, 1.5, 1.64, 1.58, 1.46, 1.33, 1.38, 1.33, 1.44, 1.62, 1.61, 1.45,
                               1.33, 1.35, 1.5, 1.64, 1.57, 1.38, 1.33, 1.38, 1.57, 1.63, 1.52, 1.38, 1.33, 1.44, 1.62,
                               1.61, 1.51, 1.34, 1.35, 1.51, 1.64, 1.57, 1.44, 1.33, 1.39, 1.58, 1.64, 1.51, 1.34, 1.35,
                               1.51, 1.64, 1.57, 1.38, 1.33, 1.44, 1.58, 1.63, 1.51, 1.33, 1.36, 1.45, 1.63, 1.6, 1.44,
                               1.33, 1.39, 1.58, 1.64, 1.56, 1.37, 1.34, 1.45, 1.59, 1.63, 1.5, 1.33, 1.36, 1.53, 1.64,
                               1.56, 1.43, 1.33, 1.4, 1.59, 1.64, 1.56, 1.37, 1.34, 1.46, 1.59, 1.63, 1.5, 1.33, 1.36,
                               1.46, 1.63, 1.6, 1.43, 1.33, 1.37, 1.53, 1.64, 1.56, 1.37, 1.33, 1.4, 1.59, 1.62, 1.49,
                               1.33, 1.34, 1.47, 1.64, 1.6, 1.54, 1.64, 1.55, 1.36, 1.34, 1.47, 1.6, 1.62, 1.49, 1.33,
                               1.37, 1.47, 1.64, 1.59, 1.41, 1.33, 1.41, 1.6, 1.64, 1.55, 1.36, 1.34, 1.48, 1.61, 1.62,
                               1.48, 1.33, 1.37, 1.48, 1.64, 1.59, 1.41, 1.33, 1.41, 1.54, 1.64, 1.54, 1.35, 1.35, 1.48,
                               1.61, 1.62, 1.47, 1.33, 1.37, 1.55, 1.64, 1.54, 1.4, 1.33, 1.42, 1.61, 1.64, 1.54, 1.35,
                               1.34, 1.49, 1.61, 1.62, 1.47, 1.33, 1.37, 1.55, 1.63, 1.58, 1.4, 1.33, 1.42, 1.61, 1.64,
                               1.47, 1.33, 1.35, 1.49, 1.64, 1.58, 1.39, 1.33, 1.38, 1.56, 1.64, 1.53, 1.39, 1.33, 1.43,
                               1.62, 1.62, 1.53, 1.34, 1.35, 1.5, 1.62, 1.61, 1.46, 1.33, 1.38, 1.5, 1.64, 1.58, 1.39,
                               1.64, 1.45, 1.34, 1.35, 1.51, 1.64, 1.58, 1.45, 1.33, 1.38, 1.57, 1.63, 1.58, 1.38, 1.33,
                               1.44, 1.63, 1.61, 1.45, 1.32, 1.39, 1.51, 1.65, 1.58, 1.38, 1.33, 1.38, 1.58, 1.63, 1.51,
                               1.38, 1.33, 1.58, 1.63, 1.57, 1.38, 1.34, 1.45, 1.63, 1.63, 1.51, 1.33, 1.36, 1.52, 1.63,
                               1.61, 1.44, 1.33, 1.39, 1.52, 1.64, 1.57, 1.37, 1.34, 1.39, 1.58, 1.63, 1.5, 1.37, 1.33,
                               1.45, 1.63, 1.6, 1.5, 1.33, 1.36, 1.52, 1.64, 1.61, 1.43, 1.32, 1.39, 1.53, 1.65, 1.56,
                               1.37, 1.34, 1.4, 1.59, 1.63, 1.5, 1.33, 1.34, 1.46, 1.63, 1.6, 1.5, 1.33, 1.36, 1.53,
                               1.64, 1.6, 1.42, 1.33, 1.4, 1.6, 1.64, 1.56, 1.36, 1.34, 1.42, 1.33, 1.4, 1.6, 1.63,
                               1.49, 1.36, 1.34, 1.47, 1.64, 1.6, 1.48, 1.33, 1.36, 1.54, 1.64, 1.6, 1.42, 1.33, 1.41,
                               1.61, 1.65, 1.55, 1.35, 1.34, 1.48, 1.64, 1.59, 1.41, 1.33, 1.41, 1.61, 1.63, 1.55, 1.35,
                               1.35, 1.48, 1.64, 1.62, 1.48, 1.33, 1.37, 1.48, 1.64, 1.59, 1.41, 1.33, 1.42, 1.56, 1.65,
                               1.54, 1.35, 1.34, 1.48, 1.61, 1.62, 1.47, 1.33, 1.37, 1.49, 1.65, 1.59, 1.4, 1.33, 1.37,
                               1.56, 1.64, 1.54, 1.4, 1.33, 1.42, 1.62, 1.63, 1.55, 1.34, 1.34, 1.49, 1.65, 1.63, 1.47,
                               1.32, 1.37, 1.57, 1.65, 1.54, 1.34, 1.32, 1.42, 1.63, 1.63, 1.54, 1.34, 1.34, 1.5, 1.66,
                               1.63, 1.47, 1.32, 1.37, 1.57, 1.32, 1.43, 1.63, 1.63, 1.46, 1.32, 1.37, 1.58, 1.66, 1.53,
                               1.38, 1.32, 1.43, 1.64, 1.66, 1.46, 1.32, 1.37, 1.58, 1.65, 1.59, 1.38, 1.32, 1.43, 1.64,
                               1.66, 1.53, 1.33, 1.34, 1.5, 1.66, 1.59, 1.45, 1.32, 1.37, 1.58, 1.65, 1.59, 1.37, 1.32,
                               1.43, 1.59, 1.66, 1.53, 1.33, 1.34, 1.51, 1.65, 1.63, 1.45, 1.31, 1.34, 1.51, 1.66, 1.59,
                               1.37, 1.31, 1.37, 1.59, 1.66, 1.52, 1.32, 1.34, 1.44, 1.65, 1.63, 1.44, 1.32, 1.37, 1.52,
                               1.67, 1.59, 1.36, 1.31, 1.38, 1.6, 1.66, 1.52, 1.36, 1.32, 1.44, 1.65, 1.63, 1.51, 1.32,
                               1.34, 1.53, 1.67, 1.63, 1.36, 1.31, 1.38, 1.6, 1.66, 1.51, 1.36, 1.32, 1.45, 1.65, 1.63,
                               1.66, 1.58, 1.42, 1.31, 1.38, 1.61, 1.66, 1.58, 1.35, 1.32, 1.45, 1.66, 1.63, 1.5, 1.32,
                               1.34, 1.62, 1.67, 1.51, 1.32, 1.34, 1.46, 1.67, 1.63, 1.42, 1.31, 1.34, 1.54, 1.68, 1.58,
                               1.35, 1.31, 1.39, 1.62, 1.66, 1.58, 1.34, 1.34, 1.46, 1.67, 1.63, 1.41, 1.31, 1.34, 1.55,
                               1.68, 1.57, 1.34, 1.31, 1.39, 1.63, 1.66, 1.49, 1.34, 1.32, 1.47, 1.67, 1.63, 1.49, 1.31,
                               1.34, 1.56, 1.68, 1.63, 1.4, 1.31, 1.4, 1.63, 1.66, 1.49, 1.31, 1.32, 1.48, 1.67, 1.62,
                               1.48, 1.31, 1.35, 1.56, 1.67, 1.62, 1.4, 1.31, 1.4, 1.64, 1.68, 1.56, 1.33, 1.32, 1.49,
                               1.64, 1.66, 1.47, 1.31, 1.35, 1.57, 1.67, 1.56, 1.39, 1.31]

            self.simulation_thread = threading.Thread(target=self.simulate_data, daemon=True)
            self.plot_timer = QtCore.QTimer()
            self.plot_timer.timeout.connect(self.update_plot)
            self.plot_timer.start(2)

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

    # Funcion con la que empieza el scope, comienza los threads
    def start(self):
        if hasattr(self, 'serial_thread'):  # hasattr verifica si la funcion tiene el atributo serial thread
            self.serial_thread.start()
        else:
            self.simulation_thread.start()
        app.exec_()

    # Funcion de leer data por lista
    def simulate_data(self):
        while True:
            if self.ptr < self.buffer_size:
                value = self.lista_data[self.c]

                self.data[self.ptr] = value
                self.ptr += 1
                self.c += 1

            else:
                self.data[:-1] = self.data[1:]
                self.data[-1] = self.lista_data[self.c]
                self.c += 1

            if self.c >= 1000:
                self.c = 0
            QtCore.QThread.msleep(2)

    # Funcion de leer data por el puerto serial
    def serial_read(self):
        self.ser.reset_input_buffer()
        start_time = time.time()
        start_time_freq = time.time()
        data_fre = 0
        data_count = 0
        while True:
            line = self.ser.readline().decode('utf-8').strip()
            top_indices = np.argsort(self.fft_graph_fft_mag)[-100:][::-1]
            top_frequencies = self.fft_freq[top_indices]
            for freq in top_frequencies:
                fre = int(freq)
                if fre != 0 and fre != 5 and fre != 10 and fre != 15 and fre != 20 and fre != 25:
                    if fre == 12 or fre == 13 or fre == 14 or fre == 11:
                        data_fre += 1

            for value in line.split(','):
                try:
                    value = float(value)
                    if self.ptr < self.buffer_size:
                        self.data[self.ptr] = value
                        self.ptr += 1
                        data_count += 1
                        self.file.write(f"{value}\n")
                        self.file.flush()
                    else:
                        self.data[:-1] = self.data[1:]
                        self.data[-1] = value
                        data_count += 1
                        self.file.write(f"{value}\n")
                        self.file.flush()
                except ValueError:
                    pass

            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                print(f"Tasa de datos: {data_count} por segundo")
                self.Fs = data_count
                data_count = 0
                start_time = time.time()

            elapsed_time_fre = time.time() - start_time_freq
            if elapsed_time_fre >= 1.0:
                print(data_fre)
                data_fre = 0
                start_time_freq = time.time()

    # Funcion para actualizar la grafica, primero se aplican los filtros, se pasa los datos a la grafica
    # Se posiciona el rango x, entre 0 y 1000 o 100 y 1000
    # y si hay suficientes datos se calcula el fft
    def update_plot(self):
        filtered_data = self.apply_filters(
            self.data[:self.ptr] if self.ptr < self.buffer_size else self.data)
        self.graph.setData(filtered_data)
        self.main_plot.setXRange(0, self.buffer_size)

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
        self.fft_graph_fft_mag = 4 / self.fft_sample_size * np.abs(
            np.fft.rfft(y_ham, self.fft_sample_size * self.fft_padding))

        self.fft_graph.setData(self.fft_freq, self.fft_graph_fft_mag)

    def exit(self):
        self.ser.close()
        self.file.close()  # Cerrar el archivo al salir
        sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    puerto = None  # None para viewer, COMx para lectura
    scope = Scope()
    scope.show()
    scope.start()
