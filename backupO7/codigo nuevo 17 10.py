import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QCheckBox, QLabel, QGridLayout
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from scipy.signal import butter, lfilter, iirnotch  # Para aplicar los filtros
import numpy as np
import threading



import time
import os
from datetime import datetime


def create_file(file_name):
    # valores hacia la carpeta datos, si no existe se crea
    directory = os.path.join(os.getcwd(), 'datos')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # fecha y hora actual
    current_time = datetime.now().strftime("%H%M%S_%d%m")

    # ruta completa del archivo
    file_path = os.path.join(directory, f"{current_time}_{file_name}.txt")

    print(f"Creating file: {file_path}")

    # abrir archivo en modo append para agregar datos
    file = open(file_path, 'a')
    return file



class MCC(QMainWindow):
    def __init__(self,file_name):
        super().__init__()
        self.serial_port = None
        self.serial_ports = []
        self.is_connected = False
        self.timer = QTimer(self)

        self.Fs = 675  # setear la frecuencia de sampleo, cuantos datos le llegan por segundo
        self.sample_interval = 1 / self.Fs  # intervalo de sampleo

        self.buffer_size1 = 1000  # tamaño del buffer para datos
        self.data1 = np.zeros(self.buffer_size1)  # Inicializar un array de 0's [0,0,0, . . . ,0,0,0]

        self.buffer_size2 = 1000  # tamaño del buffer para datos
        self.data2 = np.zeros(self.buffer_size1)  # Inicializar un array de 0's [0,0,0, . . . ,0,0,0]

        self.ptr1 = 0  # puntero para el buffer (posicion)
        self.ptr2 = 0  # puntero para el buffer (posicion)

        self.lowpass1 = None
        self.highpass1 =  None
        self.notch1 =  None

        self.lowpass2 =  None
        self.highpass2 =  None
        self.notch2 = None

        self.a_low1 = None
        self.b_low1 = None
        self.a_high1 = None
        self.b_high1 = None
        self.a_notch1 = None
        self.b_notch1 = None
        self.a_low2 = None
        self.b_low2 = None
        self.a_high2 = None
        self.b_high2 = None
        self.a_notch2 = None
        self.b_notch2 = None


        self.fft_sample_size1 = 1000  # tamaño de muestra para fft
        self.fft_padding1 = 5  # padding para calculos (agrega puntos a la señal)
        self.fft_freq1 = np.fft.rfftfreq(self.fft_sample_size1 * self.fft_padding1,
                                        1 / self.Fs)  # Calcular frecuencias del fft
        self.fft_graph_fft_mag1 = np.zeros(int((self.fft_sample_size1 * self.fft_padding1) / 2) + 1)

        self.fft_sample_size2 = 1000  # tamaño de muestra para fft
        self.fft_padding2 = 5  # padding para calculos (agrega puntos a la señal)
        self.fft_freq2 = np.fft.rfftfreq(self.fft_sample_size2 * self.fft_padding2,
                                         1 / self.Fs)  # Calcular frecuencias del fft
        self.fft_graph_fft_mag2 = np.zeros(int((self.fft_sample_size2 * self.fft_padding2) / 2) + 1)



        self.current_time = 0
        self.current_file = None  # Archivo de texto actual
        self.is_recording = False
        self.graphState=False
        self.wait_for_stabilization = False
        self.last_emg_state = 0  # Estado anterior significativo (-1, 0, o 1)
        self.emg_threshold_upper = 1.9  # Umbral para el pulso positivo
        self.emg_threshold_lower = 1.58  # Umbral para el pulso negativo

        self.last_emg_state = 0  # Estado anterior
        self.start_time_0 = 0  # Tiempo en que comienza el estado 0
        self.start_time_1 = 0
        self.min_duration_0 = 3  # Duración mínima en segundos que debe mantenerse en 0
        self.stable_duration_1 = 2  # Duración mínima en 1 (estable)
        self.max_allowed_fluctuation = 1  # Tiempo máximo permitido de fluctuación en segundos
        self.fluctuation_start_time = 0  # Marca cuando comienza una fluctuación
        self.function_one_executed = False
        self.function_two_executed = True
        self.start_time_2 = 0

        self.start_time_minus1 = 0
        self.function_three_executed = False

        self.last_state = 0
        self.start_time = 0
        self.position = 1
        self.change_time = 0  # Almacena el momento de cambio a 1 o -1
        self.state= 0
        self.function = 0
        self.functions = [self.funcion_atras, self.funcion_stop, self.funcion_adelante]

        self.alpha_data = 0

        self.alpha_list=[]
        self.start_alpha_time = time.time()

        self.initUI()

    def funcion_derecha(self):
        # Simula la primera acción
        print("Función derecha")

    def funcion_izquierda(self):
        # Simula la segunda acción
        print("Función izquierda")

    def funcion_stop(self):
        # Simula la tercera acción
        print("Función stop")

    def funcion_adelante(self):
        print("Función adelante")
    def funcion_atras(self):
        print("Función atras")

    def initUI(self):
        self.VerticalLayout = QVBoxLayout(self)

        # Horizontal layout for USB port selector and connect button
        self.HorizontalLayoutUSB = QHBoxLayout(self)
        self.port_selector = QComboBox(self)
        self.refresh_button = QPushButton('Refrescar Puertos', self)
        self.connect_button = QPushButton('Conectar', self)
        self.connect_button.setEnabled(False)  # Disabled until port selected
        self.connect_button.clicked.connect(self.connect_serial)
        self.HorizontalLayoutUSB.addWidget(self.port_selector)
        self.HorizontalLayoutUSB.addWidget(self.refresh_button)
        self.HorizontalLayoutUSB.addWidget(self.connect_button)
        self.VerticalLayout.addLayout(self.HorizontalLayoutUSB)

        self.refresh_button.clicked.connect(self.refresh_ports)

        self.toggle_button = QPushButton("Mostrar dos gráficos", self)
        self.toggle_button.clicked.connect(self.toggle_graphs)
        self.VerticalLayout.addWidget(self.toggle_button)

        # Main layout containing both sections
        self.HorizontalBothvars = QHBoxLayout(self)

        # First layout (Graph1 + FFT1 + Checkboxes)
        self.VerticalBothGraphs1 = QVBoxLayout(self)
        self.HorizontalSignal1 = QHBoxLayout(self)
        self.VerticalGraph1 = QVBoxLayout(self)

        self.signalSelector1 = QComboBox(self)
        self.signalSelector1.addItems(['None', 'ECG', 'EOG', 'EMG', 'EEG'])
        self.signalSelector1.currentIndexChanged.connect(self.update_filters)
        self.VerticalGraph1.addWidget(self.signalSelector1)


        self.case1 = pg.GraphicsLayoutWidget(show=True)
        self.case1.setMinimumWidth(250)
        self.graph1 = self.case1.addPlot()


        self.graph1.setYRange(1.1, 2.5)
        self.graph1.setLabel('left', 'Value', '')
        self.graph1.setLabel('bottom', 'Time', 's')

        self.graph1_curve = self.graph1.plot()  # Línea que se actualizará
        self.VerticalGraph1.addWidget(self.case1)

        self.HorizontalSignal1.addLayout(self.VerticalGraph1)
        self.VerticalBothGraphs1.addLayout(self.HorizontalSignal1)

        self.VerticalFFT1 = QVBoxLayout(self)
        self.checkboxFFT1 = QCheckBox("FFT 1 On", self)
        self.checkboxFFT1.setChecked(False)
        self.checkboxFFT1.toggled.connect(self.toggle_fft1)
        self.VerticalFFT1.addWidget(self.checkboxFFT1)

        self.case2 = pg.GraphicsLayoutWidget(show=True)
        self.case2.setMinimumWidth(250)
        self.graph2 = self.case2.addPlot(title="FFT 1")

        self.graph2.setLabel('left', 'Magnitude', '')
        self.graph2.setLabel('bottom', 'Frequency', 'Hz')
        self.fft_plot1 = self.graph2.plot()

        self.VerticalFFT1.addWidget(self.case2)
        self.VerticalBothGraphs1.addLayout(self.VerticalFFT1)

        self.case1.setVisible(False)  # Initially hidden
        self.case2.setVisible(False)  # Initially hidden
        self.checkboxFFT1.setVisible(False)
        self.signalSelector1.setVisible(False)

        # Second layout (Graph2 + FFT2 + Checkboxes)
        self.VerticalBothGraphs2 = QVBoxLayout(self)
        self.HorizontalSignal2 = QHBoxLayout(self)
        self.VerticalGraph2 = QVBoxLayout(self)

        self.signalSelector2 = QComboBox(self)
        self.signalSelector2.addItems(['None', 'ECG', 'EOG', 'EMG', 'EEG'])
        self.signalSelector2.currentIndexChanged.connect(self.update_filters)
        self.VerticalGraph2.addWidget(self.signalSelector2)

        self.case3 = pg.GraphicsLayoutWidget(show=True)
        self.case3.setMinimumWidth(350)
        self.graph3 = self.case3.addPlot()
        self.graph3.setYRange(1.1, 2.5)
        self.graph3.setLabel('left', 'Value', '')
        self.graph3.setLabel('bottom', 'Time', 's')

        self.graph3_curve = self.graph3.plot()  # Línea que se actualizará

        self.VerticalGraph2.addWidget(self.case3)

        self.HorizontalSignal2.addLayout(self.VerticalGraph2)
        self.VerticalBothGraphs2.addLayout(self.HorizontalSignal2)

        self.VerticalFFT2 = QVBoxLayout(self)
        self.checkboxFFT2 = QCheckBox("FFT 2 On", self)
        self.checkboxFFT2.setChecked(False)
        self.checkboxFFT2.toggled.connect(self.toggle_fft2)
        self.VerticalFFT2.addWidget(self.checkboxFFT2)

        self.case4 = pg.GraphicsLayoutWidget(show=True)
        self.case4.setMinimumWidth(250)
        self.graph4 = self.case4.addPlot(title="FFT 2")

        self.graph2.setLabel('left', 'Magnitude', '')
        self.graph2.setLabel('bottom', 'Frequency', 'Hz')
        self.fft_plot2 = self.graph4.plot()
        self.VerticalFFT2.addWidget(self.case4)

        self.case3.setVisible(False)  # Initially hidden
        self.case4.setVisible(False)  # Initially hidden
        self.checkboxFFT2.setVisible(False)
        self.signalSelector2.setVisible(False)

        self.VerticalBothGraphs2.addLayout(self.VerticalFFT2)
        self.HorizontalBothvars.addLayout(self.VerticalBothGraphs1)
        self.HorizontalBothvars.addLayout(self.VerticalBothGraphs2)
        self.VerticalLayout.addLayout(self.HorizontalBothvars)

        widget = QWidget()
        widget.setLayout(self.VerticalLayout)
        self.setCentralWidget(widget)

        self.setWindowTitle('Simulador Serial')
        self.setGeometry(300, 100, 800, 600)

    def refresh_ports(self):
        self.serial_ports = serial.tools.list_ports.comports()
        self.port_selector.clear()
        for port in self.serial_ports:
            self.port_selector.addItem(port.device)
        self.connect_button.setEnabled(True)

    def connect_serial(self):
        port_name = self.port_selector.currentText()
        if port_name:
            self.serial_port = serial.Serial(port_name, baudrate=115200, timeout=1)
            self.is_connected = True

            # Iniciar el thread de lectura de datos
            self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.serial_thread.start()

            # Timer para actualizar la gráfica
            self.plot_timer = QTimer(self)
            self.plot_timer.timeout.connect(self.update_plot)
            self.plot_timer.start(100)  # Actualizar la gráfica cada 100 ms
            self.toggle_signal1()

    def read_serial_data(self):
        self.serial_port.reset_input_buffer()
        really_start_time = time.time()
        start_time = time.time()
        start_time1 = time.time()

        data_count = 0

        while self.is_connected:
            if self.serial_port.in_waiting:
                try:
                    line = self.serial_port.readline().decode('utf-8').strip()

                except Exception as e:

                    print(f"Error de line: {e}")
                    line="0.00"
                self.current_time = time.time() - really_start_time

                # Detectar si la señal es doble o simple
                if ',' in line:  # Señal doble
                    self.graphState=True

                    try:
                        # Separar los dos valores de la señal doble
                        value1, value2 = map(float, line.split(','))

                        # Almacenar el primer valor en data1
                        if self.is_recording and self.current_file:
                            self.current_file.write(f"{self.current_time:.4f},{value1}\n")
                        if self.ptr1 < self.buffer_size1:
                            self.data1[self.ptr1] = value1
                            self.ptr1 += 1
                        else:
                            self.data1[:-1] = self.data1[1:]  # Desplazar datos
                            self.data1[-1] = value1

                        # Almacenar el segundo valor en data2
                        if self.ptr2 < self.buffer_size2:
                            self.data2[self.ptr2] = value2
                            self.ptr2 += 1
                        else:
                            self.data2[:-1] = self.data2[1:]  # Desplazar datos
                            self.data2[-1] = value2

                        data_count += 1

                    except Exception as e:
                        print(f"Error al leer datos: {e}")

                    # Actualizar tasa de muestreo (Fs) cada 5 segundos
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= 1.0:
                        #print(f"Tasa de datos: {data_count } por segundo")
                        self.Fs = int(data_count)
                        # Actualizar las frecuencias del FFT


                        data_count = 0
                        start_time = time.time()

                    # Actualizar los filtros cada 10 segundos
                    elapsed_time1 = time.time() - start_time1
                    if elapsed_time1 >= 10.0:
                        self.update_filters()
                        start_time1 = time.time()

                else:  # Señal simple
                    self.graphState = False

                    try:
                        value1 = float(line)

                        # Almacenar el valor en data1
                        if self.is_recording and self.current_file:
                            self.current_file.write(f"{self.current_time:.4f},{value1}\n")
                        if self.ptr1 < self.buffer_size1:
                            self.data1[self.ptr1] = value1
                            self.ptr1 += 1
                        else:
                            self.data1[:-1] = self.data1[1:]  # Desplazar datos
                            self.data1[-1] = value1

                        data_count += 1

                    except Exception as e:
                        print(f"Error al leer datos: {e}")

                    # Actualizar tasa de muestreo (Fs) cada 5 segundos
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= 1.0:
                        print(f"Tasa de datos: {data_count } por segundo")
                        self.Fs = int(data_count )
                        # self.fft_freq1 = np.fft.rfftfreq(self.fft_sample_size1 * self.fft_padding1, 1 / self.Fs)
                        # self.fft_freq2 = np.fft.rfftfreq(self.fft_sample_size2 * self.fft_padding2, 1 / self.Fs)
                        self.update_filters()
                        data_count = 0
                        start_time = time.time()

                    # Actualizar los filtros cada 10 segundos
                    elapsed_time1 = time.time() - start_time1
                    if elapsed_time1 >= 10.0:
                        self.update_filters()
                        start_time1 = time.time()

    # Funciones para limpiar y alternar gráficos
    def toggle_graphs(self):
        pass

    def toggle_signal1(self):
        self.case1.setVisible(True)
        self.case2.setVisible(True)
        self.checkboxFFT1.setVisible(True)
        self.signalSelector1.setVisible(True)

    def toggle_signal2(self, state):
        self.case3.setVisible(state)
        self.case4.setVisible(state)
        self.checkboxFFT2.setVisible(state)
        self.signalSelector2.setVisible(state)





    def update_plot(self):
        if self.graphState:
            #self.Fs = 550
            self.toggle_signal2(True)
            time_values = np.linspace(0 + self.current_time, (self.ptr1 / self.Fs) + self.current_time, self.ptr1)
            if self.signalSelector1.currentText() == 'None':
                data1 = self.data1[:self.ptr1] if self.ptr1 < self.buffer_size1 else self.data1
            else:
                data1 = self.apply_filter((self.data1[:self.ptr1] if self.ptr1 < self.buffer_size1 else self.data1), 1)
            self.graph1_curve.clear()
            self.graph1_curve.setData(time_values,data1)
            if len(time_values) > 0:
                self.graph1.setXRange(time_values[0], time_values[-1])

            if self.ptr1 >= self.fft_sample_size1 and self.checkboxFFT1.isChecked():
                self.calc_fft(data1[-self.fft_sample_size1:], 1)


            time_values2 = np.linspace(0 + self.current_time, (self.ptr2 / self.Fs) + self.current_time, self.ptr2)
            if self.signalSelector2.currentText() == 'None':
                data2 = self.data2[:self.ptr2] if self.ptr2 < self.buffer_size2 else self.data2
            else:
                data2 = self.apply_filter((self.data2[:self.ptr2] if self.ptr2 < self.buffer_size2 else self.data2), 2)

            if self.signalSelector1.currentText() == "EOG":
                self.eog(data1)
            if self.signalSelector2.currentText()=="EMG":
                self.emg(data2,1.6,1.4)

            self.graph3_curve.clear()
            self.graph3_curve.setData(time_values2,data2)
            if len(time_values2) > 0:
                self.graph3.setXRange(time_values2[0], time_values2[-1])

            if self.ptr2 >= self.fft_sample_size2 and self.checkboxFFT2.isChecked():
                self.calc_fft(data2[-self.fft_sample_size2:], 2)


        else:
            self.Fs = 675
            self.toggle_signal2(False)
            if self.signalSelector1.currentText()=='None':
                data = self.data1[:self.ptr1] if self.ptr1 < self.buffer_size1 else self.data1
            else:
                data = self.apply_filter((self.data1[:self.ptr1] if self.ptr1 < self.buffer_size1 else self.data1), 1)

            if self.signalSelector1.currentText() == "EOG":
                self.eog(data)
            if self.signalSelector1.currentText() == "EMG":
                self.emg(data,1.45,1.75)
            if self.signalSelector1.currentText() == "EEG":
                elapsed_time = time.time() - self.start_alpha_time
                if elapsed_time >= 1.0:
                    print(f"alpha data {self.current_time - 1}-{self.current_time} : {self.alpha_data} por segundo")

                    self.alpha_list.append(self.alpha_data)
                    mean_values_last_20 = [np.mean(self.alpha_list[max(0, i - 19):i + 1]) for i in range(len(self.alpha_list))]

                    percentage_mapped_mean_values = [
                        ((value - min(mean_values_last_20[max(0, i - 19):i + 1])) /
                         (max(mean_values_last_20[max(0, i - 19):i + 1]) - min(
                             mean_values_last_20[max(0, i - 19):i + 1])) * 100)
                        if max(mean_values_last_20[max(0, i - 19):i + 1]) != min(
                            mean_values_last_20[max(0, i - 19):i + 1]) else 0
                        for i, value in enumerate(mean_values_last_20)
                    ]

                    print(mean_values_last_20[-1])

                    print(percentage_mapped_mean_values[-1])

                    # Reiniciar `alpha_data` y el tiempo de inicio
                    self.alpha_data = 0
                    self.start_alpha_time = time.time()



            time_values = np.linspace(0 + self.current_time, (self.ptr1 / self.Fs) + self.current_time, self.ptr1)
            self.graph1_curve.clear()
            self.graph1_curve.setData(time_values,data)
            if len(time_values) > 0:
                self.graph1.setXRange(time_values[0], time_values[-1])
            if self.ptr1 >= self.fft_sample_size1 and self.checkboxFFT1.isChecked():
                self.calc_fft(data[-self.fft_sample_size1:], 1)

    def eog(self,data1):
        eog = data1[-1]
        time_in_zero = self.current_time - self.start_time if self.last_state == 0 else 0
        # Determinar el estado actual
        if eog < 1.45:
            current_state = -1
        elif 1.45 <= eog <= 1.8:
            current_state = 0
        else:
            current_state = 1


        # Control de cambio de estado
        if self.last_state == 0 and current_state != 0:
            if time_in_zero >= 1.5:
                self.change_time = self.current_time
                self.last_state = current_state
                # Actualiza posición según la dirección (1 o -1)
                self.update_position(current_state)
                print(f"Posición actual en la lista de funciones: {self.position}")

        elif self.last_state != 0:
            if current_state == 0 and (self.current_time - self.change_time) <= 1:
                self.start_time = self.current_time  # Resetear tiempo en 0
                self.last_state = current_state
                print(current_state)

    def update_position(self, direction):
        """Controla la posición y ejecuta la función correspondiente."""
        if direction == 1 and self.position < len(self.functions) - 1:
            # Sube una posición y ejecuta función
            self.position += 1
            self.functions[self.position]()
        elif direction == -1 and self.position > 0:
            # Baja una posición y ejecuta función
            self.position -= 1
            self.functions[self.position]()
    def emg(self,data2,max,min):
        emg = np.mean(data2)
        if min < emg < max:
            if self.last_emg_state != 0:
                # Cambia a estado 0 y comienza/reinicia el contador
                self.start_time_0 = self.current_time
                self.last_emg_state = 0
                self.fluctuation_start_time = 0  # Reinicia la fluctuación permitida
                self.graph3.setTitle("0")
            elif self.current_time - self.start_time_0 >= self.min_duration_0:
                # Si permanece en 0 por más de 3 segundos, imprime un mensaje
                self.graph3.setTitle("0 estado")
                #print("estado 0")
        elif emg >= max:

            if self.last_emg_state == 0 and self.current_time - self.start_time_0 >= self.min_duration_0:

                if self.fluctuation_start_time == 0:

                    self.fluctuation_start_time = self.current_time
                elif self.current_time - self.fluctuation_start_time < self.max_allowed_fluctuation:

                    self.start_time_1 = self.current_time
                    self.last_emg_state = 1
                    self.graph3.setTitle("1")

            # Si el estado es 1 y se mantiene estable por más de 2 segundos
            if self.last_emg_state == 1 and self.start_time_1:
                if self.current_time - self.start_time_1 >= self.stable_duration_1 and not self.function_one_executed:
                    self.funcion_derecha()  # Ejecuta funcion_uno una vez
                    self.function_one_executed = True
                    self.start_time_2 = self.current_time
                    self.function_two_executed = False
            # Ejecuta funcion_dos después de 2 segundos de funcion_uno
        elif emg <= min:
            if self.last_emg_state == 0 and self.current_time - self.start_time_0 >= self.min_duration_0:
                if self.fluctuation_start_time == 0:
                    self.fluctuation_start_time = self.current_time
                elif self.current_time - self.fluctuation_start_time < self.max_allowed_fluctuation:
                    # Cambia a estado -1 y registra el tiempo
                    self.start_time_minus1 = self.current_time
                    self.last_emg_state = -1
                    self.graph3.setTitle("-1")

            # Si el estado es -1 y se mantiene estable por más de 2 segundos
            if self.last_emg_state == -1 and self.start_time_minus1:
                if self.current_time - self.start_time_minus1 >= self.stable_duration_1 and not self.function_three_executed:
                    self.funcion_izquierda()  # Ejecuta funcion_tres una vez
                    self.function_three_executed = True
                    self.start_time_2 = self.current_time
                    self.function_two_executed = False

        if (
                self.function_one_executed or self.function_three_executed) and self.current_time - self.start_time_2 >= 2 and not self.function_two_executed:
            self.funcion_stop()
            self.function_two_executed = True
            self.function_one_executed = False
            self.function_three_executed = False
            # Vuelve a estado 0
            self.last_emg_state = 0
            self.start_time_2 = self.current_time
            self.fluctuation_start_time = 0

    def detect_alpha_peak(self,fft_values, freq_range, alpha_range=(8, 12)):
        # Extraer las frecuencias y potencias dentro del rango alfa
        alpha_indices = np.where((freq_range >= alpha_range[0]) & (freq_range <= alpha_range[1]))
        alpha_power = np.mean(fft_values[alpha_indices])

        # Comparar con las potencias fuera de la banda alfa
        non_alpha_power = np.mean(fft_values[np.setdiff1d(range(len(freq_range)), alpha_indices)])


        threshold = 15 * non_alpha_power
        #print(threshold)

        if alpha_power > threshold:
            return True, alpha_power
        else:
            return False, alpha_power

    def calc_fft(self, data,num):
        if num==1:
            data = data - np.mean(data)  # Eliminar componente dc

            # Moudela la señal con una ventana de hamming, para suavizala y evitar "leakage"
            ham = np.hamming(self.fft_sample_size1)
            y_ham = data * ham
            self.fft_graph_fft_mag1 = 4 / self.fft_sample_size1 * np.abs(
                np.fft.rfft(y_ham, self.fft_sample_size1 * self.fft_padding1))

            self.fft_plot1.setData(self.fft_freq1, self.fft_graph_fft_mag1)

            if self.signalSelector1.currentText() == "EEG":
                peak_detected, alpha_power = self.detect_alpha_peak(self.fft_graph_fft_mag1, self.fft_freq1)
                if peak_detected:
                    # print(f"Alfa detectada: Potencia = {alpha_power:.4f}, {self.current_time}")
                    self.alpha_data += 1


        elif num==2:
            data = data - np.mean(data)  # Eliminar componente dc

            # Moudela la señal con una ventana de hamming, para suavizala y evitar "leakage"
            ham = np.hamming(self.fft_sample_size2)
            y_ham = data * ham
            self.fft_graph_fft_mag2 = 4 / self.fft_sample_size2 * np.abs(
                np.fft.rfft(y_ham, self.fft_sample_size2 * self.fft_padding2))

            self.fft_plot2.setData(self.fft_freq2, self.fft_graph_fft_mag2)


    def toggle_fft1(self, state):

        self.graph2.setVisible(state)
        self.resize(self.size().width() + 1, self.size().height() + 1)  # Forzar un pequeño cambio de tamaño
        self.resize(self.size().width() - 1, self.size().height() - 1)
        if not state:
            self.fft_plot1.clear()  # Limpiar la gráfica cuando se desactiva

    def toggle_fft2(self, state):
        self.graph4.setVisible(state)
        self.resize(self.size().width() + 1, self.size().height() + 1)  # Forzar un pequeño cambio de tamaño
        self.resize(self.size().width() - 1, self.size().height() - 1)
        if not state:
            self.fft_plot2.clear()  # Limpiar la gráfica cuando se desactiva

    def update_filters(self):
        signal_type1 = self.signalSelector1.currentText()
        signal_type2= self.signalSelector2.currentText()

        if signal_type1 in ['ECG', 'EEG']:
            if not self.is_recording or (self.current_file and self.current_file_name != signal_type1):
                if self.current_file:  # Cerrar archivo anterior si existe
                    self.current_file.close()
                self.current_file_name = signal_type1
                self.current_file = create_file(signal_type1)  # Crear nuevo archivo
                self.is_recording = True
                print(f"Iniciando grabación en archivo: {self.current_file_name}")
        elif signal_type1 in ['EMG','EOG','None']:
            if self.is_recording:
                if self.current_file:
                    self.current_file.close()
                self.is_recording = False
                print("Grabación detenida.")


        if signal_type1 == 'ECG' or signal_type1 == 'EEG':
            self.checkboxFFT1.setChecked(True)  # Activar checkbox automáticamente
        if signal_type2 == 'ECG' or signal_type2 == 'EEG':
            self.checkboxFFT2.setChecked(True)  # Activar checkbox automáticamente
        if signal_type1 == 'ECG':
            self.lowpass1 = 50
            self.highpass1 = 0.00001
            self.notch1 = 50
        elif signal_type1 == 'EOG':
            self.lowpass1 = 40
            self.highpass1 = 0.00001
            self.notch1 = 50
        elif signal_type1 == 'EMG':
            self.lowpass1 = 100
            self.highpass1 = 0.00001
            self.notch1 = 50
        elif signal_type1 == 'EEG':
            self.lowpass1 = 30
            self.highpass1 = 5
            self.notch1 = 50
        else:  # Ninguna señal seleccionada
            self.lowpass1 = 0.00001
            self.highpass1 = 0.00001
            self.notch1 = 0.00001

        if signal_type2 == 'ECG':
            self.lowpass2 = 100
            self.highpass2 = 0.00001
            self.notch2 = 50
        elif signal_type2 == 'EOG':
            self.lowpass2 = 40
            self.highpass2 = 0.00001
            self.notch2 = 50
        elif signal_type2 == 'EMG':
            self.lowpass2 = 100
            self.highpass2 = 0.00001
            self.notch2 = 50
        elif signal_type2 == 'EEG':
            self.lowpass2 = 30
            self.highpass2 = 5
            self.notch2 = 50
        else:  # Ninguna señal seleccionada
            self.lowpass2 = 0.00001
            self.highpass2 = 0.00001
            self.notch2 = 0.00001

        #print(f"Filtros actualizados - Lowpass: {self.lowpass1}Hz, Highpass: {self.highpass1}Hz, Notch: {self.notch1}Hz")
        # frecuencia de corte debe estar entre 0 y la mitad de la frecuencia de sampleo
        # Filtro butterworth
        # orden del filtro, frecuencia de corte normalizada y el tipo
        # La Q del filtro notch es el factor de calidad, un valor mas alto significa un rechazo mas estrecho
        if 0 < self.lowpass1 < 0.5 * self.Fs and 0 < self.highpass1 < 0.5 * self.Fs:
            self.b_low1, self.a_low1 = butter(5, self.lowpass1 / (0.5 * self.Fs), btype='low')
            self.b_high1, self.a_high1 = butter(5, self.highpass1 / (0.5 * self.Fs), btype='high')
            self.b_notch1, self.a_notch1 = iirnotch(self.notch1 / (0.5 * self.Fs), 1)
        if 0 < self.lowpass2 < 0.5 * self.Fs and 0 < self.highpass2 < 0.5 * self.Fs:
            self.b_low2, self.a_low2 = butter(5, self.lowpass2 / (0.5 * self.Fs), btype='low')
            self.b_high2, self.a_high2 = butter(5,self.highpass2 / (0.5 * self.Fs), btype='high')
            self.b_notch2, self.a_notch2 = iirnotch(self.notch2 / (0.5 * self.Fs), 1)

    # Filtros para señales
    def apply_filter(self, data, num):
        filtered_data = data
        if num==1:
            filtered_data = lfilter(self.b_high1, self.a_high1, filtered_data)
            filtered_data = lfilter(self.b_low1, self.a_low1, filtered_data)
            filtered_data = lfilter(self.b_notch1, self.a_notch1, filtered_data)

            return filtered_data
        elif num==2:
            filtered_data = lfilter(self.b_high2, self.a_high2, filtered_data)
            filtered_data = lfilter(self.b_low2, self.a_low2, filtered_data)
            filtered_data = lfilter(self.b_notch2, self.a_notch2, filtered_data)
            return filtered_data

    def exit(self):
        self.ser.close()
        self.current_file.close()
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MCC("asd")
    window.show()
    sys.exit(app.exec_())
